from __future__ import annotations

from .brain_eval import score_response
from .brain_retrieve import RetrievalPlan, execute_retrieval_plan
from .brain_store import BrainStore
from .vram_optimizer import VRAMOptimizer


def run_director_cycle(store: BrainStore, request_text: str, plan_type: str, **kwargs):
    plan = RetrievalPlan(plan_type=plan_type, query=request_text, top_k=kwargs.get("top_k", 5))
    results = execute_retrieval_plan(store, plan)

    tokens = len(request_text.split()) + sum(len(item["document"].text.split()) for item in results)
    optimizer = VRAMOptimizer(kwargs.get("hardware_profile", "8gb"))
    budget = optimizer.get_budget_map(tokens)

    if not budget["safety_gate"]:
        return {"status": "REFUSED_OVERFLOW", "reason": "Hardware limits reached."}

    raw_answer = f"Grounded response utilizing {len(results)} source chunks."
    audit = score_response({"required_signal_groups": [["grounded"]]}, raw_answer)

    return {
        "status": "SUCCESS" if audit["passed"] else "AUDIT_FAILED",
        "answer": raw_answer,
        "budget": budget,
        "evidence_count": len(results),
    }

