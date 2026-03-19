# Evaluation Card

## Current Evaluation Surface

AoA Spine currently evaluates three layers:

1. smoke and contract tests in `tests/`
2. golden seed checks from `data/GOLDEN_DATASET_SEED.json`
3. reproducible report generation via `aoa-spine eval-report`

## Current Metrics

- scenario pass rate
- golden eval pass rate
- Director status outputs
- retrieval telemetry
- budget strategy traces

## Current Limits

- not yet a full held-out benchmark suite
- no external retrieval leaderboard comparison yet
- no ablation harness yet
- no hardware-normalized longitudinal report set yet

## Release Rule

Do not claim scientific or benchmark leadership from the current evaluation
surface alone. Use it as a reproducible baseline, not as final proof.
