from __future__ import annotations

from dataclasses import dataclass

from .brain_store import BrainStore
from .embedder import HashingEmbedder, OllamaEmbedder
from .reranker import SurgicalReranker


@dataclass
class RetrievalPlan:
    plan_type: str
    query: str
    top_k: int = 5
    embedding_backend: str = "ollama"


def execute_retrieval_plan(store: BrainStore, plan: RetrievalPlan) -> list[dict[str, object]]:
    embedder = OllamaEmbedder() if plan.embedding_backend == "ollama" else HashingEmbedder()
    query_embedding = embedder.embed_texts([plan.query])[0]

    results = store.search_documents(
        query=plan.query,
        top_k=plan.top_k,
        query_embedding=query_embedding,
        plan_type=plan.plan_type,
    )

    return SurgicalReranker().rerank(results, plan.query, plan.plan_type)[: plan.top_k]

