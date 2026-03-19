# AoA Spine 1.0

AoA Spine 1.0 is a local-first, low-VRAM, evidence-bounded multi-agent
intelligence spine for repository work.

The system is being built around one strict goal:

> retrieve the smallest sufficient evidence, route compact packets to the right
> agent lane, and stay stable on consumer-grade hardware.

This repository currently contains the first runnable spine plus the planning
documents that define the production direction.

## Product Direction

AoA Spine is not meant to be a generic autonomous swarm or a vague prompt pack.
It is meant to become:

- grounded repository intelligence
- low-VRAM multi-agent coordination
- evidence-compressed task routing
- measurable retrieval and evaluation infrastructure

Start with these docs:

- [Product Vision](C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine\docs\PRODUCT_VISION.md)
- [System Architecture](C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine\docs\SYSTEM_ARCHITECTURE.md)
- [Roadmap](C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine\docs\ROADMAP.md)
- [Implementation Order](C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine\docs\IMPLEMENTATION_ORDER.md)
- [System Card](C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine\docs\SYSTEM_CARD.md)
- [Evaluation Card](C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine\docs\EVALUATION_CARD.md)

## Current Repository Surface

```text
AoA-v2-Surgical-Spine/
├─ core/                  Runtime modules
├─ data/                  Fixtures, seeds, and telemetry samples
├─ docs/                  Vision, architecture, roadmap, implementation order
├─ tests/                 Smoke coverage
├─ boot_system.py         Minimal startup check
├─ pyproject.toml         Packaging and CLI entrypoint
├─ CONTRIBUTING.md        Local development guidance
└─ RELEASE_CHECKLIST.md   Pre-release validation checklist
```

## Quick Start

```powershell
cd C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python boot_system.py
.\aoa-spine.ps1 build-index --repo-root . --reset
.\aoa-spine.ps1 director-run --request-text "What providers are supported?" --plan-type code_lookup --embedding-backend hash --trace
.\aoa-spine.ps1 eval-report
python -m pytest -q
```

## One-Minute Verification

```powershell
.\aoa-spine.ps1 build-index --repo-root . --reset
.\aoa-spine.ps1 director-run --request-text "How does the budget strategy work?" --plan-type code_lookup --embedding-backend hash --hardware-profile 8gb --trace
.\aoa-spine.ps1 eval-report
```

## Current Status

The repository is validated as a runnable baseline, not yet as a production
claim:

- `python boot_system.py`
- `.\aoa-spine.ps1 build-index --repo-root . --reset`
- `.\aoa-spine.ps1 director-run --request-text "What providers are supported?" --plan-type code_lookup --embedding-backend hash`
- `.\aoa-spine.ps1 eval-report`
- `python -m pytest -q`

## Current Limits

- retrieval is still prototype-grade
- embedding backends are not yet production-real
- low-VRAM logic is still shallow
- evaluation is still smoke-level, not benchmark-grade

That is intentional in the current stage. The roadmap in `docs/` is the source
of truth for how this becomes AoA Spine 1.0 rather than remaining a recovered
prototype.
