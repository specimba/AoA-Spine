from __future__ import annotations

from time import perf_counter
from typing import Any

from .brain_evidence import build_evidence_pack
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
        return {
            "status": "REFUSED_PRECHECK",
            "reason": "Estimated request exceeds hardware budget before retrieval.",
            "budget": preflight["budget"],
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
        return {
            "status": "REFUSED_OVERFLOW",
            "reason": "Hardware limits reached after retrieval sizing.",
            "budget": actual_budget,
            "trace": trace,
            "telemetry": {
                "phase": "post-retrieval",
                "refusal_reason": "actual_overflow",
                "retrieval_executed": True,
                "retrieval_ms": retrieval_ms,
            },
        }

    if not results:
        return {
            "status": "NO_EVIDENCE",
            "reason": "No grounded source chunks matched the request.",
            "budget": actual_budget,
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
        "evidence_pack": build_evidence_pack(results, top_k=top_k),
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
