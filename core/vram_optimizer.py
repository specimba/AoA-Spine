from __future__ import annotations

from typing import Any


class VRAMOptimizer:
    """Hardware logic for Q8 KV-cache budgeting and RAM spilling."""

    def __init__(self, hardware_profile: str = "8gb"):
        self.max_vram_tokens = 12000 if hardware_profile == "8gb" else 6000
        self.max_system_ram_tokens = 32000

    def get_budget_map(self, requested_tokens: int) -> dict[str, Any]:
        if requested_tokens <= self.max_vram_tokens:
            return {
                "safety_gate": True,
                "strategy": "FULL_VRAM",
                "vram_tokens": requested_tokens,
                "ram_tokens": 0,
            }

        if requested_tokens <= self.max_system_ram_tokens:
            return {
                "safety_gate": True,
                "strategy": "HYBRID_SPILL",
                "vram_tokens": self.max_vram_tokens,
                "ram_tokens": requested_tokens - self.max_vram_tokens,
            }

        return {"safety_gate": False, "strategy": "REFUSE_OVERFLOW"}

