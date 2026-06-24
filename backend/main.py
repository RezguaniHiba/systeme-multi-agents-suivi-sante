# lance le dispatcher principal du backend
from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
import os
import httpx
import uvicorn
import asyncio
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse


PORT_USER = 8001
PORT_IOT  = 8002


_proc_user: subprocess.Popen | None = None
_proc_iot:  subprocess.Popen | None = None


def _start_subprocess(script: str, port: int, dev: bool) -> subprocess.Popen:
    cmd = [sys.executable, script, "--port", str(port)]
    if dev:
        cmd.append("--dev")


    proc = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(os.path.abspath(__file__)),

    )
    return proc


def _wait_for_server(url: str, timeout: float = 30.0, label: str = "") -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=2.0)
            if r.status_code == 200:
                print(f"  ✅ {label} prêt ({url})")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print(f"  ❌ {label} n'a pas démarré dans {timeout}s")
    return False


def start_sub_servers(dev: bool = False):
    global _proc_user, _proc_iot

    print("\nLancement des sous-serveurs...")
    _proc_user = _start_subprocess("server_user.py", PORT_USER, dev)
    _proc_iot  = _start_subprocess("server_iot.py",  PORT_IOT,  dev)


    _wait_for_server(f"http://127.0.0.1:{PORT_USER}/health", label="Serveur Cas 1 (user) ")
    _wait_for_server(f"http://127.0.0.1:{PORT_IOT}/health",  label="Serveur Cas 2 (IoT)  ")


def stop_sub_servers():
    for proc, label in [(_proc_user, "Cas 1"), (_proc_iot, "Cas 2")]:
        if proc and proc.poll() is None:
            print(f" Arrêt {label} (pid={proc.pid})...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


app = FastAPI(
    title="Système Multi-Agents Santé — Dispatcher",
    description=(
        "Point d'entrée unique du système multi-agents de suivi de santé.\n\n"
        "Ce dispatcher relaie chaque requête vers le serveur spécialisé approprié :\n\n"
        "| Route | Serveur cible | Description |\n"
        "|---|---|---|\n"
        "| `POST /ask` | port 8001 | Cas 1 — question médicale utilisateur |\n"
        "| `POST /iot/data` | port 8002 | Cas 2 — données SmartWatch IoT |\n"
        "| `GET /iot/latest/{patient_id}` | port 8002 | Dernière mesure IoT |\n"
        "| `GET /iot/history/{patient_id}` | port 8002 | Historique IoT |\n\n"
        "Les deux pipelines CrewAI tournent dans des **processus Python séparés** "
        "(ports 8001 et 8002), garantissant une isolation absolue de la mémoire.\n\n"
        "> **Tip :** Vous pouvez aussi appeler les serveurs directement sur leurs ports "
        "respectifs pour le debug."
    ),
    version="3.1.0",
)


from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_http_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def startup():
    global _http_client
    _http_client = httpx.AsyncClient(timeout=600.0)


@app.on_event("shutdown")
async def shutdown():
    if _http_client:
        await _http_client.aclose()
    stop_sub_servers()


async def _proxy(request: Request, target_url: str) -> Response:
    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    try:
        resp = await _http_client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "application/json"),
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Sous-serveur inaccessible : {target_url}. Vérifiez qu'il est démarré."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout — le pipeline LLM prend trop de temps. Réessayez."
        )


@app.get("/", tags=["Info"])
async def root():
    return {
        "service":       "Système Multi-Agents Santé",
        "version":       "3.1.0",
        "architecture":  "2 processus Python isolés (subprocess)",
        "dispatcher":    "port 8000",
        "servers": {
            "cas_1_user": f"http://localhost:{PORT_USER}  (server_user.py)",
            "cas_2_iot":  f"http://localhost:{PORT_IOT}   (server_iot.py)",
        },
        "routes": {
            "POST /ask":                 f"→ proxy → port {PORT_USER}",
            "POST /iot/data":            f"→ proxy → port {PORT_IOT}",
            "GET /iot/latest/{{id}}":    f"→ proxy → port {PORT_IOT}",
            "GET /iot/history/{{id}}":   f"→ proxy → port {PORT_IOT}",
            "GET  /health":              "état des deux sous-serveurs",
        },
    }


@app.get("/health", tags=["Info"])
async def health():
    results = {}
    for label, port in [("user_server", PORT_USER), ("iot_server", PORT_IOT)]:
        try:
            r = await _http_client.get(f"http://127.0.0.1:{port}/health", timeout=3.0)
            results[label] = r.json() if r.status_code == 200 else {"status": "error", "code": r.status_code}
        except Exception as e:
            results[label] = {"status": "unreachable", "error": str(e)}

    all_ok = all(v.get("status") == "ok" for v in results.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"dispatcher": "ok", "sub_servers": results},
    )


@app.post("/auth/register", tags=["Authentification"])
async def auth_register(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/auth/register")


@app.post("/auth/login", tags=["Authentification"])
async def auth_login(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/auth/login")


@app.post("/auth/forgot-password", tags=["Authentification"])
async def auth_forgot_password(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/auth/forgot-password")


@app.post("/auth/reset-password", tags=["Authentification"])
async def auth_reset_password(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/auth/reset-password")


@app.get("/auth/smtp-status", tags=["Authentification"])
async def auth_smtp_status(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/auth/smtp-status")


@app.post("/auth/test-email", tags=["Authentification"])
async def auth_test_email(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/auth/test-email")


@app.get("/auth/me/{user_id}", tags=["Authentification"])
async def auth_me(user_id: str, request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/auth/me/{user_id}")


@app.post("/ask", tags=["Cas 1 — Utilisateur"])
async def ask_question(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/ask")


@app.get("/conversations", tags=["Historique conversations"])
async def list_conversations(request: Request):
    query = request.url.query
    suffix = f"?{query}" if query else ""
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/conversations{suffix}")


@app.get("/conversations/{conversation_id}/messages", tags=["Historique conversations"])
async def get_conversation_messages(conversation_id: str, request: Request):
    query = request.url.query
    suffix = f"?{query}" if query else ""
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/conversations/{conversation_id}/messages{suffix}")


@app.patch("/conversations/{conversation_id}", tags=["Historique conversations"])
async def rename_conversation_route(conversation_id: str, request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/conversations/{conversation_id}")


@app.delete("/conversations/{conversation_id}", tags=["Historique conversations"])
async def delete_conversation_route(conversation_id: str, request: Request):
    query = request.url.query
    suffix = f"?{query}" if query else ""
    return await _proxy(request, f"http://127.0.0.1:{PORT_USER}/conversations/{conversation_id}{suffix}")


@app.post("/iot/data", tags=["Cas 2 — SmartWatch IoT"])
async def receive_iot_data(request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_IOT}/iot/data")


@app.get("/iot/latest/{patient_id}", tags=["Cas 2 — SmartWatch IoT"])
async def get_latest_iot(patient_id: str, request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_IOT}/iot/latest/{patient_id}")


@app.get("/iot/history/{patient_id}", tags=["Cas 2 — SmartWatch IoT"])
async def get_history_iot(patient_id: str, request: Request):
    return await _proxy(request, f"http://127.0.0.1:{PORT_IOT}/iot/history/{patient_id}")


def main():
    parser = argparse.ArgumentParser(description="Système Multi-Agents Santé")
    parser.add_argument("--dev",        action="store_true",
                        help="Active le reload automatique sur les sous-serveurs (développement)")
    parser.add_argument("--host",       default="0.0.0.0")
    parser.add_argument("--port",       type=int, default=8000)
    parser.add_argument("--user-port",  type=int, default=8001,
                        help="Port du serveur Cas 1 (défaut: 8001)")
    parser.add_argument("--iot-port",   type=int, default=8002,
                        help="Port du serveur Cas 2 (défaut: 8002)")
    args = parser.parse_args()


    global PORT_USER, PORT_IOT
    PORT_USER = args.user_port
    PORT_IOT  = args.iot_port


    print("\nSystème Multi-Agents Santé — démarrage")
    print("=" * 60)
    print(f"  Dispatcher  : http://localhost:{args.port}")
    print(f"  Docs        : http://localhost:{args.port}/docs")
    print(f"  Cas 1 (user): http://localhost:{PORT_USER}  [processus isolé]")
    print(f"  Cas 2 (IoT) : http://localhost:{PORT_IOT}  [processus isolé]")
    print(f"  Isolation   : subprocess par pipeline (fix Windows spawn)")
    if args.dev:
        print("  🔧  Mode        : DÉVELOPPEMENT (reload activé)")
    else:
        print("  🚀  Mode        : PRODUCTION")
    print("=" * 60)


    start_sub_servers(dev=args.dev)


    def handle_signal(signum, frame):
        print("\n\nSignal reçu — arrêt du système...")
        stop_sub_servers()
        sys.exit(0)

    signal.signal(signal.SIGINT,  handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


    print(f"\nDispatcher démarré sur http://localhost:{args.port}")
    print("    Appuyez sur Ctrl+C pour arrêter tous les serveurs.\n")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=False,
        workers=1,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
