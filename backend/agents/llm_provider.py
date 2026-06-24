# définit un agent du système

import os
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()


def _normalize_base_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _detect_provider() -> str:
    provider = (os.getenv("AI_PROVIDER") or "").strip().lower()
    endpoint = (os.getenv("AI_ENDPOINT") or "").strip().lower()
    if provider:
        return provider
    if "localhost:11434" in endpoint or "127.0.0.1:11434" in endpoint:
        return "ollama"
    return "openai"


def _openai_model_name(model_name: str) -> str:
    model_name = (model_name or "gpt-4o-mini").strip()
    if model_name.startswith("openai/"):
        return model_name
    return f"openai/{model_name}"


def make_llm(temperature: float = 0.3) -> LLM:
    provider = _detect_provider()
    model_name = (os.getenv("AI_MODEL") or "gpt-4o-mini").strip()
    api_key = (os.getenv("AI_API_KEY") or "").strip()
    endpoint = _normalize_base_url(os.getenv("AI_ENDPOINT") or "")

    if provider == "ollama":
        base_url = endpoint.replace("/v1", "") or "http://localhost:11434"
        return LLM(
            model=f"ollama/{model_name}",
            api_key=api_key or "ollama",
            base_url=base_url,
            temperature=temperature,
        )

    if not api_key or api_key.lower() == "ollama":
        raise ValueError("AI_API_KEY manquant ou invalide dans .env")
    if not endpoint:
        endpoint = "https://api.openai.com/v1"

    return LLM(
        model=_openai_model_name(model_name),
        api_key=api_key,
        base_url=endpoint,
        temperature=temperature,
    )
