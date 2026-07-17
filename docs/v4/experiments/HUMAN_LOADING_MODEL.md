# E06 — Human mechanical and capacitive loading

Coverage: **H001–H008, H017**.
Status: **`ETHICS_APPROVAL_REQUIRED`** — blocked, not performed.
Implementation: `apparatus.contact_load_model`.

## Purpose

Quantify **ordinary** hand loading before anyone interprets an operator
effect. A hand on a crystal is a mass, a stiffness, a damper, a
capacitance, and a heat source. All five change the measurement by
plain physics.

## The model

Hertzian contact stiffness added in parallel with the modal stiffness:

    k_c = 2 E* a
    f_loaded / f_unloaded = sqrt(1 + k_c / k_m)

`contact_load_model()` returns the predicted shift, and its own note
says it plainly: **`NOT an operator effect`**.

## Measurement plan

Grip force, contact location and area, hand capacitance, contact
stiffness and damping, grounded/ungrounded, glove/no-glove, dry skin
(wet only where safe and ethical), no-contact proximity, temperature,
handedness, orientation, repeated placements, and an **automated
fixture baseline** that reproduces the grip without a person.

The automated fixture is the control that matters: if a clamp
reproducing the same force and area produces the same shift, the shift
is mechanical.

## Fitting

Equivalent modal load and held-target length correction, fitted **per
person, per mode, per grip, per force, per temperature**.

There is **no universal human constant** here, and the protocol is
designed so that no such constant can be manufactured: the fit is
explicitly person-and-condition specific, and reporting a single "human
loading coefficient" would be an artifact of averaging over people.

## Boundaries

- **Do not interpret ordinary loading shifts as consciousness
  effects.** This campaign exists precisely so E07 cannot do that.
- No biometric or health claim.
- Privacy: contact and physiology data are private by default.

## Ethics gate

`safety_gate` returns `ETHICS_APPROVAL_REQUIRED` for `human_loading`
regardless of engineering safety. A zero-volt hand-on-crystal study is
still a human-subject study.

**Blocked pending IRB/ethics determination — a human-only action that
only Andrew can initiate.** No person has participated.
