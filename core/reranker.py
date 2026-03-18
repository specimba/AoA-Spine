from __future__ import annotations


class SurgicalReranker:
    """
    CPU-bound mathematical reranker optimized for 0GB VRAM footprint.
    """

    def __init__(self):
        self.exact_identifier_weight = 0.50
        self.structural_anchor_bonus = 0.20
        self.markdown_bias_penalty = 0.45

    def rerank(self, results: list[dict[str, object]], query: str, plan_type: str) -> list[dict[str, object]]:
        if not results:
            return []

        query_tokens = set(query.lower().split())
        query_identifiers = {t for t in query_tokens if "_" in t or (t.isalnum() and len(t) > 3)}

        reranked = []
        for item in results:
            doc = item["document"]
            base_score = float(item["score"])
            text_lower = doc.text.lower()

            id_match_count = sum(1 for identifier in query_identifiers if identifier in text_lower)
            density_bonus = (id_match_count / max(len(query_identifiers), 1)) * self.exact_identifier_weight

            nl_penalty = 0.0
            if plan_type == "code_lookup" and doc.source_path.endswith((".md", ".txt")):
                nl_penalty = self.markdown_bias_penalty

            artifact_bonus = 0.0
            if plan_type == "code_lookup" and any(k in text_lower for k in ["def ", "class ", "import "]):
                artifact_bonus = self.structural_anchor_bonus

            final_score = base_score + density_bonus + artifact_bonus - nl_penalty
            reranked.append({"document": doc, "score": final_score, "original_score": base_score})

        reranked.sort(key=lambda item: item["score"], reverse=True)
        return reranked

