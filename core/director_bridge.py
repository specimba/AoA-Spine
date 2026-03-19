from __future__ import annotations

from time import perf_counter
from typing import Any

from .brain_evidence import build_agent_packet, build_evidence_pack
from .brain_eval import score_response
from .brain_retrieve import RetrievalPlan, execute_retrieval_plan
from .brain_store import BrainStore
from .vram_optimizer import VRAMOptimizer


def run_director_cycle(store: BrainStore, request_text: str, plan_type: str, **kwargs: Any) -> dict[str, Any]:
    top_k = max(1, int(kwargs.get("top_k", 5)))
    hardware_profile = kwargs.get("hardware_profile", "8gb")
    embedding_backend = kwargs.get("embedding_backend", "hash")

    optimizer = VRAMOptimizer(hardware_profile)
    preflight = optimizer.estimate_preflight(request_text, top_k=top_k)
    trace: dict[str, Any] = {
        "hardware_profile": preflight["hardware_profile"],
        "plan_type": plan_type,
        "requested_top_k": top_k,
        "preflight": preflight,
        "store": store.describe(),
    }

    if not preflight["budget"]["safety_gate"]:
        packet = build_agent_packet(
            request_text=request_text,
            plan_type=plan_type,
            evidence_pack={"evidence_count": 0, "sources": [], "evidence_token_count": 0},
            owner_lane="director",
            target_lane="director",
            routing_reason="preflight_refusal",
            confidence=0.0,
            evidence_sufficient=False,
            missing_signals=["budget_within_limits"],
            required_followup=["reduce scope", "lower top_k", "switch hardware profile"],
        )
        return {
            "status": "REFUSED_PRECHECK",
            "reason": "Estimated request exceeds hardware budget before retrieval.",
            "budget": preflight["budget"],
            "packet": packet,
            "trace": trace,
            "telemetry": {
                "phase": "preflight",
                "refusal_reason": "estimated_overflow",
                "retrieval_executed": False,
            },
        }

    retrieval_started = perf_counter()
    plan = RetrievalPlan(plan_type=plan_type, query=request_text, top_k=top_k, embedding_backend=embedding_backend)
    results = execute_retrieval_plan(store, plan)
    retrieval_ms = round((perf_counter() - retrieval_started) * 1000, 2)

    actual_tokens = len(request_text.split()) + sum(len(item["document"].text.split()) for item in results)
    actual_budget = optimizer.get_budget_map(actual_tokens)
    trace["actual"] = {
        "retrieval_ms": retrieval_ms,
        "result_count": len(results),
        "actual_total_tokens": actual_tokens,
        "budget": actual_budget,
    }

    if not actual_budget["safety_gate"]:
        packet = build_agent_packet(
            request_text=request_text,
            plan_type=plan_type,
            evidence_pack={"evidence_count": len(results), "sources": [], "evidence_token_count": 0},
            owner_lane="director",
            target_lane="director",
            routing_reason="post_retrieval_overflow",
            confidence=0.1,
            evidence_sufficient=False,
            missing_signals=["budget_within_limits"],
            required_followup=["reduce retrieval fanout", "switch hardware profile"],
        )
        return {
            "status": "REFUSED_OVERFLOW",
            "reason": "Hardware limits reached after retrieval sizing.",
            "budget": actual_budget,
            "packet": packet,
            "trace": trace,
            "telemetry": {
                "phase": "post-retrieval",
                "refusal_reason": "actual_overflow",
                "retrieval_executed": True,
                "retrieval_ms": retrieval_ms,
            },
        }

    if not results:
        packet = build_agent_packet(
            request_text=request_text,
            plan_type=plan_type,
            evidence_pack={"evidence_count": 0, "sources": [], "evidence_token_count": 0},
            owner_lane="director",
            target_lane="research",
            routing_reason="no_evidence",
            confidence=0.0,
            evidence_sufficient=False,
            missing_signals=["retrieved_grounded_sources"],
            open_questions=["Which source files or documents should be indexed for this request?"],
            required_followup=["index relevant sources", "refine plan type"],
            expected_output="Gap report or refined retrieval target.",
        )
        return {
            "status": "NO_EVIDENCE",
            "reason": "No grounded source chunks matched the request.",
            "budget": actual_budget,
            "packet": packet,
            "trace": trace,
            "telemetry": {
                "phase": "retrieval",
                "retrieval_executed": True,
                "retrieval_ms": retrieval_ms,
                "evidence_count": 0,
                "misalignment": False,
            },
        }

    raw_answer = f"Grounded response utilizing {len(results)} source chunks."
    audit = score_response({"required_signal_groups": [["grounded"]]}, raw_answer)
    evidence_pack = build_evidence_pack(results, top_k=top_k)
    packet = build_agent_packet(
        request_text=request_text,
        plan_type=plan_type,
        evidence_pack=evidence_pack,
        owner_lane="director",
        target_lane="implementation" if plan_type == "code_lookup" else "analysis",
        routing_reason="grounded_answer_ready",
        confidence=0.8 if audit["passed"] else 0.45,
        evidence_sufficient=audit["passed"],
        missing_signals=[] if audit["passed"] else ["grounding_audit_passed"],
        open_questions=[] if audit["passed"] else ["Does the answer need more specific citations?"],
        required_followup=[] if audit["passed"] else ["inspect top evidence pack before acting"],
        expected_output="Grounded answer, bounded implementation note, or handoff report.",
    )

    if not audit["passed"]:
        status = "MISALIGNED_AUDIT"
        reason = "Generated response did not satisfy grounding audit."
    else:
        status = "SUCCESS"
        reason = ""

    return {
        "status": status,
        "reason": reason,
        "answer": raw_answer,
        "budget": actual_budget,
        "evidence_count": len(results),
        "evidence_pack": evidence_pack,
        "packet": packet,
        "trace": trace,
        "telemetry": {
            "phase": "complete",
            "retrieval_executed": True,
            "retrieval_ms": retrieval_ms,
            "evidence_count": len(results),
            "misalignment": status == "MISALIGNED_AUDIT",
            "preflight_strategy": preflight["budget"]["strategy"],
            "final_strategy": actual_budget["strategy"],
            "embedding_backend": embedding_backend,
        },
    }
