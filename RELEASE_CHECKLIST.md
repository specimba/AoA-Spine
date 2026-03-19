# Release Checklist

- [ ] `python -m pip install -e .[dev]`
- [ ] `python boot_system.py`
- [ ] `.\aoa-spine.ps1 build-index --repo-root . --reset`
- [ ] `.\aoa-spine.ps1 director-run --request-text "What providers are supported?" --plan-type code_lookup --embedding-backend hash`
- [ ] `.\aoa-spine.ps1 eval-report`
- [ ] `python -m pytest -q`
- [ ] Review `reports/eval-report.json` and confirm benchmark claims remain honest
- [ ] Confirm README instructions still match the real commands
- [ ] Confirm package metadata, version, and URLs are correct
- [ ] Decide whether the embedder should remain local-hash-first or be integrated with a live backend
