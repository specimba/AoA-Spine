from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HardwareProfile:
    name: str
    max_vram_tokens: int
    max_system_ram_tokens: int
    default_top_k: int
    target_chunk_tokens: int
    spill_allowed: bool = True


class VRAMOptimizer:
    """Hardware logic for preflight estimation, spill strategy, and overflow refusal."""

    _PROFILES: dict[str, HardwareProfile] = {
        "4gb": HardwareProfile(
            name="4gb",
            max_vram_tokens=6000,
            max_system_ram_tokens=18000,
            default_top_k=3,
            target_chunk_tokens=180,
            spill_allowed=True,
        ),
        "8gb": HardwareProfile(
            name="8gb",
            max_vram_tokens=12000,
            max_system_ram_tokens=32000,
            default_top_k=5,
            target_chunk_tokens=240,
            spill_allowed=True,
        ),
        "16gb": HardwareProfile(
            name="16gb",
            max_vram_tokens=24000,
            max_system_ram_tokens=64000,
            default_top_k=8,
            target_chunk_tokens=320,
            spill_allowed=True,
        ),
        "cpu-only": HardwareProfile(
            name="cpu-only",
            max_vram_tokens=0,
            max_system_ram_tokens=24000,
            default_top_k=3,
            target_chunk_tokens=180,
            spill_allowed=True,
        ),
        "micro": HardwareProfile(
            name="micro",
            max_vram_tokens=3000,
            max_system_ram_tokens=10000,
            default_top_k=2,
            target_chunk_tokens=140,
            spill_allowed=True,
        ),
    }

    def __init__(self, hardware_profile: str = "8gb"):
        self.profile = self._PROFILES.get(hardware_profile, self._PROFILES["8gb"])

    @classmethod
    def supported_profiles(cls) -> list[str]:
        return sorted(cls._PROFILES.keys())

    def get_budget_map(self, requested_tokens: int) -> dict[str, Any]:
        if self.profile.max_vram_tokens and requested_tokens <= self.profile.max_vram_tokens:
            return {
                "safety_gate": True,
                "strategy": "FULL_VRAM",
                "hardware_profile": self.profile.name,
                "requested_tokens": requested_tokens,
                "vram_tokens": requested_tokens,
                "ram_tokens": 0,
            }

        if requested_tokens <= self.profile.max_system_ram_tokens and self.profile.spill_allowed:
            return {
                "safety_gate": True,
                "strategy": "HYBRID_SPILL" if self.profile.max_vram_tokens else "CPU_ONLY",
                "hardware_profile": self.profile.name,
                "requested_tokens": requested_tokens,
                "vram_tokens": min(requested_tokens, self.profile.max_vram_tokens),
                "ram_tokens": max(0, requested_tokens - self.profile.max_vram_tokens),
            }

        return {
            "safety_gate": False,
            "strategy": "REFUSE_OVERFLOW",
            "hardware_profile": self.profile.name,
            "requested_tokens": requested_tokens,
            "vram_tokens": self.profile.max_vram_tokens,
            "ram_tokens": max(0, requested_tokens - self.profile.max_vram_tokens),
        }

    def estimate_preflight(
        self,
        request_text: str,
        top_k: int | None = None,
        average_chunk_tokens: int | None = None,
    ) -> dict[str, Any]:
        effective_top_k = max(1, top_k if top_k is not None else self.profile.default_top_k)
        chunk_tokens = max(
            1,
            average_chunk_tokens if average_chunk_tokens is not None else self.profile.target_chunk_tokens,
        )
        prompt_tokens = max(1, len(request_text.split()))
        retrieval_tokens = effective_top_k * chunk_tokens
        estimated_tokens = prompt_tokens + retrieval_tokens
        budget = self.get_budget_map(estimated_tokens)

        return {
            "hardware_profile": self.profile.name,
            "requested_top_k": effective_top_k,
            "average_chunk_tokens": chunk_tokens,
            "request_tokens": prompt_tokens,
            "retrieval_tokens": retrieval_tokens,
            "estimated_total_tokens": estimated_tokens,
            "budget": budget,
        }
