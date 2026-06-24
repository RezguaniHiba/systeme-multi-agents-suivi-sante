# gère le stockage local des données
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = os.getenv("IOT_DB_PATH", "iot_health.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS iot_measurements (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id          TEXT    NOT NULL DEFAULT 'patient_001',
            timestamp           TEXT    NOT NULL,
            heart_rate          REAL,
            spo2                REAL,
            blood_pressure_sys  REAL,
            blood_pressure_dia  REAL,
            temperature         REAL,
            raw_json            TEXT,
            status              TEXT    DEFAULT 'pending',
            anomalies_json      TEXT,
            alert               TEXT
        )
    """)

    for col, definition in [
        ("status",         "TEXT DEFAULT 'pending'"),
        ("anomalies_json", "TEXT"),
        ("alert",          "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE iot_measurements ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def save_measurement(data: dict, patient_id: str = "patient_001") -> int:
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO iot_measurements
            (patient_id, timestamp, heart_rate, spo2,
             blood_pressure_sys, blood_pressure_dia, temperature, raw_json,
             status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        patient_id,
        data.get("timestamp", datetime.utcnow().isoformat()),
        data.get("heart_rate"),
        data.get("spo2"),
        data.get("blood_pressure_sys"),
        data.get("blood_pressure_dia"),
        data.get("temperature"),
        json.dumps(data),
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def update_record_result(
    record_id: int,
    status: str,
    anomalies: list,
    alert: str | None,
) -> None:
    conn = get_connection()
    conn.execute("""
        UPDATE iot_measurements
        SET status         = ?,
            anomalies_json = ?,
            alert          = ?
        WHERE id = ?
    """, (
        status,
        json.dumps(anomalies),
        alert,
        record_id,
    ))
    conn.commit()
    conn.close()


def get_history(patient_id: str = "patient_001", days: int = 15) -> list[dict]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM iot_measurements
        WHERE patient_id = ? AND timestamp >= ?
        ORDER BY timestamp ASC
    """, (patient_id, since)).fetchall()
    conn.close()
    result = []
    for r in rows:
        row = dict(r)

        raw = row.pop("anomalies_json", None)
        row["anomalies"] = json.loads(raw) if raw else []
        result.append(row)
    return result


def get_history_summary(patient_id: str = "patient_001", days: int = 15) -> dict:
    history = get_history(patient_id=patient_id, days=days)

    if not history:
        return {
            "count": 0,
            "summary": "Aucun historique disponible pour ce patient.",
            "latest": None,
            "stats": {}
        }


    hr_values = [h["heart_rate"] for h in history if h.get("heart_rate") is not None]
    spo2_values = [h["spo2"] for h in history if h.get("spo2") is not None]
    sys_values = [h["blood_pressure_sys"] for h in history if h.get("blood_pressure_sys") is not None]
    dia_values = [h["blood_pressure_dia"] for h in history if h.get("blood_pressure_dia") is not None]
    temp_values = [h["temperature"] for h in history if h.get("temperature") is not None]


    latest = history[-1]


    stats = {}

    if hr_values:
        stats["heart_rate"] = {
            "min": round(min(hr_values), 1),
            "max": round(max(hr_values), 1),
            "avg": round(sum(hr_values) / len(hr_values), 1),
            "count": len(hr_values)
        }

    if spo2_values:
        stats["spo2"] = {
            "min": round(min(spo2_values), 1),
            "max": round(max(spo2_values), 1),
            "avg": round(sum(spo2_values) / len(spo2_values), 1),
            "count": len(spo2_values)
        }

    if sys_values:
        stats["blood_pressure_sys"] = {
            "min": round(min(sys_values), 1),
            "max": round(max(sys_values), 1),
            "avg": round(sum(sys_values) / len(sys_values), 1),
            "count": len(sys_values)
        }

    if dia_values:
        stats["blood_pressure_dia"] = {
            "min": round(min(dia_values), 1),
            "max": round(max(dia_values), 1),
            "avg": round(sum(dia_values) / len(dia_values), 1),
            "count": len(dia_values)
        }

    if temp_values:
        stats["temperature"] = {
            "min": round(min(temp_values), 1),
            "max": round(max(temp_values), 1),
            "avg": round(sum(temp_values) / len(temp_values), 1),
            "count": len(temp_values)
        }


    summary_lines = [
        f"📊 RÉSUMÉ STATISTIQUE des {len(history)} dernières mesures ({days} jours) :",
        ""
    ]

    if "heart_rate" in stats:
        hr = stats["heart_rate"]
        summary_lines.append(f"Fréquence cardiaque : min={hr['min']} | max={hr['max']} | moyenne={hr['avg']} bpm ({hr['count']} mesures)")

    if "spo2" in stats:
        spo2 = stats["spo2"]
        summary_lines.append(f"SpO₂ : min={spo2['min']} | max={spo2['max']} | moyenne={spo2['avg']} % ({spo2['count']} mesures)")

    if "blood_pressure_sys" in stats and "blood_pressure_dia" in stats:
        sys = stats["blood_pressure_sys"]
        dia = stats["blood_pressure_dia"]
        summary_lines.append(f"Pression artérielle : systolique min={sys['min']} | max={sys['max']} | moyenne={sys['avg']} mmHg")
        summary_lines.append(f"                     : diastolique min={dia['min']} | max={dia['max']} | moyenne={dia['avg']} mmHg")

    if "temperature" in stats:
        temp = stats["temperature"]
        summary_lines.append(f"Température : min={temp['min']} | max={temp['max']} | moyenne={temp['avg']} °C ({temp['count']} mesures)")

    summary_lines.append("")
    summary_lines.append(f"📡 DERNIÈRE MESURE ({latest.get('timestamp', '?')[:19].replace('T', ' ')}):")
    summary_lines.append(f"   • Fréquence cardiaque : {latest.get('heart_rate', 'N/A')} bpm")
    summary_lines.append(f"   • SpO₂ : {latest.get('spo2', 'N/A')} %")
    summary_lines.append(f"   • Pression artérielle : {latest.get('blood_pressure_sys', 'N/A')}/{latest.get('blood_pressure_dia', 'N/A')} mmHg")
    summary_lines.append(f"   • Température : {latest.get('temperature', 'N/A')} °C")

    return {
        "count": len(history),
        "summary": "\n".join(summary_lines),
        "latest": latest,
        "stats": stats
    }


def format_history_for_agents(history: list[dict]) -> str:
    if not history:
        return "Aucun historique disponible pour ce patient."

    lines = [f"📋 Historique des {len(history)} dernière(s) mesure(s) (15 jours) :\n"]
    for row in history:
        ts  = row.get("timestamp", "?")[:19].replace("T", " ")
        hr  = row.get("heart_rate", "N/A")
        spo2 = row.get("spo2", "N/A")
        sys_bp = row.get("blood_pressure_sys", "N/A")
        dia_bp = row.get("blood_pressure_dia", "N/A")
        temp = row.get("temperature", "N/A")
        lines.append(
            f"  [{ts}] FC={hr} bpm | SpO2={spo2}% | "
            f"PA={sys_bp}/{dia_bp} mmHg | T°={temp}°C"
        )
    return "\n".join(lines)


init_db()
