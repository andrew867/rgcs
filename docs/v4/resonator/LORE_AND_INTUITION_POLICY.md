# Private lore ledger and the intuition-to-hypothesis pipeline
(Agents L01, L02)

## L01 — the private lore ledger (mechanism, not content)

The human story — intuitions, coincidences, encounters, creative
leads — is preserved in a **private, consent-controlled ledger** at
`internal-docs/private/LORE_LEDGER.md` (gitignored; never in any
public asset; the release source filter and Q07 both check).

Ledger entry schema (each entry):

- date; what was observed/felt (OBSERVATION — verbatim, unedited);
- what it seemed to mean (INTERPRETATION — clearly separated);
- consent status (private / shareable-with-attribution /
  shareable-anonymous);
- any research translation (link to a hypothesis record, if one was
  made);
- explicit note that presence in the ledger is not evidence.

Rules, binding:

1. **Observation and interpretation never share a sentence.**
2. Content is excluded from public assets **by default**; sharing any
   entry requires explicit consent recorded in the entry.
3. Nothing in the ledger may be cited as evidence in any scientific
   document. The ledger records that an idea occurred, not that it is
   true.
4. **No assistant may diagnose or pathologize Andrew based on
   unconventional research content.** An assistant may state
   uncertainty, and may separate observation from interpretation —
   that is the whole extent of its role here. (Binding rule from the
   master orchestrator, restated where it applies.)

## L02 — intuition-to-hypothesis pipeline with hit/miss accounting

Andrew's real workflow — a felt connection to a paper before deep
reading — becomes an explicit, calibratable pipeline:

1. **Capture** the felt connection BEFORE deep reading: one sentence,
   dated, in the intuition ledger
   (`docs/v4/resonator/INTUITION_LEDGER.json`).
2. **Translate**: what mechanism might connect? what would be
   observable? what would falsify the connection?
3. **Read and implement**: the reference model or transfer.
4. **Score the outcome**, one of: `USEFUL_TRANSFER` (mathematics or
   method genuinely adopted), `WEAK_ANALOGY` (interesting, nothing
   adopted), `NULL` (no connection survived reading),
   `MISLEADING` (the felt connection pointed the work in a wrong
   direction that cost effort).
5. **Report the ratio**, including misses. A hit rate without a
   denominator is a testimonial.

### Baseline cohort (retrospective — labelled as such)

The five 2026 papers were selected before this pipeline existed, so
they form a RETROSPECTIVE baseline, which cannot measure selection
skill (survivorship: papers that felt connected and went nowhere may
already be forgotten). Scored honestly:

| Paper | Outcome | What was adopted |
|---|---|---|
| spin-electric (Q01) | USEFUL_TRANSFER | tunability-vs-linewidth bookkeeping; threshold nonlinearity model |
| triangular transport (Q02) | USEFUL_TRANSFER | the total-change/redistribution/transfer-function classification — now in the discrimination tree |
| honeycomb VHS (Q03) | USEFUL_TRANSFER | spacing-tunes-bandwidth as a resonator-lattice design principle |
| Feynman filtration (Q04) | WEAK_ANALOGY | workflow demo built; **no RGCS solve restructured yet** — scored weak until a measured benefit exists |
| neutron OAM (Q05→R11) | USEFUL_TRANSFER | parity selection + azimuthal decomposition, verified computationally |

Retrospective ratio: 4 useful / 1 weak / 0 null / 0 misleading —
**and this number is not evidence of selection skill** (see
survivorship note above). The pipeline's value begins with the first
prospective entry.

### Prospective protocol (from now on)

Every future candidate paper gets a ledger entry at step 1 BEFORE
reading, and every entry gets scored — including the ones that go
nowhere. The ledger is append-only. The honest metric after N
prospective entries is the full outcome distribution, not the hits.

Status: L01 mechanism active (private ledger local-only); L02
pipeline defined with its baseline labelled retrospective;
prospective accounting starts at the next paper.
