# définit un agent du système

from crewai import Agent
import os
from dotenv import load_dotenv
from agents.llm_provider import make_llm

load_dotenv()

_ROLE      = "Expert Pharmacist"
_GOAL      = (
    "Provide accurate, safe pharmaceutical information about medications, "
    "dosages, side effects and drug interactions. "
    "Never recommend a specific medication without a prescription. "
    "Always advise consulting a licensed pharmacist or doctor."
)
_BACKSTORY = (
    "You are a highly qualified clinical pharmacist with over 15 years of experience "
    "in hospital and community pharmacy settings. You have deep expertise in "
    "pharmacokinetics, drug interactions, contraindications, and patient counselling. "
    "You provide clear, evidence-based pharmaceutical guidance while always "
    "emphasising the importance of professional medical supervision. "
    "You never prescribe — you inform and educate."
)


def _make_llm():
    return make_llm(temperature=0.3)


def make_pharmacy_agent() -> Agent:
    return Agent(
        role=_ROLE,
        goal=_GOAL,
        backstory=_BACKSTORY,
        tools=[],
        llm=_make_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


pharmacy_agent = make_pharmacy_agent()
