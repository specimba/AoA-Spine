from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvidenceItem:
    doc_id: str
    source_path: str
    source_area: str
    source_kind: str
    title: str
    score: float
    excerpt: str
    metadata: dict[str, Any]


def build_evidence_pack(
    retrieval_results: list[dict[str, Any]],
    *,
    top_k: int | None = None,
    excerpt_chars: int = 240,
) -> dict[str, Any]:
    limited_results = retrieval_results if top_k is None else retrieval_results[:top_k]
    evidence_items: list[EvidenceItem] = []

    for result in limited_results:
        document = result["document"]
        evidence_items.append(
            EvidenceItem(
                doc_id=document.doc_id,
                source_path=document.source_path,
                source_area=getattr(document, "source_area", "unknown"),
                source_kind=document.source_kind,
                title=document.title,
                score=round(float(result.get("score", 0.0)), 6),
                excerpt=document.text[:excerpt_chars].strip(),
                metadata=dict(document.metadata),
            )
        )

    return {
        "evidence_count": len(evidence_items),
        "sources": [item.__dict__ for item in evidence_items],
    }
