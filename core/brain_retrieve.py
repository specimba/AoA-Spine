from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from .brain_store import BrainStore
from .embedder import HashingEmbedder, OllamaEmbedder
from .reranker import SurgicalReranker


@dataclass
class RetrievalPlan:
    plan_type: str
    query: str
    top_k: int = 5
    embedding_backend: str = "ollama"


@dataclass
class QueryProfile:
    normalized_query: str
    source_kinds: set[str] = field(default_factory=set)
    downweight_areas: set[str] = field(default_factory=set)
    must_terms: set[str] = field(default_factory=set)
    boost_terms: set[str] = field(default_factory=set)
    path_terms: set[str] = field(default_factory=set)
    symbol_terms: set[str] = field(default_factory=set)
    phrase_terms: tuple[str, ...] = ()
    oversample_factor: int = 6

    @property
    def expanded_query(self) -> str:
        expansion_terms = sorted(self.must_terms | self.boost_terms | self.path_terms | self.symbol_terms)
        if not expansion_terms:
            return self.normalized_query
        return f"{self.normalized_query} {' '.join(expansion_terms)}".strip()


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_./:-]*")


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def _build_query_profile(query: str, plan_type: str) -> QueryProfile:
    normalized_query = " ".join(query.split())
    tokens = _tokenize(normalized_query)

    must_terms = {token for token in tokens if len(token) > 2}
    path_terms = {token for token in tokens if any(marker in token for marker in ("/", ".", "\\"))}
    symbol_terms = {token for token in tokens if "_" in token or token.endswith("()")}
    phrase_terms = tuple(match.group(1).lower() for match in re.finditer(r'"([^"]+)"', normalized_query))
    boost_terms: set[str] = set()
    source_kinds: set[str] = set()
    downweight_areas: set[str] = set()
    oversample_factor = 6

    if plan_type == "code_lookup":
        source_kinds = {"code", "doc"}
        boost_terms.update({"function", "class", "import", "module"})
        oversample_factor = 8
        if "test" not in tokens and "tests" not in tokens:
            downweight_areas.add("tests")
    elif plan_type in {"policy_lookup", "doc_lookup"}:
        source_kinds = {"doc"}
        boost_terms.update({"guide", "policy", "readme"})
        oversample_factor = 5

    if any(token in {"why", "how", "when"} for token in tokens):
        boost_terms.update({"overview", "usage"})

    return QueryProfile(
        normalized_query=normalized_query,
        source_kinds=source_kinds,
        downweight_areas=downweight_areas,
        must_terms=must_terms,
        boost_terms=boost_terms,
        path_terms=path_terms,
        symbol_terms=symbol_terms,
        phrase_terms=phrase_terms,
        oversample_factor=oversample_factor,
    )


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    return dot / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0.0


def execute_retrieval_plan(store: BrainStore, plan: RetrievalPlan) -> list[dict[str, object]]:
    profile = _build_query_profile(plan.query, plan.plan_type)
    embedder = OllamaEmbedder() if plan.embedding_backend == "ollama" else HashingEmbedder()
    query_embedding = embedder.embed_texts([profile.expanded_query])[0]

    results = store.search_documents(
        query=profile.expanded_query,
        top_k=plan.top_k * profile.oversample_factor,
        query_embedding=query_embedding,
        plan_type=plan.plan_type,
        source_kinds=profile.source_kinds or None,
        query_profile={
            "must_terms": sorted(profile.must_terms),
            "boost_terms": sorted(profile.boost_terms),
            "downweight_areas": sorted(profile.downweight_areas),
        },
    )

    rescored_results: list[dict[str, object]] = []
    missing_embedding_docs = [item["document"].text for item in results if not item["document"].embedding]
    generated_embeddings = iter(embedder.embed_texts(missing_embedding_docs)) if missing_embedding_docs else iter(())

    for item in results:
        doc = item["document"]
        base_score = float(item["score"])
        doc_embedding = doc.embedding if doc.embedding else next(generated_embeddings)
        semantic_bonus = _cosine_similarity(query_embedding, doc_embedding) if doc_embedding else 0.0
        rescored_results.append(
            {
                "document": doc,
                "score": (base_score * 0.65) + (semantic_bonus * 0.35),
                "semantic_score": semantic_bonus,
            }
        )

    return SurgicalReranker().rerank(
        rescored_results,
        plan.query,
        plan.plan_type,
        query_profile=profile,
    )[: plan.top_k]
