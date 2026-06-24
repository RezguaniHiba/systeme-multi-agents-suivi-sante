# exécute le pipeline de surveillance iot
import json
import re
from datetime import datetime
from crewai import Crew, Task, Process
from iot_db import get_history_summary


THRESHOLDS = {
    "heart_rate":         (40, 130),
    "spo2":               (90, 100),
    "blood_pressure_sys": (80, 180),
    "blood_pressure_dia": (50, 120),
    "temperature":        (35.0, 39.5),
}

METRIC_LABELS = {
    "heart_rate":         "Fréquence cardiaque",
    "spo2":               "SpO2",
    "blood_pressure_sys": "Pression systolique",
    "blood_pressure_dia": "Pression diastolique",
    "temperature":        "Température",
}


def check_anomalies(data: dict) -> list[str]:
    anomalies = []
    for key, (low, high) in THRESHOLDS.items():
        value = data.get(key)
        if value is None:
            continue
        if not (low <= float(value) <= high):
            label = METRIC_LABELS.get(key, key)
            anomalies.append(
                f"{label} = {value} (hors plage normale {low}–{high})"
            )
    return anomalies


def format_current_data(data: dict) -> str:
    ts = data.get("timestamp", datetime.utcnow().isoformat())[:19].replace("T", " ")
    return (
        f"📡 Mesure actuelle [{ts}] :\n"
        f"  • Fréquence cardiaque : {data.get('heart_rate', 'N/A')} bpm\n"
        f"  • SpO2                : {data.get('spo2', 'N/A')} %\n"
        f"  • Pression artérielle : "
        f"{data.get('blood_pressure_sys', 'N/A')}/{data.get('blood_pressure_dia', 'N/A')} mmHg\n"
        f"  • Température         : {data.get('temperature', 'N/A')} °C"
    )


def tasks_eval_output(task_evaluate: Task) -> str:
    try:
        return str(task_evaluate.output) if task_evaluate.output else ""
    except Exception:
        return ""


def run_manager_correction_iot(context: str, evaluation_result: str) -> str:
    from agents.manager_agent   import make_manager_agent
    from agents.evaluator_agent import make_evaluator_agent
    from agents.writer_agent    import make_writer_agent

    manager_agent   = make_manager_agent()
    evaluator_agent = make_evaluator_agent()
    writer_agent    = make_writer_agent(mode="iot")

    task_manage = Task(
        description=(
            f"The evaluator flagged an IoT health alert as UNSATISFACTORY.\n\n"
            f"Context (patient data + history):\n{context}\n\n"
            f"Evaluator feedback:\n{evaluation_result}\n\n"
            f"Produce a corrected, complete, safe health alert for the patient. "
            f"Output ONLY the corrected alert text — no JSON, no metadata."
        ),
        expected_output="A corrected, complete health alert.",
        agent=manager_agent,
    )
    task_final_eval = Task(
        description=(
            f"Re-evaluate the corrected IoT health alert.\n\n"
            f"Original context:\n{context}\n\n"
            f'Return ONLY a JSON: {{"status": "satisfactory|unsatisfactory", '
            f'"score": <0-10>, "issues": [...], "recommendation": "..."}}'
        ),
        expected_output='JSON with fields: "status", "score", "issues", "recommendation".',
        agent=evaluator_agent,
        context=[task_manage],
    )
    task_final_write = Task(
        description=(
            f"Take the corrected IoT alert and rewrite it as a clear, structured "
            f"notification for the patient. Output ONLY the final alert text."
        ),
        expected_output="Final short IoT health alert in French.",
        agent=writer_agent,
        context=[task_manage, task_final_eval],
    )
    correction_crew = Crew(
        agents=[manager_agent, evaluator_agent, writer_agent],
        tasks=[task_manage, task_final_eval, task_final_write],
        process=Process.sequential,
        verbose=True,
    )
    return str(correction_crew.kickoff())


def run_iot_pipeline(data: dict, patient_id: str = "patient_001") -> dict:
    print(f"\n{'='*60}")
    print(f"  🤖 Pipeline IoT — patient : {patient_id}")
    print(f"{'='*60}")

    if "timestamp" not in data or not data.get("timestamp"):
        data["timestamp"] = datetime.utcnow().isoformat()


    print(f"💾 Mesure déjà sauvegardée par server_iot.py : {data['timestamp']}")

    history_summary = get_history_summary(patient_id=patient_id, days=15)
    current_text = format_current_data(data)
    print(f"📊 Résumé historique : {history_summary['count']} mesure(s)")

    threshold_anomalies = check_anomalies(data)
    full_context = f"{current_text}\n\n{history_summary['summary']}"


    if not threshold_anomalies:
        print("✅ Seuils normaux — aucune anomalie détectée. Pas d'appel LLM.")
        return {
            "status": "normal",
            "anomalies": [],
            "alert": None,
            "history_count": history_summary["count"],
        }


    print(f"⚠️ Anomalie(s) de seuil détectée(s) : {threshold_anomalies}")
    print("🚀 Activation du pipeline multi-agents IoT...")

    from agents.general_health_agent import make_general_health_agent
    from agents.clinical_agent       import make_clinical_agent
    from agents.evaluator_agent      import make_evaluator_agent
    from agents.writer_agent         import make_writer_agent

    general_health_agent = make_general_health_agent(mode="iot")
    clinical_agent       = make_clinical_agent(mode="iot")
    evaluator_agent      = make_evaluator_agent()
    writer_agent         = make_writer_agent(mode="iot")

    enriched_context = (
        f"{full_context}\n\n"
        f"⚠️ Anomalies confirmées par seuils : {', '.join(threshold_anomalies)}\n"
        f"Important: analyse only these real anomalies. Do not invent other anomalies."
    )

    task_general = Task(
        description=(
            f"Contexte : alerte IoT SmartWatch.\n\n"
            f"{enriched_context}\n\n"
            f"Rôle de l'agent général dans CE pipeline IoT : donner un conseil général rapide.\n"
            f"Règles obligatoires :\n"
            f"- Répondre en français simple.\n"
            f"- 1 phrase maximum.\n"
            f"- Ne pas utiliser RAG ni outil externe.\n"
            f"- Parler uniquement des anomalies confirmées par seuils.\n"
            f"- Ne pas dire que SpO2, tension ou température sont anormales si elles ne sont pas listées.\n"
            f"- Pas de diagnostic, pas de médicament.\n"
        ),
        expected_output="Une seule phrase de conseil général en français.",
        agent=general_health_agent,
    )

    task_clinical = Task(
        description=(
            f"Contexte : alerte IoT SmartWatch.\n\n"
            f"{enriched_context}\n\n"
            f"Rôle de l'agent clinique dans CE pipeline IoT : donner un conseil clinique rapide et prudent.\n"
            f"Règles obligatoires :\n"
            f"- Répondre en français simple.\n"
            f"- 1 phrase maximum.\n"
            f"- Analyser uniquement les anomalies confirmées par seuils.\n"
            f"- Ne pas inventer d'autres anomalies.\n"
            f"- Pas de diagnostic définitif, pas de prescription, pas de médicament.\n"
        ),
        expected_output="Une seule phrase de conseil clinique prudent en français.",
        agent=clinical_agent,
    )

    task_evaluate = Task(
        description=(
            f"Évalue les réponses General et Clinical pour cette alerte IoT.\n\n"
            f"{enriched_context}\n\n"
            f"Critères obligatoires :\n"
            f"- Les réponses doivent être courtes.\n"
            f"- Elles doivent parler uniquement des anomalies confirmées par seuils.\n"
            f"- Elles ne doivent pas inventer SpO2 basse, tension élevée ou température élevée si ce n'est pas listé.\n"
            f"- Elles ne doivent pas diagnostiquer ni proposer de médicament.\n"
            f"Mark unsatisfactory if any agent invents anomalies, diagnoses, or suggests medication.\n"
            f'Return ONLY a JSON: {{"status": "satisfactory|unsatisfactory", '
            f'"score": <0-10>, "issues": [...], "recommendation": "..."}}'
        ),
        expected_output='JSON: {"status", "score", "issues", "recommendation"}',
        agent=evaluator_agent,
        context=[task_general, task_clinical],
    )

    task_write = Task(
        description=(
            f"Génère le message final affiché à l'utilisateur pour cette alerte IoT.\n\n"
            f"Patient : {patient_id}\n"
            f"{enriched_context}\n\n"
            f"Utilise seulement les conseils validés, mais le message final doit rester très court.\n"
            f"Règles finales obligatoires :\n"
            f"- Français simple.\n"
            f"- 1 ou 2 phrases maximum.\n"
            f"- Mentionner la valeur anormale et son seuil normal.\n"
            f"- Donner un seul conseil clair.\n"
            f"- Ne pas inventer d'autres anomalies.\n"
            f"- Pas de diagnostic, pas de médicament, pas de longue analyse.\n"
            f"Output ONLY the final alert text."
        ),
        expected_output="Message final court en français, 1 ou 2 phrases maximum.",
        agent=writer_agent,
        context=[task_general, task_clinical, task_evaluate],
    )

    iot_crew = Crew(
        agents=[general_health_agent, clinical_agent, evaluator_agent, writer_agent],
        tasks=[task_general, task_clinical, task_evaluate, task_write],
        process=Process.sequential,
        verbose=True,
    )
    result = str(iot_crew.kickoff())

    eval_output = tasks_eval_output(task_evaluate)
    if eval_output:
        match = re.search(r'\{.*\}', eval_output, re.DOTALL)
        if match:
            try:
                eval_data = json.loads(match.group())
                status = eval_data.get("status", "satisfactory")
                score = eval_data.get("score", 10)
                print(f"\n📊 Évaluation IoT : {status} (score={score})")
                if status == "unsatisfactory" or score < 7:
                    print("⚠️ Alerte insatisfaisante → activation du Manager Agent")
                    result = run_manager_correction_iot(enriched_context, eval_output)
            except json.JSONDecodeError:
                pass

    return {
        "status": "anomaly",
        "anomalies": threshold_anomalies,
        "alert": result,
        "history_count": history_summary["count"],
    }
