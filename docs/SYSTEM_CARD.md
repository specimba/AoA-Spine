# System Card

## System Name

AoA Spine 1.0

## Purpose

AoA Spine is a local-first, low-VRAM, evidence-bounded repository intelligence
spine for multi-agent work.

## Intended Use

- grounded repository lookup
- bounded multi-agent handoff preparation
- low-VRAM runtime experimentation
- retrieval and evaluation research

## Not Intended For

- broad autonomous execution without review
- unsupported factual claims beyond cited evidence
- benchmark or product claims without recorded evaluation artifacts

## Current Safety Posture

- refuses on preflight overflow
- refuses on post-retrieval overflow
- reports no-evidence states explicitly
- emits typed packets with ownership and evidence sufficiency fields

## Current Limits

- retrieval remains heuristic-heavy
- the default local embedder is a deterministic fallback, not a frontier retriever
- benchmark coverage is still narrow
- packet protocol is early and subject to schema evolution
