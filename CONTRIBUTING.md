# Contributing

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Standard Validation

Run these checks before proposing a release:

```powershell
python boot_system.py
.\aoa-spine.ps1 build-index --repo-root . --reset
.\aoa-spine.ps1 director-run --request-text "What providers are supported?" --plan-type code_lookup --embedding-backend hash
.\aoa-spine.ps1 eval-report
python -m pytest -q
```

## Change Rules

- Keep the runtime dependency surface small by default.
- Preserve safe local execution when external services are absent.
- Prefer additive fixtures and tests over hidden behavior changes.
- If you replace the embedding stub with a live provider, keep a local fallback path.
- Preserve packet contract compatibility unless you intentionally version the packet schema.
