from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


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


@dataclass
class AgentPacket:
    packet_version: str
    packet_type: str
    packet_id: str
    request_id: str
    task_id: str
    plan_type: str
    created_at: str
    owner_lane: str
    target_lane: str
    routing_reason: str
    primary_owner: str
    ownership_locked: bool
    evidence_sufficient: bool
    confidence: float
    missing_signals: list[str]
    open_questions: list[str]
    required_followup: list[str]
    evidence_token_count: int
    compression_level: str
    objective: str
    scope_boundary: str
    allowed_actions: list[str]
    forbidden_actions: list[str]
    expected_output: str
    evidence_count: int
    sources: list[dict[str, Any]]
    trace_id: str
    parent_packet_id: str | None = None
    next_owner: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
        "evidence_token_count": sum(len(item.excerpt.split()) for item in evidence_items),
    }


def build_agent_packet(
    *,
    request_text: str,
    plan_type: str,
    evidence_pack: dict[str, Any],
    owner_lane: str,
    target_lane: str,
    routing_reason: str,
    confidence: float,
    evidence_sufficient: bool,
    missing_signals: list[str] | None = None,
    open_questions: list[str] | None = None,
    required_followup: list[str] | None = None,
    allowed_actions: list[str] | None = None,
    forbidden_actions: list[str] | None = None,
    expected_output: str = "Grounded answer or bounded handoff report.",
    scope_boundary: str = "Do not exceed cited evidence and assigned lane.",
    task_id: str = "active-task",
    request_id: str | None = None,
    trace_id: str | None = None,
    parent_packet_id: str | None = None,
) -> dict[str, Any]:
    request_id = request_id or f"req-{uuid4().hex[:10]}"
    trace_id = trace_id or f"trace-{uuid4().hex[:10]}"
    packet = AgentPacket(
        packet_version="1.0",
        packet_type="director_handoff",
        packet_id=f"pkt-{uuid4().hex[:10]}",
        request_id=request_id,
        task_id=task_id,
        plan_type=plan_type,
        created_at=datetime.now(UTC).isoformat(),
        owner_lane=owner_lane,
        target_lane=target_lane,
        routing_reason=routing_reason,
        primary_owner=target_lane,
        ownership_locked=True,
        evidence_sufficient=evidence_sufficient,
        confidence=round(confidence, 3),
        missing_signals=missing_signals or [],
        open_questions=open_questions or [],
        required_followup=required_followup or [],
        evidence_token_count=int(evidence_pack.get("evidence_token_count", 0)),
        compression_level="compact",
        objective=request_text,
        scope_boundary=scope_boundary,
        allowed_actions=allowed_actions or ["summarize", "answer", "handoff"],
        forbidden_actions=forbidden_actions or ["invent facts", "expand beyond evidence", "co-own implementation slices"],
        expected_output=expected_output,
        evidence_count=int(evidence_pack.get("evidence_count", 0)),
        sources=list(evidence_pack.get("sources", [])),
        trace_id=trace_id,
        parent_packet_id=parent_packet_id,
    )
    return packet.to_dict()
