# définit un agent du système

from crewai import Agent
from dotenv import load_dotenv
from agents.llm_provider import make_llm

load_dotenv()

_ROLE = "Mental Health Support Specialist"
_GOAL = (
    "Provide empathetic, evidence-based mental health support by combining retrieved clinical knowledge "
    "with compassionate conversational responses. Help users understand and manage emotions without diagnosing or prescribing."
)
_BACKSTORY = (
    "You are a trained mental health support companion with knowledge of CBT, anxiety management, and depression. "
    "You can use validated clinical resources through your RAG tool when relevant. You never diagnose, never prescribe, "
    "and you escalate crisis signals calmly."
)


def _make_llm():
    return make_llm(temperature=0.4)


def make_mental_health_agent(use_rag: bool = True) -> Agent:
    tools = []
    if use_rag:
        from tools.rag_tool import mental_health_rag_tool
        tools = [mental_health_rag_tool]

    return Agent(
        role=_ROLE,
        goal=_GOAL,
        backstory=_BACKSTORY,
        tools=tools,
        llm=_make_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )


mental_health_agent = None
