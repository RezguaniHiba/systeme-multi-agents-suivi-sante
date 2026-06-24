# définit un agent du système

from crewai import Agent
import os
from dotenv import load_dotenv
from agents.llm_provider import make_llm

load_dotenv()

_ROLE      = "Medical Domain Router"
_GOAL      = (
    "Analyse the user's question and determine the most relevant medical domain. "
    "Output ONLY a JSON object with two fields: "
    "'domain' (one of: mental, nutrition, pharmacy, clinical, general) "
    "and 'reason' (one sentence explaining the choice)."
)
_BACKSTORY = (
    "You are an expert medical triage specialist. Your only job is to read a user "
    "question and classify it into the correct medical domain so it can be routed "
    "to the right specialist agent. You are fast, precise, and never answer the "
    "question yourself — you only classify it. "
    "Domains you recognise:\n"
    "  - mental    : emotions, anxiety, depression, stress, mental health, psychology\n"
    "  - nutrition : diet, food, vitamins, weight, eating habits\n"
    "  - pharmacy  : medications, drugs, dosage, side effects, interactions\n"
    "  - clinical  : symptoms, diagnosis, physical illness, medical conditions\n"
    "  - general   : anything that doesn't fit clearly into one domain above"
)


def _make_llm():
    return make_llm(temperature=0.0)


def make_router_agent() -> Agent:
    return Agent(
        role=_ROLE,
        goal=_GOAL,
        backstory=_BACKSTORY,
        tools=[],
        llm=_make_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=1,
    )


router_agent = make_router_agent()
