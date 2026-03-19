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
- add stronger lexical retrieval
- add real dense embeddings
- add reranking
- add retrieval metrics

### Milestone 3
- add hardware profiles
- add preflight budget estimation
- add packet compression and spill policy
- add runtime telemetry

## Source Guidance

Use current repo assets as the runnable baseline.

Borrow selectively from:
- `brain.zip` for evidence packs, query profiles, and Director trace discipline
- AoA v1 for packaging and release discipline
- Hugging Face for retriever, reranker, dataset, and demo surfaces
- GPT4All for local-first runtime philosophy
