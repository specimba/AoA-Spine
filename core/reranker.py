from __future__ import annotations

import re


class SurgicalReranker:
    """
    CPU-bound mathematical reranker optimized for 0GB VRAM footprint.
    """

    def __init__(self):
        self.exact_identifier_weight = 0.50
        self.structural_anchor_bonus = 0.20
        self.markdown_bias_penalty = 0.45

    def rerank(
        self,
        results: list[dict[str, object]],
        query: str,
        plan_type: str,
        query_profile=None,
    ) -> list[dict[str, object]]:
        if not results:
            return []

        query_tokens = set(query.lower().split())
        must_terms = set(getattr(query_profile, "must_terms", set())) or query_tokens
        path_terms = set(getattr(query_profile, "path_terms", set()))
        symbol_terms = set(getattr(query_profile, "symbol_terms", set()))
        phrase_terms = tuple(getattr(query_profile, "phrase_terms", ()))
        query_identifiers = {
            term
            for term in must_terms | symbol_terms
            if "_" in term or (term.replace(".", "").replace("/", "").isalnum() and len(term) > 3)
        }

        reranked = []
        for item in results:
            doc = item["document"]
            base_score = float(item["score"])
            text_lower = doc.text.lower()
            path_lower = doc.source_path.lower()
            title_lower = doc.title.lower()

            id_match_count = sum(1 for identifier in query_identifiers if identifier in text_lower)
            density_bonus = (id_match_count / max(len(query_identifiers), 1)) * self.exact_identifier_weight

            nl_penalty = 0.0
            if plan_type == "code_lookup" and doc.source_path.endswith((".md", ".txt")):
                nl_penalty = self.markdown_bias_penalty

            artifact_bonus = 0.0
            if plan_type == "code_lookup" and any(k in text_lower for k in ["def ", "class ", "import "]):
                artifact_bonus = self.structural_anchor_bonus

            coverage = sum(1 for term in must_terms if term in text_lower or term in path_lower or term in title_lower)
            coverage_bonus = 0.30 * (coverage / max(len(must_terms), 1))

            path_bonus = 0.18 * sum(1 for term in path_terms if term in path_lower or term in title_lower)
            symbol_bonus = 0.15 * sum(1 for term in symbol_terms if term.rstrip("()") in text_lower)
            phrase_bonus = 0.25 * sum(1 for phrase in phrase_terms if phrase in text_lower or phrase in path_lower)

            code_bias = 0.0
            if plan_type == "code_lookup" and doc.source_kind == "code":
                code_bias = 0.12
            if plan_type in {"policy_lookup", "doc_lookup"} and doc.source_kind == "doc":
                code_bias = 0.12

            lexical_hits = len(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text_lower))
            sparse_penalty = 0.08 if must_terms and coverage == 0 and lexical_hits < 8 else 0.0

            final_score = (
                base_score
                + density_bonus
                + artifact_bonus
                + coverage_bonus
                + path_bonus
                + symbol_bonus
                + phrase_bonus
                + code_bias
                - nl_penalty
                - sparse_penalty
            )
            reranked.append(
                {
                    "document": doc,
                    "score": final_score,
                    "original_score": base_score,
                    "coverage": coverage,
                }
            )

        reranked.sort(key=lambda item: item["score"], reverse=True)
        return reranked
