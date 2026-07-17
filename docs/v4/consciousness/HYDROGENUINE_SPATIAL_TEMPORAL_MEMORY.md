# T09 — Hydrogenuine spatial-temporal memory

Coverage: **C049–C052**. Gate: **G39**. Lane: **quarantined**.
Status: `ENGINEERING_PROTOTYPE` — all four.

## What this is

The **safe engineering branch**: an embodied spatial-temporal memory
architecture inspired by Arisaka-style structures, built as software.

It is a memory system. It is not a brain model, not a neuroscience
claim, and **not conscious** (G39).

## Components

| ID | Component | Falsified if |
|---|---|---|
| C049 | embodied spatial event memory | retrieval benchmark fails |
| C050 | SWR-like replay / offline consolidation | replay does not improve the declared benchmark |
| C051 | Q-HAL local world-memory block | block fails its capacity/latency benchmark |
| C052 | BFFT transform/compression scaffold | transform is not invertible within the declared error bound |

Every one is falsified by an **engineering benchmark**, which is the
correct kind of test for an engineering artifact. None is falsified by
a claim about minds, because none makes one.

## Design elements

Spatial-temporal event records; coordinate frames and object
permanence; local world-memory blocks; phase/time indexing;
BFFT-inspired transform/compression; replay and SWR-like offline
consolidation **as engineering analogues**; confidence and provenance;
conflict reconciliation; identity anchoring; SOAR/HAL/GPP/RTC
integration; **no self-authorization**; audit receipts; navigation and
recall benchmarks.

## Naming discipline

"SWR-like" means *inspired by sharp-wave ripples*, not *equivalent to*
them. Hippocampal replay is a real, measured phenomenon; a software
replay buffer that consolidates offline is a software replay buffer.
The resemblance is a design inspiration, and the biological name is
retained with "-like" attached precisely so the analogy cannot be
quietly upgraded.

The same applies to "holographic" in C051's lineage — see
[ARISAKA_AUDIT.md](ARISAKA_AUDIT.md), where the ring attractor is the
component that actually works and the word adds nothing.

## Governance

- **No self-authorization.** The system cannot grant itself
  permissions.
- Audit receipts for every memory write.
- Privacy and permission boundaries enforced.
- Benchmarks must beat **simpler memory** — an architecture that does
  not outperform a plain store has not earned its complexity.

## Failure modes tested

Deterministic replay, memory corruption, stale world models,
conflicting observations, privacy leakage, permission boundaries,
**hallucinated permanence** (the system asserting an object persists
when it has no evidence), and benchmark gains over simpler baselines.

## Boundary

**Do not call the system conscious, AGI, or a validated brain model.**
It is a memory architecture with benchmarks, and the benchmarks are how
it is judged.
