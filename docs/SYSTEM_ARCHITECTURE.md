# System Architecture

## Layer Model

AoA Spine should be built in seven layers.

1. Source Layer
- repository files
- docs
- plans
- policies
- task history
- optional telemetry traces

2. Ingest Layer
- structural chunking
- deterministic ids
- metadata enrichment
- source-area labeling
- dedup and upsert

3. Retrieval Layer
- lexical retrieval
- dense retrieval
- fusion
- reranking
- plan-aware filtering

4. Evidence Layer
- evidence items
- evidence packs
- citation references
- trace snapshots

5. Budget Layer
- hardware profiles
- preflight cost estimation
- retrieval fanout control
- rerank gating
- spill and refusal policy

6. Director Layer
- plan selection
- packet routing
- evidence sufficiency checks
- grounded answer synthesis
- refusal and escalation logic

7. Evaluation Layer
- replay harness
- retrieval metrics
- grounding metrics
- telemetry reports
- ablation comparisons

## Runtime Flow

1. ingest approved sources
2. upsert normalized chunks into the memory spine
3. select a retrieval plan
4. retrieve and rerank bounded candidates
5. compress the top results into an evidence pack
6. check budget and sufficiency
7. route the evidence pack to the Director or worker lane
8. answer, escalate, or refuse
9. capture traces for replay and evaluation

## Key Design Rule

Workers should receive compact evidence packets by default, not the entire raw
retrieval context.

This is the central mechanism for keeping multi-agent work stable on 4GB to 8GB
machines.

## Innovation Focus

The highest-upside system technique is evidence compression routing:

- retrieve once
- rank once
- compress to typed packets
- reuse packets across agent lanes
- expand only when needed
- count packet cost against the runtime budget
