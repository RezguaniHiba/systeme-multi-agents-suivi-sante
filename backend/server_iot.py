# gère les routes liées aux données iot
import argparse
import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


app = FastAPI(
    title="Multi-Agents Santé — Cas 2 (SmartWatch IoT)",
    description=(
        "Serveur dédié à la surveillance IoT SmartWatch.\n\n"
        "- **POST /iot/data** : données capteurs (FC, SpO2, PA, Température)\n\n"
        "Sauvegarde **immédiate** en SQLite + pipeline CrewAI en **thread background**.\n\n"
        "Ce serveur tourne dans un processus Python **isolé** du pipeline utilisateur (port 8001)."
    ),
    version="1.1.0",
)


class SmartWatchData(BaseModel):
    patient_id:          Optional[str]   = Field(default="patient_001")
    timestamp:           Optional[str]   = Field(default=None)
    heart_rate:          Optional[float] = Field(default=None, description="bpm")
    spo2:                Optional[float] = Field(default=None, description="%")
    blood_pressure_sys:  Optional[float] = Field(default=None, description="mmHg")
    blood_pressure_dia:  Optional[float] = Field(default=None, description="mmHg")
    temperature:         Optional[float] = Field(default=None, description="°C")


def _run_pipeline_background(data: dict, patient_id: str, record_id: int) -> None:
    try:
        from iot_pipeline import run_iot_pipeline
        print(f"[IoT background] Démarrage pipeline pour record_id={record_id}")

        result = run_iot_pipeline(data, patient_id=patient_id)

        print(f"[IoT background] Pipeline terminé. Result: {result}")
        print(f"[IoT background] status={result.get('status')}, alert={'oui' if result.get('alert') else 'non'}")


        from iot_db import update_record_result
        update_record_result(
            record_id=record_id,
            status=result.get("status", "unknown"),
            anomalies=result.get("anomalies", []),
            alert=result.get("alert"),
        )
        print(f"[IoT background] update_record_result terminé pour record_id={record_id}")

    except Exception as exc:
        import traceback
        print(f"[IoT background pipeline] Erreur (record_id={record_id}) : {exc}")
        traceback.print_exc()


        try:
            from iot_db import update_record_result
            update_record_result(
                record_id=record_id,
                status="error",
                anomalies=[],
                alert=f"Erreur pipeline : {str(exc)}",
            )
        except Exception:
            pass


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Cas 2 — SmartWatch IoT",
        "port": 8002,
        "routes": {"POST /iot/data": "données capteurs SmartWatch"},
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "iot"}


@app.post("/iot/data", tags=["Cas 2 — SmartWatch IoT"])
def receive_iot_data(body: SmartWatchData):
    data = body.model_dump(exclude_none=False)


    if not data.get("timestamp"):
        data["timestamp"] = datetime.now(timezone.utc).isoformat()

    patient_id = data.pop("patient_id", "patient_001")


    from iot_db import save_measurement, get_history

    record_id = save_measurement(data, patient_id=patient_id)
    history_count = len(get_history(patient_id=patient_id, days=15))


    thread = threading.Thread(
        target=_run_pipeline_background,
        args=(data.copy(), patient_id, record_id),
        daemon=True,
        name=f"iot-pipeline-{record_id}",
    )
    thread.start()


    return {
        "case":          2,
        "patient_id":    patient_id,
        "received_at":   data.get("timestamp"),
        "history_count": history_count,
        "record_id":     record_id,
        "status":        "pending",
        "anomalies":     [],
        "alert":         None,
        "message":       "Données enregistrées. Analyse CrewAI en cours…",
    }

@app.get("/iot/latest/{patient_id}", tags=["Cas 2 — SmartWatch IoT"])
def get_latest_iot_data(patient_id: str = "patient_001"):
    from iot_db import get_connection
    import json

    conn = get_connection()


    row = conn.execute("""
        SELECT id, patient_id, timestamp, heart_rate, spo2,
               blood_pressure_sys, blood_pressure_dia, temperature,
               status, anomalies_json, alert
        FROM iot_measurements
        WHERE patient_id = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
    """, (patient_id,)).fetchone()

    conn.close()

    if not row:
        return {"patient_id": patient_id, "data": None}

    latest = dict(row)
    raw = latest.pop("anomalies_json", None)
    latest["anomalies"] = json.loads(raw) if raw else []

    return {
        "patient_id": patient_id,
        "received_at": latest.get("timestamp"),
        "status":      latest.get("status", "pending"),
        "anomalies":   latest.get("anomalies", []),
        "alert":       latest.get("alert"),
        "vitals": {
            "heart_rate":         latest.get("heart_rate"),
            "spo2":               latest.get("spo2"),
            "blood_pressure_sys": latest.get("blood_pressure_sys"),
            "blood_pressure_dia": latest.get("blood_pressure_dia"),
            "temperature":        latest.get("temperature"),
        },
    }

@app.get("/iot/history/{patient_id}", tags=["Cas 2 — SmartWatch IoT"])
def get_iot_history(patient_id: str = "patient_001", days: int = 1):
    from iot_db import get_history
    rows = get_history(patient_id=patient_id, days=days)
    return {
        "patient_id": patient_id,
        "count": len(rows),
        "measurements": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serveur Cas 2 — SmartWatch IoT")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--dev",  action="store_true", help="Mode reload (développement)")
    args = parser.parse_args()

    print(f"\n⌚  Serveur Cas 2 (SmartWatch IoT) — port {args.port}")
    print("=" * 50)
    uvicorn.run(
        "server_iot:app",
        host=args.host,
        port=args.port,
        reload=args.dev,
        workers=1,
    )
