# prépare les documents utilisés par le rag

import os
from typing import Type
from dotenv import load_dotenv
from pinecone import Pinecone
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

load_dotenv()

_PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
_INDEX_NAME = os.getenv("PINECONE_INDEX")
_pc = None
_index = None
_embeddings = None


class MentalHealthRAGInput(BaseModel):
    query: str = Field(..., description="Short search query for the mental health knowledge base.")


def _get_index():
    global _pc, _index
    if _index is None:
        if not _PINECONE_API_KEY or not _INDEX_NAME:
            raise RuntimeError("PINECONE_API_KEY ou PINECONE_INDEX manquant dans .env")
        _pc = Pinecone(api_key=_PINECONE_API_KEY)
        _index = _pc.Index(_INDEX_NAME)
    return _index


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings


class MentalHealthRAGTool(BaseTool):
    name: str = "mental_health_rag"
    description: str = (
        "Searches the mental health knowledge base and returns relevant excerpts. "
        "Input must be a plain string query."
    )
    args_schema: Type[BaseModel] = MentalHealthRAGInput

    def _run(self, query: str) -> str:
        try:
            if isinstance(query, dict):
                query = query.get("query", str(query))
            query_vector = _get_embeddings().embed_query(str(query))
            results = _get_index().query(vector=query_vector, top_k=5, include_metadata=True)
            contexts = []
            for m in results.get("matches", [])[:3]:
                meta = m.get("metadata", {})
                text = meta.get("text")
                if text:
                    contexts.append(f"[Source: {meta.get('source', 'unknown')}]\n{text}")
            return "\n\n---\n\n".join(contexts) if contexts else "No relevant context found in the knowledge base."
        except Exception as e:
            return f"RAG retrieval error: {e}"


mental_health_rag_tool = MentalHealthRAGTool()
