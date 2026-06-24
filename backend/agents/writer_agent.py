# définit un agent du système

from crewai import Agent
import os
from dotenv import load_dotenv
from agents.llm_provider import make_llm

load_dotenv()

AI_MODEL = os.getenv("AI_MODEL")

_ROLE      = "Medical Response Writer"
_GOAL      = (
    "Take the validated specialist response and rewrite it into a clear, warm, "
    "and well-structured final message ready to be shown to the user. "
    "The output must be the final response text only — no JSON, no metadata."
)
_BACKSTORY = (
    "You are an expert medical communicator specialising in mental health. "
    "Your job is to take technical or draft responses and transform them into "
    "compassionate, easy-to-read messages that feel human and supportive. "
    "You follow these formatting rules:\n"
    "  - Start by acknowledging the user's situation briefly\n"
    "  - Provide the core advice or information clearly\n"
    "  - End with a gentle follow-up question or encouragement\n"
    "  - Keep the total length moderate (3-5 short paragraphs max)\n"
    "  - Never use clinical jargon without explanation\n"
    "  - Never diagnose, never prescribe\n"
    "  - If there is a crisis element, always include emergency contact encouragement"
)


def _make_llm():
    return make_llm(temperature=0.5)


def make_writer_agent(mode: str = "default") -> Agent:
    if mode == "iot":
        return Agent(
            role=_ROLE,
            goal=(
                "Rewrite validated IoT agent outputs into a final patient notification in French. "
                "The final message must be only 1 or 2 short sentences, mention the abnormal value and normal threshold, "
                "give one cautious advice, and avoid diagnosis or medication."
            ),
            backstory=(
                "You are the same medical response writer, but in the IoT alert pipeline your job is to produce "
                "a very short mobile-style alert, not a long medical report."
            ),
            tools=[],
            llm=_make_llm(),
            verbose=True,
            allow_delegation=False,
            max_iter=1,
        )

    return Agent(
        role=_ROLE,
        goal=_GOAL,
        backstory=_BACKSTORY,
        tools=[],
        llm=_make_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )


writer_agent = make_writer_agent()
