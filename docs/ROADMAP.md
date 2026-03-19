# Roadmap

## Phase 0: Product Lock

Lock the product definition before implementation grows.

Deliverables:
- stable product thesis
- terminology map
- architecture map
- scope boundaries for low-VRAM and grounded execution

## Phase 1: Truthful Spine

Goal: make the system honest before making it powerful.

Build:
- upsert-based storage
- real evidence pack module
- structural metadata model
- deterministic refusal and status paths
- traceable Director packet output

## Phase 2: Real Retrieval

Goal: make retrieval worth trusting.

Build:
- stronger lexical retrieval baseline first
- dense retrieval with a real compact model after the lexical baseline is measured
- reciprocal-rank fusion after both lexical and dense rankers are independently credible
- budget-gated reranking
- structural chunking for code and docs
- explicit benchmark comparison against the current heuristic stack
- revisit Matryoshka-style compact embeddings only after the baseline is benchmarked
- defer ColBERTv2 until the benchmark shows simpler retrieval is insufficient

## Phase 3: Low-VRAM Intelligence

Goal: make the package differentiated.

Build:
- hardware profiles
- pre-retrieval budget estimation
- retrieval fanout control
- rerank gating
- evidence token caps
- spill and refusal strategy

## Phase 4: Agent Packet Protocol

Goal: turn retrieval into multi-agent leverage.

Build:
- typed agent packet contracts
- one-owner slice routing
- confidence and sufficiency signals
- packet-first worker execution
- packet schema versioning
- packet replay and artifact persistence

## Phase 5: Evaluation and Proof

Goal: make claims defensible.

Build:
- benchmark suite
- retrieval metrics such as Recall@k, MRR, and nDCG
- grounding metrics
- telemetry capture
- ablation reports
- reasoning-intensive retrieval tasks in addition to direct lookup tasks
- baseline-first comparison before advanced retrieval additions
- task-level raw run artifacts
- benchmark manifests with hashes and environment capture
- negative controls and impossible-task refusals
- human-audited sample sets
- plotting-ready report tables and variance summaries

## Phase 6: Product Release

Goal: make the system adoptable.

Build:
- polished package identity
- release artifacts
- compatibility matrix
- install path
- demo surface
- dataset and eval artifact publication strategy
- explicit claim boundaries tied to the current evaluation card
- release proof bundle with benchmark summary, manifest, and raw artifact references
