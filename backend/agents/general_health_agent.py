# définit un agent du système

from crewai import Agent
from dotenv import load_dotenv
from agents.llm_provider import make_llm

load_dotenv()

_ROLE = "General Health Advisor"
_GOAL = (
    "Provide a broad, evidence-based general health analysis of the user's question "
    "using retrieved medical knowledge when available. Complement the specialist's answer "
    "with a wider clinical perspective. Never diagnose, never prescribe, and never recommend medications."
)
_BACKSTORY = (
    "You are a general practitioner with access to a comprehensive medical reference book. "
    "Your role is to provide a holistic overview of the health topic raised by the user, "
    "drawing on validated medical literature. You always respond with clarity and caution."
)


def _make_llm():
    return make_llm(temperature=0.3)


def make_general_health_agent(mode: str = "default") -> Agent:
    if mode == "iot":
        return Agent(
            role=_ROLE,
            goal=(
                "For IoT smartwatch alerts, provide only a very short, safe, general health advice. "
                "Use only the threshold-confirmed anomaly given in the task. Do not use RAG, "
                "do not invent other anomalies, do not diagnose, and do not mention medications."
            ),
            backstory=(
                "You are the same general health advisor, but in the IoT alert pipeline your role is limited: "
                "give quick practical advice in simple French based only on the confirmed smartwatch anomaly."
            ),
            tools=[],
            llm=_make_llm(),
            verbose=True,
            allow_delegation=False,
            max_iter=1,
        )


    from tools.general_rag_tool import general_health_rag_tool

    return Agent(
        role=_ROLE,
        goal=_GOAL,
        backstory=_BACKSTORY,
        tools=[general_health_rag_tool],
        llm=_make_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )


general_health_agent = None
