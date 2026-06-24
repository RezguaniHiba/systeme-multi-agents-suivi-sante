# expose les routes principales de l'assistant
import asyncio
from concurrent.futures import ProcessPoolExecutor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


_user_pool = ProcessPoolExecutor(max_workers=1)
_iot_pool  = ProcessPoolExecutor(max_workers=1)


def _run_health_crew_worker(question: str) -> str:
    from crew import run_health_crew
    return run_health_crew(question)


def _run_iot_pipeline_worker(data: dict, patient_id: str) -> dict:
    from iot_pipeline import run_iot_pipeline
    return run_iot_pipeline(data, patient_id=patient_id)


app = FastAPI(
    title="Système Multi-Agents Santé",
    description=(
        "API unifiée pour le système multi-agents de suivi de santé.\n\n"
        "- **POST /ask** : Cas 1 — réponse à une question médicale utilisateur\n"
        "- **POST /iot/data** : Cas 2 — analyse de données SmartWatch IoT\n\n"
        "Les deux cas peuvent s'exécuter **en parallèle** sans interférence "
        "(processus isolés)."
    ),
    version="2.0.0",
)


class UserQuestion(BaseModel):
    question: str = Field(..., example="J'ai des maux de tête fréquents, que faire ?")
    user_id: Optional[str] = Field(default="user_001", example="user_001")


class SmartWatchData(BaseModel):
    patient_id:          Optional[str]   = Field(default="patient_001")
    timestamp:           Optional[str]   = Field(default=None)
    heart_rate:          Optional[float] = Field(default=None, description="bpm")
    spo2:                Optional[float] = Field(default=None, description="%")
    blood_pressure_sys:  Optional[float] = Field(default=None, description="mmHg")
    blood_pressure_dia:  Optional[float] = Field(default=None, description="mmHg")
    temperature:         Optional[float] = Field(default=None, description="°C")


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Système Multi-Agents Santé",
        "version": "2.0.0",
        "isolation": "subprocess par pipeline (Cas 1 et Cas 2 parallèles)",
        "routes": {
            "POST /ask":      "Cas 1 — question médicale utilisateur",
            "POST /iot/data": "Cas 2 — données SmartWatch IoT",
        }
    }


@app.post("/ask", tags=["Cas 1 — Utilisateur"])
async def ask_question(body: UserQuestion):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(
            _user_pool,
            _run_health_crew_worker,
            body.question,
        )
        return {
            "case":     1,
            "user_id":  body.user_id,
            "question": body.question,
            "response": response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur pipeline Cas 1 : {str(e)}")


@app.post("/iot/data", tags=["Cas 2 — SmartWatch IoT"])
async def receive_iot_data(body: SmartWatchData):
    data = body.model_dump(exclude_none=False)
    if not data.get("timestamp"):
        data["timestamp"] = datetime.utcnow().isoformat()

    patient_id = data.pop("patient_id", "patient_001")

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _iot_pool,
            _run_iot_pipeline_worker,
            data,
            patient_id,
        )
        return {
            "case":          2,
            "patient_id":    patient_id,
            "received_at":   data.get("timestamp"),
            "history_count": result.get("history_count", 0),
            "status":        result["status"],
            "anomalies":     result.get("anomalies", []),
            "alert":         result.get("alert"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur pipeline Cas 2 : {str(e)}")


@app.on_event("shutdown")
def shutdown_pools():
    _user_pool.shutdown(wait=False)
    _iot_pool.shutdown(wait=False)
