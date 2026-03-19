# Decision Record

## Decision Pass: Post-Milestone 6

This decision pass was made after the Milestone 6 baseline and before further
major additions. The goal is to stay strict, evidence-based, and conservative.

## Voting Outcome

### Keep

- evidence compression routing as the central systems idea
- packet-first worker routing
- local-first low-VRAM product boundary
- preflight budget estimation and refusal
- reproducible evaluation reports as a release gate

### Add Next

- stronger lexical retrieval baseline before more complex neural retrieval
- reciprocal rank fusion once there are two independently credible rankers
- held-out retrieval benchmarks and harder reasoning-oriented eval tasks
- packet schema versioning and replay-ready packet artifacts
- retrieval metrics such as Recall@k, MRR, and nDCG in the evaluation surface
- per-task raw artifact capture with manifests, hashes, and environment metadata
- plotting-ready CSV/JSONL tables for latency, memory, accuracy, and failure analysis
- negative controls and human-audited benchmark subsets

### Defer

- late-interaction retrieval such as ColBERTv2 until the stronger lexical+dense baseline is benchmarked
- sparse neural retrieval such as SPLADE until benchmark evidence shows the simpler stack is insufficient
- heavy quantization or compressed-index research until the retrieval stack is stable enough to measure
- browser or cloud-heavy execution sidecars
- public scientific claims beyond the current evaluation surface

## Scientific Rationale

- BEIR indicates BM25 remains a robust retrieval baseline while reranking and
  late interaction improve quality at a higher computational cost.
- BRIGHT suggests reasoning-intensive retrieval should be tested explicitly and
  that better query reasoning can materially change retrieval performance.
- ColBERTv2 shows late interaction can be space-efficient relative to older
  late-interaction systems, but it still adds significant implementation and
  runtime complexity relative to the current AoA Spine stage.
- Matryoshka Representation Learning is promising for dimension-flexible
  embeddings, but should be treated as a later optimization after the baseline
  retrieval stack is trustworthy.

## Proof Requirements

To make AoA Spine results hard to fake or dismiss, the project should emit:

- fixed benchmark manifests with file hashes
- raw per-task outputs and traces
- run-level environment metadata
- baseline and ablation comparisons
- repeated-run summaries with variance
- failure taxonomy labels
- plot-ready artifact tables

## Strict Rule

No major retrieval architecture should be added unless:

1. a baseline exists
2. a benchmark demonstrates the current baseline is insufficient
3. the new addition can be measured against latency, memory, and quality
