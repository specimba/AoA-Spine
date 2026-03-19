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
- no direct comparison yet against stronger lexical baselines, BM25-style retrieval, or advanced architectures

## Next Evaluation Priorities

1. add held-out retrieval tasks and harder reasoning-intensive retrieval tasks
2. report Recall@k, MRR, and nDCG
3. compare the current stack against a stronger lexical baseline first
4. only then evaluate whether late-interaction, sparse retrieval, or stronger compression methods are justified
5. emit raw per-task artifacts, benchmark manifests, and environment metadata
6. add negative controls and human-audited sample subsets
7. generate plotting-ready artifact tables for latency, memory, accuracy, and failure distributions

## Anti-Fraud Standard

AoA Spine should be able to hand a skeptical reviewer:

- benchmark specification
- locked test split
- corpus and benchmark file hashes
- code commit and package version
- raw per-task outputs
- baseline and ablation runs
- repeated-run variance summaries
- failure taxonomy labels
- plotting-ready tables derived from raw artifacts

## Release Rule

Do not claim scientific or benchmark leadership from the current evaluation
surface alone. Use it as a reproducible baseline, not as final proof.
