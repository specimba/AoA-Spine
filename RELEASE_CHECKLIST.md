# Release Checklist

- [ ] `python -m pip install -e .[dev]`
- [ ] `python boot_system.py`
- [ ] `python -m core.cli build-index --repo-root .`
- [ ] `python -m core.cli director-run --request-text "What providers are supported?"`
- [ ] `python -m pytest -q`
- [ ] Review `data/GOLDEN_DATASET_SEED.json` for release relevance
- [ ] Confirm README instructions still match the real commands
- [ ] Decide whether the embedder should remain stubbed or be integrated with a live backend
