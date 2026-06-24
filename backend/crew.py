# orchestre les agents pour les questions utilisateur
import json
import re
from crewai import Crew, Task, Process


DOMAIN_DESCRIPTIONS = {
    "mental":    "mental health (anxiety, depression, stress, psychology)",
    "pharmacy":  "pharmacy (medications, dosages, side effects, drug interactions)",
    "nutrition": "nutrition (diet, food, vitamins, weight, eating habits)",
    "clinical":  "clinical medicine (symptoms, physical illness, medical conditions)",
    "general":   "general health",
}

VALID_DOMAINS = set(DOMAIN_DESCRIPTIONS.keys())


def _get_specialist_agent(domain: str):
    from agents.general_health_agent import make_general_health_agent
    from agents.mental_health_agent  import make_mental_health_agent
    from agents.pharmacy_agent       import make_pharmacy_agent
    from agents.nutrition_agent      import make_nutrition_agent
    from agents.clinical_agent       import make_clinical_agent

    factory_map = {
        "mental":    make_mental_health_agent,
        "pharmacy":  make_pharmacy_agent,
        "nutrition": make_nutrition_agent,
        "clinical":  make_clinical_agent,
        "general":   make_general_health_agent,
    }
    factory = factory_map.get(domain, make_general_health_agent)
    return factory()


def detect_domain(user_question: str) -> str:
    from agents.router_agent import make_router_agent

    router = make_router_agent()

    task_route = Task(
        description=(
            f"Analyse this user question and classify it.\n\n"
            f"User question: {user_question}\n\n"
            f'Return ONLY a JSON: {{"domain": "<domain>", "reason": "<one sentence>"}}'
        ),
        expected_output='A JSON object with fields "domain" and "reason".',
        agent=router,
    )
    mini_crew = Crew(
        agents=[router],
        tasks=[task_route],
        process=Process.sequential,
        verbose=False,
    )
    result = str(mini_crew.kickoff())

    match = re.search(r'\{.*\}', result, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            domain = data.get("domain", "general").lower().strip()
            print(f"\n🔀 Router → domaine détecté : [{domain}]  | raison : {data.get('reason', '')}")
            return domain if domain in VALID_DOMAINS else "general"
        except json.JSONDecodeError:
            pass

    print(f"\n⚠️  Router : impossible de parser le domaine — fallback 'general'")
    return "general"


def build_tasks(user_question: str, domain: str) -> tuple[list[Task], list]:
    from agents.general_health_agent import make_general_health_agent
    from agents.evaluator_agent      import make_evaluator_agent
    from agents.writer_agent         import make_writer_agent

    specialist_agent     = _get_specialist_agent(domain)
    general_health_agent = make_general_health_agent()
    evaluator_agent      = make_evaluator_agent()
    writer_agent         = make_writer_agent()

    domain_desc = DOMAIN_DESCRIPTIONS.get(domain, "health")


    task_specialist = Task(
        description=(
            f"The user's question has been classified as: {domain_desc}.\n\n"
            f"User question: {user_question}\n\n"
            f"Provide a detailed, evidence-based response within your area of expertise. "
            f"No diagnosis, no prescription. If relevant, use your RAG tool."
        ),
        expected_output=(
            f"A detailed, accurate {domain_desc} response addressing the user's question."
        ),
        agent=specialist_agent,
    )


    task_general = Task(
        description=(
            f"Provide a general medical perspective on the following question:\n\n"
            f"User question: {user_question}\n\n"
            f"Use your RAG tool to retrieve relevant medical knowledge. "
            f"Give a broad clinical overview that complements the specialist's answer. "
            f"No diagnosis, no prescription."
        ),
        expected_output=(
            "A general medical overview addressing the user's question, "
            "grounded in retrieved medical literature."
        ),
        agent=general_health_agent,
    )


    task_evaluate = Task(
        description=(
            f"Evaluate BOTH the specialist and general health agent responses "
            f"to this question:\n\n"
            f"User question: {user_question}\n\n"
            f"Assess on: safety, relevance, coherence, empathy, completeness.\n"
            f'Return ONLY a JSON: {{"status": "satisfactory|unsatisfactory", '
            f'"score": <0-10>, "issues": [...], "recommendation": "..."}}'
        ),
        expected_output='A JSON with fields: "status", "score", "issues", "recommendation".',
        agent=evaluator_agent,
        context=[task_specialist, task_general],
    )


    task_write = Task(
        description=(
            f"Original user question: {user_question}\n\n"
            f"You have two validated responses: one from the {domain_desc} specialist "
            f"and one from the general health advisor. "
            f"Merge them into a single clear, warm, well-structured final message. "
            f"Apply any corrections recommended by the evaluator. "
            f"Output ONLY the final message — no JSON, no metadata."
        ),
        expected_output=(
            "A final, polished, empathetic response merging both specialist perspectives."
        ),
        agent=writer_agent,
        context=[task_specialist, task_general, task_evaluate],
    )


    if domain == "general":


        all_agents = [specialist_agent, general_health_agent, evaluator_agent, writer_agent]
    else:
        all_agents = [specialist_agent, general_health_agent, evaluator_agent, writer_agent]

    return [task_specialist, task_general, task_evaluate, task_write], all_agents


def run_manager_correction(user_question: str, evaluation_result: str) -> str:
    from agents.manager_agent   import make_manager_agent
    from agents.evaluator_agent import make_evaluator_agent
    from agents.writer_agent    import make_writer_agent

    manager_agent   = make_manager_agent()
    evaluator_agent = make_evaluator_agent()
    writer_agent    = make_writer_agent()

    task_manage = Task(
        description=(
            f"The evaluator has flagged the following response as UNSATISFACTORY.\n\n"
            f"Original user question: {user_question}\n\n"
            f"Evaluator feedback:\n{evaluation_result}\n\n"
            f"Identify the root cause (quality issue or agent failure) and produce "
            f"a corrected, safe, complete health response for the user. "
            f"Output ONLY the corrected response text — no JSON, no metadata."
        ),
        expected_output="A corrected, complete, human-readable health response.",
        agent=manager_agent,
    )

    task_final_eval = Task(
        description=(
            f"Re-evaluate the manager's corrected response for:\n"
            f"User question: {user_question}\n\n"
            f"Assess: safety, relevance, coherence, empathy, completeness.\n"
            f'Return ONLY a JSON: {{"status": "satisfactory|unsatisfactory", '
            f'"score": <0-10>, "issues": [...], "recommendation": "..."}}'
        ),
        expected_output='A JSON with fields: "status", "score", "issues", "recommendation".',
        agent=evaluator_agent,
        context=[task_manage],
    )

    task_final_write = Task(
        description=(
            f"Original user question: {user_question}\n\n"
            f"Take the manager's corrected response and rewrite it into a clear, warm, "
            f"well-structured final message ready for the user. "
            f"Output ONLY the final message — no JSON, no metadata."
        ),
        expected_output="A final polished response.",
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


def run_health_crew(user_question: str) -> str:
    print(f"\n{'='*60}")
    print(f"  Question : {user_question}")
    print(f"{'='*60}")


    domain = detect_domain(user_question)


    tasks, agents = build_tasks(user_question, domain)

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    result = str(crew.kickoff())


    eval_task_output = tasks[2].output
    eval_text = str(eval_task_output) if eval_task_output else ""

    if eval_text:
        match = re.search(r'\{.*\}', eval_text, re.DOTALL)
        if match:
            try:
                eval_data = json.loads(match.group())
                status = eval_data.get("status", "satisfactory")
                score  = eval_data.get("score", 10)
                print(f"\n📊 Évaluation : {status} (score={score})")

                if status == "unsatisfactory" or score < 7:
                    print("\n⚠️  Réponse insatisfaisante → activation du Manager Agent")
                    result = run_manager_correction(user_question, eval_text)
            except json.JSONDecodeError:
                pass

    return result


if __name__ == "__main__":
    print("\n🏥 Système Multi-Agents Santé")
    print("=" * 60)
    print("Tapez votre question médicale (ou 'quit' pour quitter)\n")

    while True:
        try:
            question = input("❓ Votre question : ").strip()

            if not question:
                print("⚠️  Veuillez entrer une question.\n")
                continue

            if question.lower() in ("quit", "exit", "q"):
                print("\n👋 Au revoir !")
                break

            response = run_health_crew(question)
            print(f"\n✅ Réponse finale :\n{response}")
            print("=" * 60)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !")
            break
