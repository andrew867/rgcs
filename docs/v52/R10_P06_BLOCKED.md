# R10 P06 — BLOCKED: the 144.000 source frame

**State:** `BLOCKED`
**Blocking condition:** no source record exists to ingest.
**Date:** 2026-07-19

---

## What P06 requires

The phase asks us to ingest the original private frame, determine what
is *visibly present* in it, and only then decide whether `144.000` is a
frequency, a count, or something else.

## What exists

The private repository was created (P05) and is correctly isolated: no
Git remote, outside the public worktree, receipt recorded. Its
`sources/raw/144000/` directory is **empty**.

There is no frame, no screenshot, no timestamp, no source URL, and no
device context. Nothing to ingest.

## Why this is not worked around

The pack forbids the only shortcuts available, and it is right to:

> Do not replace missing context with guessed metadata.
> Do not infer `144.000 MHz` from an untyped decimal.

`144.000` is, on its own, an **untyped decimal**. At least three
readings are live and none can be eliminated without the source:

1. **`144.000` MHz** — the 2 m amateur band. Plausible *if* the display
   was a radio, and only then.
2. **`144.000` = 144 000** — a locale thousands separator. Much of
   continental Europe writes it this way, and this reading requires no
   radio context at all.
3. **A count, index, address field, or software version** — three
   decimal places is also just a display format.

Reading (2) deserves emphasis because it is the *cheapest* explanation
and needs no exotic assumption. Choosing (1) without evidence would be
selecting the interesting hypothesis over the ordinary one, which is
the failure mode this programme keeps finding in its own work.

## What has been done instead

`r10/cwontology.py` makes the refusal structural rather than a matter of
discipline:

- `refuse_untyped_as_frequency()` raises on any attempt to promote an
  untyped decimal to hertz, and names the locale ambiguity in the error.
- `TypedValue.same_as()` raises `UnitCollision` when values of different
  dimension are compared, so `144` the code word can never be silently
  equated with `144` the frequency.
- The R9 CW integer set is typed `DIMENSIONLESS` / `UNTYPED_DECIMAL`,
  because no unit was ever recorded for it.

This means the blocked state is enforced in code. If someone later tries
to shortcut it, they get an exception rather than a plausible number.

## To unblock

Place the source material in the private root:

```
<private-root>/sources/raw/144000/
```

with, at minimum: the original frame or screenshot, its source URL or
local provenance, a timestamp, and any visible unit, label, or device
context in the surrounding UI.

Then P06 can run: observe what is actually visible, enumerate the
candidate interpretations, and emit a public-safe typed conclusion with
the private material staying private.

## What must not happen at unblock

Even with the frame in hand, a visible "MHz" label establishes what the
*display* said. It does not establish that a transmission occurred, that
anything was received, or that the number carries meaning beyond the
device that rendered it. Those are separate claims needing separate
evidence.
