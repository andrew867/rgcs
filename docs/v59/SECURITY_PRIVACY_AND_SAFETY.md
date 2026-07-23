# Security, Privacy, and Safety

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** the public/private firewall, the content-claim firewall, and the human-safety refusals.
**Last verified commit:** v5.8.0 baseline (branch `v580-r10-10`).
**Prerequisites:** [PUBLICATION_POLICY](PUBLICATION_POLICY.md).
**Related code / tests / schemas:** [`r10/firewall.py`](../../r10/firewall.py), [`r10/claimfirewall.py`](../../r10/claimfirewall.py), [`r10/handshake.py`](../../r10/handshake.py), [`r10/txline.py`](../../r10/txline.py), [`r10/prospective.py`](../../r10/prospective.py).
**Known limitations:** the publication firewall matches structural categories, not the real private names — name-privacy is an editorial responsibility enforced by review, not solely by the scanner.
**Next review trigger:** any new private-material category, or any hardware/experiment proposal.

---

## Two firewalls, different jobs

- **Publication firewall** ([`r10/firewall.py`](../../r10/firewall.py)) —
  keeps private *material* out of the public tree. It scans the
  **committed** surface (that is what publication means) plus history, for
  private paths, credentials, private-channelling markers, and
  supernatural-authentication phrasing. It must report **zero findings**
  before any release. It deliberately does **not** hardcode the real
  private names (that would itself leak them), so reviewers also grep the
  tree for names, private localities, the private repository's directory
  name, and source digits before publishing.
- **Content-claim firewall** ([`r10/claimfirewall.py`](../../r10/claimfirewall.py))
  — keeps unsupported/dangerous *claims* out of findings. It quarantines
  harmful-biological, medical, human-classification, discrimination, and
  financial claims as `UNSUPPORTED` and refuses to promote them.

## Human-safety refusals (non-negotiable, enforced in code)

- **No human stimulation.** The handshake is software/bench only; there is
  no pineal, brain, subliminal, RF, optical, acoustic, magnetic, or
  electrical human-stimulation path (`r10/handshake.py`).
- **No electrical-safety compromise.** Grounding/EMI mitigation never
  overrides electrical safety; protective earth is never defeated and no
  person is connected to mains earth (`r10/txline.py`).
- **No person classification.** No real person is classified as nonhuman,
  hybrid, genetically altered, or a hidden species; no biology is inferred
  from race, geography, appearance, or group.
- **No financial action.** Investment cues are paper-trading hypotheses
  only, with frozen rules and retained failures; no real-money execution
  and no personalized advice (`r10/prospective.py`).

## Privacy

The private repository has **0 remotes** and lives **outside** the public
worktree (`.gitignore` is not confidentiality). It holds raw Tier-A text,
personal journal and location material, and private interpretations. It is
OneDrive-synchronized on a managed tenant — private from the public
internet, but reachable by tenant administration; treat it accordingly and
keep an independent cold backup (see [DISASTER_RECOVERY](DISASTER_RECOVERY.md)).

`PHYSICAL_VALIDATION_NOT_CLAIMED`
