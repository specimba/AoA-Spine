# Implementation Order

## Order of Execution

Build in this order or the map will drift:

1. storage correctness
2. metadata correctness
3. structural chunking
4. truthful retrieval
5. evidence pack protocol
6. budget engine
7. Director routing
8. evaluation harness
9. product/demo surfaces

## Why This Order Matters

If orchestration is built before retrieval truth, the system becomes polished but
misleading.

If demos are built before evaluation, the project will look stronger than it is.

If budget logic is built after multi-agent routing, weak hardware will fail under
exactly the workloads the product claims to support.

## Immediate Build Targets

### Milestone 1
- replace append-only indexing with upsert/reset behavior
- add evidence pack construction
- add Director refusal and misalignment states
- improve fallback embedding behavior

### Milestone 2
- add structural chunking
- replace heuristic lexical search with a stronger lexical baseline
- add reciprocal-rank fusion only after both lexical and dense retrieval are measured independently
- add real dense embeddings only after the lexical baseline is measured
- add reranking and retrieval metrics
- defer ColBERTv2 until benchmark evidence shows the simpler stack is insufficient
- treat Matryoshka-style compact embeddings as an optimization phase after the baseline is trustworthy

### Milestone 3
- add hardware profiles
- add preflight budget estimation
- add packet compression and spill policy
- add runtime telemetry

### Milestone 4
- add typed worker packet families
- add packet schema versioning
- add replayable packet artifacts

### Milestone 5
- add held-out retrieval benchmarks
- add reasoning-intensive retrieval tasks
- add retrieval metrics and ablation comparisons
- add raw per-task artifacts, manifests, and environment capture
- add negative controls and failure taxonomy labeling
- add plotting-ready tables for scientific presentation
- only then evaluate whether ColBERTv2, SPLADE, or stronger compression methods are necessary

### Milestone 6
- align package, install, and release identity
- keep claim boundaries synced to measured evaluation
- publish only the surfaces that the current evidence supports

## Source Guidance

Use current repo assets as the runnable baseline.

Borrow selectively from:
- `brain.zip` for evidence packs, query profiles, and Director trace discipline
- AoA v1 for packaging and release discipline
- Hugging Face for retriever, reranker, dataset, and demo surfaces
- GPT4All for local-first runtime philosophy

Do not adopt advanced retrieval architectures by default until the simpler
baseline has been benchmarked and shown insufficient.
