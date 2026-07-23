# Changelog

All notable changes to RGCS / RSCS. Semantic versioning; the frozen
v2.0.0 baseline is tag `v2.0.0` and `archive/v2.0.0/`.

## [5.8.0] - 2026-07-23

R10.8. A handshake protocol, an EMI survey, a 13 MHz microcrystal model,
atomic-time standards, and the 1604/1644 numeric cues, all from a private
source session. Software verified, physically untested, hardware
deferred. PHYSICAL_VALIDATION_NOT_CLAIMED.

The firewalls come first. The session contained claims that would be
dangerous if acted on -- alleged differential viral effects on hidden
groups, hidden hybrid/genetically-modified populations, medical
predictions, and investment tips. r10/claimfirewall.py preserves each as
a source record and refuses to do more: no person classified as nonhuman/
hybrid/genetic, no biology inferred from group, no pathogen or group-
targeted medical analysis, no medical advice, no accusation, no financial
action. Every quarantined claim is UNSUPPORTED and cannot be promoted.
Human exposure is prohibited throughout: the 925 Hz handshake
(r10/handshake.py) is software-only with no pineal/brain/subliminal/RF/
optical/acoustic/electrical path; grounding never overrides electrical
safety (r10/txline.py); financial cues are paper-trading only
(r10/prospective.py).

Eighteen new r10 modules (261 new tests): session, nolookahead, numcue
(provenance); cue1604 (1604 vs 925*sqrt(3) is APPROXIMATE_NOT_EXACT and
NO_BETTER_THAN_CHANCE, look-elsewhere p=1.0; 1644-1604=40 no meaning);
handshake; microcrystal (13 MHz BVD, refuses free-space wavelength in
quartz); multiframe (exact closures 15.625 ms / 40 ms / 1 s); timebase
(cesium 9192631770 Hz definition, Allan deviation; live data blocked);
emisurvey (blinded ABAB, measured data blocked); txline; envlog; pcemi
(refocus degrades monotonically under EMI); routebind (no retrofit);
memhandshake; extcompare (publication-time discipline); skycorr
(UNIDENTIFIED_CORRELATION_ONLY); prospective (paper-trading only, failures
retained).

The private 2026-07-22 session archive and the quarantined claims are held
in the private repository only; no name, session text, opening-key word,
or CW vector digit enters the public tree.

Not executed: measured EMI spectra, environmental captures, live atomic-
time data, apparatus/bench, prospective outcomes, and real external-corpus
ingestion. Hardware and future-data phases deferred.

CI note: the free-tier GitHub Actions minutes are exhausted; this release
was verified by the full local suite on the exact release commit, not by
hosted CI. No relicensing. MIT unchanged.

Tests: 3340 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [5.7.0] - 2026-07-23

R10.7. Rooted interbody routing, solar/slate calibration roots, a
phase-conjugate return path, and a sky-observation reconstruction
engine. Software verified, physically untested, hardware deferred.
PHYSICAL_VALIDATION_NOT_CLAIMED.

Six new r10 modules, each defaulting to a refusal or a null. The
transcription correction 8300 -> 8.300 and 1876 -> 1.876 is
append-only: the ratio is scale-invariant (2075/469), the residual
against 4096/925 is unchanged (~0.086%), the mapping stays
PhysicalMappingUnresolved, and no unit is invented. Body frames are
built roots-first: two non-parallel directions determine a proper
rotation, a single direction is ROOT_UNDERDETERMINED (a latitude and a
longitude are calibration, not a frame). The rooted route compiler
carries a light-time floor (~1.28 s Earth-Moon) and raises
CausalityViolation on any zero-time transit across distance -- no route
beats the floor, no gateway.

The solar root is the weighted centroid of emission directions, shown
to have power against planted structure; the real catalog is declared
BLOCKED_NO_DATA_SOURCE, not faked (ROOT_CANDIDATE_ONLY). The sky engine
ranks ordinary candidates from kinematics but never identifies without a
catalog match; the default verdict is UNIDENTIFIED_OBSERVATION and it
holds no specific observation. The phase-conjugate return is ordinary
DSP: a reciprocal channel refocuses a phase-conjugated pulse (shown with
power), while a sign flip, a bare time reversal, and a pointwise
conjugate all fail; reciprocity is required, the causal round-trip books
the full light-time delay, and the carrier/key/LO/clock roles are kept
separate.

The Tier-A private sources SRC_JH (Jen Han) and SRC_LS (The L's) carry
forward as distinct records under the single public alias
OMEGA_REGION_SOURCE; the five twelve-digit CW vectors and the twelve-
word Vortex Opening Key are preserved byte-for-byte (integrity
re-verified). A source-provenance trail and a field-observation record,
whose particulars concern a real named individual and a personal
observation, are held privately only (not reproduced publicly),
verbatim, with every post-message item a lead, no independent
verification performed or fabricated, and no claim about any real person.

Not executed: density-layer routing, the apparatus/field-solver phases,
the blinded/prospective harness run (no future vector, slate angle, or
emission interval exists yet to reveal against), the private narrative
archive, real slate-image ingestion, and the real solar catalog.
Hardware deferred.

No relicensing. MIT unchanged.

Tests: 3079 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [5.6.0] - 2026-07-21

R10.6. The Vortex Opening Key pack: base-10 unpacking, the exact phase
frames, and the fading-memory crystal hypothesis. Software verified,
physically untested, hardware deferred. PHYSICAL_VALIDATION_NOT_CLAIMED.

"You have to unpack it from your base 10 system" is treated as a
reversible-view search, not an octal assumption -- octal is not even
well defined here since the vectors contain 8s and 9s. Five reversible
views round-trip the five twelve-digit vectors byte-for-byte, and the
result is NO_DECODER_IDENTIFIED for the structural reason that a
reversible codec relocates information but cannot create it. The shared
16287 prefix is band clustering (p=0.0001), not content
(span-matched null p=0.86). The R9 lesson again.

The phase frames are exact rational arithmetic: 4096 = 2^12,
20.48 = 512/25, periods 244.140625 us and 48.828125 ms, q = 925/4096.
The one honesty hinge is the ratio match -- q^-1 = 4096/925 is close to
8300/1876 but NOT equal, residual 1649/433825 exactly, about 0.086%,
and refuse_exact_ratio_claim() refuses to call it an identity.

The fading-memory crystal is a typed hypothesis, and the firewall is
its point: a decaying trace has the same functional form as ordinary
relaxation, and over 65 stage-times the two curves are point-for-point
identical (max difference 0). Only ordered delayed readout separates a
memory from a passive ringdown, and that needs a bench test that does
not exist. Dispersion strictly costs stages, making the register worse
than a single cell.

The Tier-A sources SRC_JH (Jen Han) and SRC_LS (The L's) are
registered privately with public alias OMEGA_REGION_SOURCE; the
twelve-word Vortex Opening Key and the private delta are preserved
byte-for-byte in the private repository with SHA-256 provenance. No
name, key word, or journal text appears in the public tree.

Not executed: the astronomy/route phases (roots-first Sun/Earth/Moon/
Mars, solar-emission centroid, slate photogrammetry, density-layer
routing), the apparatus phases, and the holdout reveals (no future
vector or measurement exists yet to reveal against). Hardware deferred.

No relicensing. MIT unchanged.

Tests: 3014 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [5.5.0] - 2026-07-21

R10.3. Five typed engines from a lore pack on a nine-density ontology,
a toroidal-Source cosmology, geographic node/gateway sites, and coil
quadrature. Software verified, physically untested, hardware deferred.
PHYSICAL_VALIDATION_NOT_CLAIMED.

The headline is the node look-elsewhere null (r10/nodes.py), the CW
EXPLAINED_BY_CONSTRUCTION result in geography. Fitting a few sites to a
polyhedron gives five solids, a 3-DOF orientation, free vertex
assignment and a chosen tolerance, so a handful of points fits
something almost always. alignment_pvalue() runs the same search on
random sites: 4 random fit to 13.5 deg (null median 13.5, p=0.51), 8
random to 17.2 (p=0.24). It has power -- an exact rotated cube scores
p=0.003 -- so the null is meaningful. Public registry holds public
heritage coordinates only; Antarctica and a Bahamas crystal-sphere
narrative stay LOCATION_UNKNOWN, gateway/stargate pinned UNSUPPORTED.

r10/density.py enforces that source "density" is not mathematical
dimension and not mass density. Only two numbers are supplied (0.5 at
step 6, Source at 9), so steps 1-5 are UNSUPPLIED and 7-8 are
model-derived bands, not point values.

r10/polarity.py: four channels at 0/90/180/270 make a constant-
magnitude rotating field (ripple 3e-16); four spatial poles are not
four charge polarities. Six-phase and dual-three-phase are identical;
alternating triads step rather than rotate.

r10/toroid.py: a torus is ordinary geometry and the zero-point is a
hole. Toroidal EM is not spacetime torsion, and no channel beats light
-- a 0-second latency over 1 AU (floor 499 s) is PHYSICALLY_IMPOSSIBLE.

The private hypothesis delta, source transcripts, and named-site rows
stay private. No real person is named or classified. Operator-specific
site hypotheses are tested privately with the public engine.

Not executed: P01, P06 beyond the causality firewall, P09-P14, P16,
P18-P23. Apparatus phases remain deferred hardware.

No relicensing. MIT unchanged.

Tests: 2948 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [5.4.1] - 2026-07-20

R10.2 corpus import. The private source corpus was supplied and
imported into the private source root: 70 files in, 53 byte-unique
canonical files copied, all 53 SHA-256 hashes matching the manifest,
17 exact duplicates skipped. The import is private (no remote, outside
the public worktree); the public firewall reports zero findings.

Two of the files are public academic papers and produce the public
results. r10/priorart.py records both as CONVENTIONAL_LITERATURE, and
both correct an overestimate. The firefly paper (Silver 2026) puts a
flash at 1e8-1e11 photons, far fewer than the 1e13-1e14 of Coblentz
1912 -- a downward correction of two to six orders, reported as a
range. The tetrahedron paper (Vilcu & Vilcu 2018) is the exact prior
art for the R10.1 inverse estimator, so the Q19 "could not verify"
caveat is now closed; the reproduction stays independent and the
mathematics is unchanged.

r10/chronology.py keeps nine date roles separate and admits only exact
dates into the strict timeline. Populated with public
conventional-science events; of ten, only Pauli's exactly-dated 1930
letter enters the strict timeline. 45 possible-access edges record
opportunity, never influence, and refuse_causal_claim() refuses to
turn precedence into causation.

The 68 private transcripts stay private. No date, quotation, name or
provenance derived from them appears in the public repository, and no
real person is named, characterised, or classified as nonhuman or any
lore species anywhere public. The source-content phases have public
engines but private rows by policy.

No relicensing. MIT unchanged.

Tests: 2867 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [5.4.0] - 2026-07-20

R10.2. Crystal breach as a measurable resonance shift, and typed
separation of the pump branches. Software verified, physically
untested, hardware deferred.

Breach now has an operational definition -- a persistent change in a
crystal's resonant frequency -- which is an improvement because it can
be wrong. The module's job is to make that hard to fake. A quartz
resonator drifts for six ordinary reasons totalling 12.5 ppm typical
and 153 ppm worst case with nothing controlled, falling to 2.0 ppm
once everything controllable is controlled, with aging irreducible.

No exotic verdict exists on any code path, enforced by test: no
verdict may contain BREACH, CONFIRMED, EXOTIC or ANOMAL. The best
available outcome is UNEXPLAINED_BY_THIS_BUDGET, which names what was
not controlled and disclaims itself -- the commonest explanation for a
shift outside a budget is a cause missing from the budget. A claim
with no baseline is refused outright rather than scored, because
aging guarantees the frequency was already drifting.

8 Hz * 2**9 = 4096 Hz exactly; 20.48 = 512/25 and 20.48 * 200 = 4096
exactly. The three low branches differ by 2.4-5%, and whether that
matters is decided from Q rather than taste: inside one linewidth at
Q=10, and 2400 linewidths apart at the Q a quartz crystal actually
has. Nine doublings from 8 reaches 4096 the way nine from 7 reaches
3584 -- a property of the radix, not a privileged frequency.

Most of the pack is BLOCKED: the private corpus contains zero files,
so the chronology, concordance, precedence and contamination phases
cannot run. No metadata was fabricated. No person is classified as
nonhuman or as any lore species, and no personal encounter record or
private journal content appears in this repository.

Not executed: S01-S08, S10-S16, S19-S23.

No relicensing. MIT unchanged.

Tests: 2837 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [5.3.1] - 2026-07-20

R10.1. Hedron coordinate mapping -- roots, topology, address, shells --
and the tetrahedron inverse estimator. Software verified, physically
untested.

The addressing arithmetic is exact: 4096**3 == 8**12 == 2**36, so
twelve levels of one-to-eight refinement is exactly thirty-six bits and
three 12-bit words, reaching 1.5554 km from a 6371.0088 km mean radius.

Three refusals carry the phase. "Twenty regions" does not specify a
topology, because twenty icosahedral faces and twenty dodecahedral
vertices both give twenty and their adjacency graphs differ; both are
implemented and neither assumed. Twelve levels is a RETROSPECTIVE_FIT,
chosen because it reaches the target scale rather than predicted -- and
the tidiness of 8**12 == 2**36 is a property of the radix, not a
discovery about Earth. The 2500-statute-mile shell converts to
4023.36 km exactly, and that exactness belongs to the 1959 definition
of the mile rather than the source, so the honestly reportable figure
is 4000 km.

Q19 reproduces moment-based recovery of a tetrahedron's vertices, with
the constants 20 and 60 derived in Fraction rather than fitted.
Recovery is clean N^(-1/2). The result that matters is the failure
analysis: under non-uniform density the error is a bias, not noise --
25.1%, 25.6%, 25.5% at N = 1e4, 1e5, 1e6, so more data makes the wrong
answer more precise. Three of six broken assumptions produce confident
wrong answers with healthy diagnostics.

Two constructive non-identifiability results. Second moments never
identify a tetrahedron: a similarity transform preserves mean,
covariance and volume while changing shape. Shell-confined observations
are non-identifiable outright: two tetrahedra with volume ratio 1.42
share an insphere and their shell samples agree to 1e-9, an
8-parameter equivalence class. Impossibility, not difficulty.

Q02 closes R10-D-004, the inverse of R8-D-006. consciousness_lane
shipped in the wheel while outside SOURCE_ROOTS, so changing it could
not invalidate a frozen dist. Per the operator's standing decision a
publicly shipped package must be hashed; both directions are now
asserted and the two lists must be exactly equal.

Q04 remains BLOCKED. No 144.000 source frame exists and the pack
forbids fabricating metadata for it.

Not executed: Q06, Q07, Q09-Q12, Q16, Q18, Q20-Q23.

No relicensing. MIT unchanged.

Tests: 2808 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [5.3.0] - 2026-07-19

R10. CW ontology and exact arithmetic with a proper null hierarchy, a
typed energy ledger, Unruh/Rindler scale calculators, the
private/public publication firewall, and artifact-level install
parity. Software verified, physically untested.

The headline is a p-value that moves from 1e-5 to 1.0 depending on
which null you pick. The offered CW relations -- 1516 = 1496 + 20 and
2160 = 1516 + 644 -- are exactly true. Against five integers drawn
uniformly they look remarkable. Against sets built as the partial-sum
closure of three generators they are certain, and the observed set IS
such a closure, exactly: sorted(observed) equals sorted({a, b, c, a+b,
a+b+c}) for a=1496, b=20, c=644. So the relations restate the
construction rather than revealing content. Verdict
EXPLAINED_BY_CONSTRUCTION. Three relations are also only two
independent facts, since the third follows by substitution.

That is not a claim the numbers are meaningless. The arithmetic is
exactly true and stays true; it simply carries no evidential weight
about origin, because any three integers closed under partial sums
produce it.

CW is separated into three senses -- code word, continuous wave,
carrier wave -- of which only the last has a frequency. TypedValue
raises UnitCollision across dimensions, so 144 the index can never be
silently equated with 144 Hz. The R9 CW integers stay
DIMENSIONLESS/UNTYPED_DECIMAL because no unit was ever recorded.

Energy raises on addition across heat, work, reservoir, stored and
dissipation, so "there is energy in the reservoir" cannot be added to
"energy available as work"; available_work_bound() requires a sink
temperature, so an isothermal reservoir yields exactly 0 J whether it
holds 1 J or 1e24 J.

Unruh: 4.055e-21 K per m/s^2, and a conclusion we expected and did not
get. Bulk acceleration falls short by ~2.5e14, but a single electron
at a record laser focus reaches T_Unruh ~ 6.5e5 K, computed rather
than asserted. That is not absurd, so the verdict is split rather than
overstated, and the energy-source refusal is carried by the budget --
the driving field exceeds the induced bath by 2.7e10 times.

The publication firewall found 30 absolute-path disclosures already
public. Twelve in live docs are repaired; eighteen inside the
checksummed v2.0.0 archive are DECLARED with a severity assessment,
because editing them would invalidate the provenance the archive
exists to provide. Git history was not rewritten -- that breaks every
clone and tag to remove a low-severity disclosure that is already
public. Severity LOW: sandbox build paths and a username already in
the package metadata. No credential, personal record or source
material.

P20 builds the real wheel and sdist, reads what is inside them, and
imports from a virtualenv that cannot see the repository. All
seventeen packages present in both artifacts, all importing from the
installed copy.

R10-D-001: r10 was in neither SOURCE_ROOTS nor the packaging include
list -- R8-D-006 and R9-D-004 starting over one generation later. The
guards caught it this time instead of a release doing so.

R10-D-002, recorded not fixed: tests/v4 rewrites three tracked JSON
files as a side effect, so a test run dirties the tree and "clean
tree" gates become unreliable.

P06 is BLOCKED and stays blocked. No source frame exists, so 144.000
remains an untyped decimal; the locale reading 144.000 = 144000 is the
cheapest explanation and cannot be excluded. The refusal is enforced
in code.

No relicensing. MIT unchanged.

Tests: 2710 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [5.2.1] - 2026-07-19

R9-D-020. tests/v52/test_r9_packaging.py imported setuptools at module
level. setuptools is a build-system requirement, not a runtime or test
one, and it is absent from CI's portable job, so the module failed to
collect on ubuntu, macos and windows while passing locally where the
venv happens to have it. v5.2.0's CI is red for this reason.

A packaging guard that cannot run in CI is not a guard -- and this is
the same shape as the defect it was written to catch: something that
works from a developer's tree and not from a clean install. Declared
in the dev extra, and imported via importorskip so a missing build
tool skips the file rather than erroring collection.

The v5.2.0 tag is immutable and stays as cut. All 10 CI jobs green at
this release.

Tests: 2564 passing from a clean clone (1 archived-environment byte
test deselected by policy D-V3-04).

## [5.2.0] - 2026-07-19

R9. Hidden neutral carrier feasibility, the omitted-antineutrino
ledger, segment-first CW decoding, the octave relation and the 1<->8
bridge, and the vortex grammar. Software verified, physically
untested.

Prior-art review: five for five established. Nothing in R9 is novel,
and the modules say so. The vortex identification is standard number
theory, the ~202-octave figure is a two-constant division published
earlier, the beta-decay argument was settled between 1914 and 1934,
the bench-neutrino infeasibility conclusion is decades old, and the
preregistration methodology is textbook. The honest framing is
replication and correct exposition.

Headline results. A 100 g quartz crystal sees ~0.06 solar-neutrino
interactions per year -- one every sixteen years -- against ~2e7
cosmic muons, but the binding obstacle is prior to the rate: a quartz
resonator has no channel that can register a single sub-keV recoil.
NUCLEUS runs a 10 g target, so the barrier is readout, not mass. The
CW vectors yield no recoverable content in any of three framings,
while their clustering is real and is reported separately. The
antineutrino cannot be omitted: a two-body decay predicts a
monoenergetic electron and the measured spectrum is continuous. The
vortex cycle is the multiplicative order of 2 mod 9 and is
base-dependent -- base 12 excludes nothing at all.

Adversarial review found nineteen defects behind a green suite, and
three tests that could not fail. The CW bit stage was a constant
function returning 0 for every possible input, so the published claim
that three framings "could have disagreed and did not" was false when
written; three more registered tests were gated behind a hardcoded
literal or bounded below the significance threshold. Of eight
advertised tests, five can fire, and the verdict now says five.
Physics corrections: cross-sections were all multiplied by nucleon
count despite having three different denominators (the module
reported inverse beta decay in quartz, which has no free protons); the
solar rate used a 1 MeV cross-section against a 0.267 MeV spectrum and
was 10x high, now anchored to Borexino; the Super-K validation
asserted raw S/B > 1 and was wrong in principle, since Super-K runs at
~1e-4 and works by reconstruction; "four independent conservation
laws" is cut to the honest two.

Packaging: pip install of v4.9.0, v5.0.0 and v5.1.0 shipped none of
r6, r7 or r8 -- the headline research packages of those releases. The
include list stopped at r4 and a clone hid it, since pythonpath makes
the tree importable regardless. The R8-D-006 coverage guard could not
see it because it keyed on __init__.py and those were namespace
packages. Both fixed and pinned by test.

No relicensing. MIT unchanged.

Tests: 2564 passing (1 archived-environment byte test deselected by
policy D-V3-04).

## [5.1.0] — 2026-07-19

Open commons release. Software verified, physically untested.

R8.1 closeout: DDS closure theorem with the continuous/sampled
discrepancy, null-calibration harness with three worked failures,
relational coordinate technical report, measurement lanes, knowledge
audit, disclosure timeline, and the commons layer.

Prior-art reviews repositioned all three manuscripts: the DDS closure
formula is published (Nicholas & Samueli 1987; Hwang 2017; Fujifilm
US12422666B2), the null-calibration principle is the severity
requirement, and six of seven coordinate components are textbook.
None of those novelty claims is retained.

Corrections: the Pound-Rebka "validation" compared a formula against
itself and is withdrawn; frame-chain quadrature contradicted the
covariance field; a non-positive-semidefinite correlation returned
0.0 m, reporting perfect knowledge, and now refuses; MDEV and TDEV
implemented after being named but absent; "frozen" replaced with
INTERNAL_ANALYSIS_FREEZE.

No relicensing. MIT unchanged. v3.0.0-v4.8.1 were public under MIT
2026-07-15 to 2026-07-18; R6/R7/R8.1 first published here.

Tests: 2420 passing (1 archived-environment byte test deselected by
policy D-V3-04); adversarial audit 19/19.

## [5.0.0] — 2026-07-18

R7: root reference, CW vector decoder, differential clock link,
crystal alignment, directional field geometry, falsifiable metric
challenge, and the open-legacy decision. Software implemented,
physically untested. Publication path PRIVATE_RC — nothing new
published.

**R7 was asked for a falsifiable metric prediction and produced one:
nothing this apparatus can do is detectable.** Every configuration is
REFUSED_BY_ARITHMETIC, including a 2 MJ bound far beyond anything
buildable here, which still sits 17.8 decades below the best optical
clock. Raising a clock by one millimetre beats the entire apparatus
by 6.6e17. The result is independent of whether the crystal, the
geometry or the source corpus are right about anything.

**The CW vectors carry zero informative bits.** All five 38-bit
strings share header 10 and first field 1516, matching the 4096-state
architecture — but their interval's endpoints share their top 15
bits, and header plus first field occupy the top 14. Random integers
from the same interval reproduce the structure in 20000 of 20000
draws (p = 1.000). The decoder is frozen by digest so a prospective
test remains possible.

**The clock-link ceiling is a floor, not a patience problem.** OCXOs
flicker-floor at 1.4e-13, three decades above a 1 m height shift, so
the answer is never rather than longer. Sweeping links showed the
bottleneck moves: consumer quartz is oscillator-limited, the best
clocks are link-limited, and an optical pair on coax cannot resolve a
metre while the same pair on fibre resolves it in 1.7 s.

Other results: geodetic and geocentric verticals differ by 0.1924
degrees, about 693x an autocollimator's resolution, so "perpendicular
to the surface" and "toward the centre" are different claims; the
c-axis cannot be read from morphology because Dauphine twinning is
optically invisible; a passive crystal cannot self-oscillate; and the
45-degree field pair gives 2cos(theta) for any theta, with 30 degrees
giving a larger sum than 45.

Workbook: 39 sheets. Tests: 2161 passing (1 archived-environment byte
test deselected by policy D-V3-04); adversarial audit 19/19.

## [4.9.0] — 2026-07-18

R6: dynamic helicity, metric-indexed witness memory, recursive
barycentric mailbox routing, information-carrier transduction, and a
planetary polyhedral grid audit. Software implemented, physically
untested.

**The central correction.** A decaying memory is not a spacetime
sensor. Payload relaxation has twelve ordinary causes and a common
environmental cause can move payload decay and clock phase together,
so even a correlation does not license the inference. Enforced in
code: `infer_proper_time_from_payload()` always raises, and still
raises when all twelve causes are characterized.

**Results that went against the source corpus.**

- The alternating drive (copper 1-0-1-0-1-0 / silver 0-1-0-1-0-1) is
  *not* purely differential under the unipolar mapping the source
  describes. Every active slot carries an equal common-mode
  component, producing a net axial field at half amplitude. Only a
  bipolar mapping is purely differential.
- The three source frequencies (1496, 644, 587 Hz) are not
  significant against a granularity-matched null, p = 0.662. For any
  laboratory-scale specimen all three fall below the fundamental
  entirely. Tuning to a 1.9 m bar gives p = 0.531; the result did not
  move.
- Sovereign navigation is unsupported. A local clock-rate Jacobian is
  rank 1 against three position unknowns and is constant over an
  equipotential surface; separately, zero of seven signal-denied
  methods are infrastructure-free.
- A caesium pair cannot resolve the 1.09e-16 shift from 1 m of
  height. Optical clocks can. The platform decides, not the
  architecture.
- The planetary audit ships no geophysical data and always reports
  NO_REAL_DATA.

**Source corrections.** The SI second is the caesium-133 hyperfine
*transition*, not a decay. Photons carry no charge. A field "in
constant movement" does not eliminate a preferred angle.

**Defects found and fixed.** `tests/v49` was outside `testpaths`, so
every R6 test would have passed locally and never run in CI.
`ComparisonResult.consistent` reported agreement from comparisons
that had not tested anything. The navigation rank routine used an
absolute tolerance and reported that a clock carries no position
information at all — overstating our own refutation. The grid
detector was blind at every injection strength, from a fake rotation
plus an injection that cancelled in the score; replaced with real
Wigner D-matrices and true group projectors, which independently
reproduce the textbook invariant degrees. A Wigner phase error passed
unitarity, idempotency and every dimension check because it was a
diagonal similarity — only closed forms could see it.

Workbook: 33 sheets (five new R6 sheets). Protocol maturity is
EXPERIMENTAL_SCHEMA; bench readiness is 5 of 10 gates with
`ready_for_bench: False`.

Branch protection is no longer enforceable (private repository on a
plan without protected branches); recorded as a documented deviation
rather than claimed.

Tests: 1840 passing (1 archived-environment byte test deselected by
policy D-V3-04); adversarial audit 19/19.

## [4.8.1] — 2026-07-18

Workbook column-loss fix. No science changed.

_write_table built headers from rows[0].keys(), so any field unique to
a later record in the same table was silently dropped from the sheet.
The canonical store was always correct; the spreadsheet was not.
Measured impact: 52 columns lost across ten heterogeneous sheets,
including the R4 negative-control gate and every beats_any_baseline
verdict (the reader could not see that the codec fails on random
data), PMWR travel-claim reasons, and R3 root statuses. Pre-existing
since v4.5; every release from v4.6 shipped degraded sheets.

Headers are now the ordered union of all row keys, with regression
tests asserting no sheet drops a canonical field and that the
negative-control gate is readable from the workbook.

Tests: 1219 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.8.0] — 2026-07-18

R4: Tetrahedral Spin-Addressed Multiresolution Codec, Quaternary
Memory, and Physical Spin-Memory Qualification (v4.8 R4 pack, 64
agents). **SOFTWARE_VERIFIED, PHYSICAL_SPIN_UNTESTED.** All prior tags
untouched.

New `r4/` package: exact radix bridge 4096 = 8^4 = 4^6 = 2^12 verified
exhaustively over all 4096 keys in three radices -- and refused as
compression, with a RAW_QUATERNARY baseline costing exactly what flat
binary costs. Quaternary symbols require a declared basis before any
direction naming; the hierarchical address is stored DIGITAL_EXACT and
storing it in a physical spin is refused (drift would corrupt the
index). Tetrahedral codebook with exact geometry; the SIC outcome
object REFUSES to be storage (four directions at -1/3 overlap span a
2-dimensional space). GF(4) integrity fixture that states its own
scope (corrects a known erasure, not an unknown error).

Multiresolution codec with Lagrangian split/prune, train-split-only
codebook, versioned container, entropy model whose transmission cost is
counted, lossless/progressive/random-access modes, and FULL bit
accounting. Two methodological defects found and fixed while running
it: the rate-distortion curve swept only lambda (pinning fidelity at
the codebook bottleneck) and the HAL ablation pinned lambda so the tree
never split. Honest outcome after fixing both: the codec beats
quantizer baselines on piecewise-constant data, LOSES to zlib on that
same data, and offers nothing on smooth/sparse/ramp payloads; the
random-data negative control correctly shows no gain.

Physical lane: four-state platform registry (SiC spin-3/2 recorded with
its |m_s|-pair readout limitation; NV+15N; classical four-domain
separated from the spin claim; spin-1/2 tetrahedral REFUSED as memory;
quartz BLOCKED with all ten gates open), four-level spin digital twin
whose write compiler refuses Delta m_s != +-1 single pulses and whose
readout returns an explicit ERASURE without sign resolution, finite
retention/endurance, voxel crosstalk bounding addressing density, and a
staged bench whose honest stop is BLOCKED_NO_APPARATUS.

Release process: tools/r4_release_gate.py installs the no-post-tag-sync
gate (R04/R65) -- v4.8.0 is the first release whose tag already
contains every release-owned artifact. Workbook: 28 sheets (2 new R4).

Tests: 1217 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.7.1] — 2026-07-18

R3: Root-Space Resolver, Anisotropic Phase Lens, Optical Spin, HAL
Memory, Nested Tetrahedral Atlas (v4.7.x R3 pack, 95 agents).
**SOFTWARE_VERIFIED, PHYSICAL_UNTESTED.** All prior tags untouched.

The R3 correction: a root is NOT "the first zero of the phase
residual" -- wrap(phi)=0 admits integer-cycle aliases (4097 candidates
per second at 4096 Hz). New `r3/` package: six typed root classes, six
forbidden collapses as executable refusals, dual-lattice alias
thinning, gauge orbits with mandatory representative rules, emission-
coordinate localization from >=4 reference worldlines (relational by
construction), and a root-lock certificate whose best status is
ROOT_LOCK_BOUNDED with ABSOLUTE_VACUUM_ROOT_UNSUPPORTED and
NONLOCAL_REFERENCE_FRAME_UNSUPPORTED standing. Plus: anisotropic phase
lens (adjoint-verified Tikhonov inversion, refusal of unregularized
solves), exact 8^d tetrahedral addressing with five declared K
semantics and hard destination certificates, spin/torsion typing that
never merges categories (EC torsion from a fully polarized solid
~6e-25 1/m; a 1e-9 metric wish costs 6.7e17 kg -- REFUSED_BY_
ARITHMETIC), optical spin with SAM/OAM separation and dose ceilings,
synthetic-only HAL memory with a consent gate, and the nested atlas
whose null-rotation campaign rejects grid orientations that cannot
beat seeded random rotations. L'ou source log preserved verbatim,
sha256-pinned. Gate Zero re-verified v4.7.0 remotely; enforce_admins
on main is now ON (operator action) closing the R2 governance gap.
Workbook: 26 sheets (2 new R3).

Tests: 1153 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.7.0] — 2026-07-18

Phase Memory, Worldline-Indexed Multipath Recovery, Causal Channel
Reconstruction, and Phryll Translation Hypothesis (v4.7 pack, agents
A00-A83). **SOFTWARE_VERIFIED, PHYSICAL_UNTESTED**: no apparatus was
built, no data collected, and no Phryll-detected state exists in this
release by construction. All prior tags untouched.

New `pmwr/` package: typed phase authority with a nine-state
synchronization machine (cycle count only while PHASE_LOCKED, no force
flag); finite-Q phase-memory horizon with perfect-memory refusal; six
separated signal stages (propagation always loses the cycle count);
worldline/path schemas on the validated weak-field fixtures; the
arrival/causal-order firewall (reordering is delay geometry; the audit
cannot emit "causal reversal"); closure-window alias analysis (exact
closure IS a delay alias -- 4097 indistinguishable delays per second
for the binary family) with dual coprime lattices extending the
unambiguous range x4096; least-squares recovery behind an
identifiability gate that REFUSES underdetermined and ill-conditioned
cases; the crystal-translation lane (geometry schema with mandatory
reversed-orientation control, excitation registry where
self-oscillation needs a loop AND an energy source, energy ledger that
calls over-unity ACCOUNTING_ERROR); the pyramid-ratio audit (2a/h at
51.843 deg = 1.5714157792, ~5e-4 from pi/2, GEOMETRY_IDENTITY, the
mechanism reading refused); and the guarded Phryll ladder (a residual
requires all eleven ordinary channels bounded plus a sham-drive
control; the source's own power-not-engaged episode is the preserved
warning).

Gate Zero: v4.6 independently re-verified by object ID and remote
download before branching; only CI-verified commits reached main.
enforce_admins remains OFF pending operator action (documented).

Workbench gains an Evidence-ledger panel (14 panels); workbook gains
three PMWR sheets (24 total). Operator note and evaluation contract
hash-pinned before estimator work.

Tests: 1113 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.6.0] — 2026-07-18

Crystalline Spacetime Coordinate Program (v4.6 pack, agents A00-A36).
**SOFTWARE_VERIFIED, PHYSICAL_UNTESTED**: no apparatus was built, no
data collected, and no physical hypothesis is supported. All prior tags
untouched.

New `cspc/` package: exact unit-aware frequency mathematics (floats
refused; sig-figs tracked separately from exactness), a frozen
hash-pinned simplicity metric with matched nulls and Holm/BH
correction, the 64-tetrahedron lane (four non-isomorphic families,
relabeling-invariant spectra, degree-matched nulls), DDS/NCO and
phase-closure compilation, preregistered experiment definitions, a
relativistic clock model validated against Pound-Rebka and GPS, a
metric/energy audit, and structural RF safety with no override flag.

Corrections to the source material: 2.45 GHz is not a unique resonance
of water (Debye loss peak ~19.2 GHz; 2.45 GHz carries ~25% of peak
loss); "0.0356521923..." retains HERTZ and is a 36-bit DDS resolution
step; 8^11 is 33 octaves not 11; the "64-tetrahedron grid" phrase is
underdetermined and stays so.

Headline results are null or cautionary: the simplicity metric measures
human number-choosing convention, not nature, and the programme's own
candidates are flagged CIRCULAR; 4096 = 64^2 holds for any 64 objects;
the ideal phase closure collapses ~175,000x on a decimal reference
clock and is only restored by choosing a binary oscillator; a
laboratory energy budget implies a Schwarzschild radius 23 orders of
magnitude below a proton. All five travel-adjacent claims are
UNSUPPORTED.

Four new Master Evidence Workbook sheets read the canonical store and
show exact vs physically-supported precision side by side.

Five defects found by running the analysis honestly (CSPC-D-001..005),
including a null model that made every corpus -- including the negative
control -- appear significant; fixing it inverted the headline result.

Tests: 1062 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.5.2] — 2026-07-17

Windows Workbench clean-rebuild patch. The v4.5.0 and v4.5.1 release
binaries were invalid: every build after the first freeze used
`--skip-freeze`, which re-zipped a **stale** PyInstaller executable. The
current source handled `--first-run` correctly, but the shipped exe was
built before that code existed, so the installer's post-install launch
(`RGCSWorkbench.exe --first-run`) created a workspace literally named
`--first-run`.

Fixes:

- **Clean rebuild from current source** — `build/` and `dist/` deleted,
  full freeze (no `--skip-freeze`).
- **Build provenance embedded in the exe** (`rgcs_desktop/build_meta.py`,
  `_build_stamp.json` bundled): version, git commit, and a source hash
  over every packaged `.py`. New `--build-info` prints it.
- **`--skip-freeze` now refuses a stale/mismatched `dist/`** — the build
  aborts if the frozen tree's source hash differs from the working tree,
  so the failure that shipped twice cannot recur.
- **`--first-run` can never be a workspace path** — startup selection
  moved to a pure, tested `plan_startup()`; `--first-run` (and any
  `--flag`) maps to the wizard, never to creating/opening a directory.
- **Source + packaged regression tests** — `plan_startup` unit tests,
  and frozen-binary tests that run the installer's exact command and
  assert no `--first-run` directory is ever created, plus build-info
  hash match, 13-panel smoke, wizard/demo/workbook self-test.
- Installer's exact post-install launch, wizard creation, demo seed,
  workbook, all 13 panels, restart, upgrade, and uninstall verified on
  this machine (still not a clean VM; clean-machine verdict not claimed;
  installer still unsigned).

Tests: 945 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.5.1] — 2026-07-17

Windows Workbench packaging patch on 4.5.0. No source logic or
scientific claim changed; all prior tags untouched.

The v4.5.0 portable build crashed on launch: the model-browser panel
reads `docs/model_registry.yaml` (and the provenance graph reads
`references/` and `experiments/schemas/`), none of which the
PyInstaller spec bundled, so the frozen app raised `FileNotFoundError`
while constructing its panels. `--doctor` returns before any panel is
built, so the build check never saw it.

Fixed: `packaging/RGCSWorkbench.spec` now bundles every runtime data
tree the desktop reads (`docs/model_registry.yaml`, `references/`,
`experiments/schemas/` alongside the two `registry/` trees), guarded by
a new regression test; `tools/v45_build_windows.py` verifies the frozen
exe with `--smoke-check` (constructs all 13 panels + a real background
job), not just `--doctor`. New deliverable: a compiled per-user
(unsigned) Inno Setup installer EXE; the silent install → launch →
uninstall cycle was verified on a developer machine (not a clean VM —
the clean-machine verdict is still not claimed).

Tests: 939 passing (1 archived-environment byte test deselected by
policy D-V3-04).

## [4.5.0] — 2026-07-17

Windows Workbench, portable package, and Master Evidence Workbook
(v4.5 pack). **SOFTWARE_GREEN, PHYSICAL_UNTESTED** unchanged: this is
a packaging and interoperability release; no physical result is
validated and no evidence class was promoted.

**Canonical export model** (`rgcs_workbench/`): a typed `Record` /
`CanonicalStore` layer pulls live data from every v4.x lane —
frequency keys, harmonic relations, specimens, mode estimates, timing
recipes, hypotheses, the Eye numerical ladder, the resonator
platform campaign, hardware BOM, experiment queue, corrections,
source registry, and PUBLIC_SAFE lore. Each row carries an evidence
class from the eight-rung ladder and a privacy class; the store is
the single source of truth and the workbook is generated one-way from
it (never the reverse).

**Master Evidence Workbook**: `python -m rgcs_workbench.workbook`
(or the app's `--export-workbook`) writes a 17-sheet formula-visible
xlsx — Dashboard, Frequency Keys, Harmonic Relations, Specimens, Mode
Estimates, Timing Recipes, Hypotheses, Evidence Ledger, Eye Results,
Resonator Platform, Hardware BOM, Experiment Queue, Corrections,
Source Registry, Lore Registry, Installer Metadata, Workbook Guide.
Derived cells stay live formulas (mode-estimate percentage errors,
dashboard sums); evidence classes are colour-coded; a public export
provably contains no PRIVATE row content. Excel is never required to
run the app — the workbook is interoperability only.

**Windows packaging** (`packaging/`): a PyInstaller onedir build
frozen from `RGCSWorkbench.spec` produces `RGCSWorkbench.exe`, zipped
into a portable ZIP that runs with no install, no admin, no
telemetry, and no auto-start; per-user data lives in
`Documents\RGCS Workspace`. Headless `--doctor` and `--smoke-check`
verify the frozen build. The Inno Setup installer script
(`RGCS_Workbench.iss`, per-user, `PrivilegesRequired=lowest`) is
shipped in-tree; the compiled Setup EXE and clean-machine VM
verification are **honestly gated** — Inno Setup is not present in the
build environment and no clean VM was available, so this release ships
the verified portable ZIP and workbook and does NOT claim a
signed installer or clean-machine proof.

Tests: 938 passing (1 archived-environment byte test deselected by
policy D-V3-04), including 22 new workbench, workbook, and packaging tests.

## [4.4.0] — 2026-07-17

Frequency-Key Harmonic Excitation and ESP32-CYD Instrument (v4.4
pack, agents A00–A26). All prior tags untouched. **SOFTWARE_GREEN,
PHYSICAL_UNTESTED**: the specimen is an eBay listing, no board has
been powered, and all six preregistered hypotheses are UNTESTED.

**Exact relation engine** (`fkey_instrument/`): all frequency
arithmetic in `fractions.Fraction` (floats refused at the parse
boundary); every relation carries exactly one primary mechanism
class from the pack's taxonomy. The frozen seed corpus classifies as
required: 4096×5 is a low-order HARMONIC; 8×2560, 20.48×1000 and
40.96×500 are exact but PHASE_CLOSURE_ONLY; the mixed sums
(1496+32×587, order 33; the four-tone sum, order 21) are
ARITHMETIC_COINCIDENCE — not emitted frequencies in a linear system.
The A06 engine proves (analytically AND by independent FFT) that an
ideal sine has no fifth harmonic while a 50% square carries one at
exactly 1/5; duty error resurrects even harmonics.

**Pre-arrival specimen model**: immutable revision 1 from seller
claims (77.8 mm → quarter-wave 20278.959 Hz, half-wave 40557.918 Hz);
correction record FK-CORR-001 verifies the two target percentage
errors are ONE number (both ∝ v/L); the model licenses a search band,
never a magic frequency; arrival measurements create revision 2 with
mandatory instrument provenance.

**Mechanism-first optimizer**: expected amplitude comes from the
spectrum engine through a 2-DOF plant (transducer-vs-crystal
discrimination by response-to-perturbation), so sine-"harmonics" and
arithmetic coincidences score zero by construction; Pareto dominance
runs within hypotheses (a sham is not a substitute for a resonance
tone); campaigns compile randomized, blinded, sham-included, with the
no-post-hoc-frequency rule declared.

**Fail-off instrument twin + firmware**: strict JSON contracts
(missing amplitude REFUSED, never defaulted; invalid JSON faults at
load, before any output authority); safety FSM with fresh single-use
expiring arm leases, no auto-arm, 14 latching fault causes,
reset-lands-output-off; hash-chained SYNTHETIC logs; CYD board
profiles are candidates (verified=False) with boot-strap/input-only/
peripheral pin-conflict detection and UNKNOWN ⇒ OUTPUT_DISABLED;
LEDC/RMT/DDS backends report requested vs calculated-realized
frequency as exact rationals with measured=None until a measurement
exists. Firmware source tree provided
(`firmware/fkey_cyd/`, PlatformIO) mirroring the tested twin —
NOT compiled here (no toolchain, no hardware).

**Six demos** run entirely in simulator (relation census, waveform
distinction, nominal sweep + bootstrap Q, optimizer + 4 validated
recipes, full device cycle with intact log chain, fault refusal),
every artifact SYNTHETIC-labelled. **46 FK coverage requirements**
verified mechanically with bidirectional orphan checks; A24 red-team
attacks are executable regression tests.

Tests: 916 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [4.3.0] — 2026-07-17

Post-v4.2 Emergent Resonator and Structured-Wave Expansion. All prior
tags untouched. Coverage: 280 fixed IDs + 8 orphans = 288, verified
mechanically (symbols import, tests exist, docs exist, status legal
for depth) from the programme's first commit.

**Closed-loop resonator platform** (`resonator_platform/`, 14
modules): lifecycle state machine without a force flag; append-only
hash-chained ledger; predicted/measured/fitted/accepted frequency
separation enforced in constructors; digital twin with fabrication
variation and execution noise; Lorentzian DAQ fits that report
non-identifiability; conservative trim planner (overshoot is
unrecoverable, so the selector refuses rather than burns); approval
tokens + machine-capability registry requiring fume-extraction and
interlock evidence (no machine registered → the physical path
refuses, truthfully); reversible-trial tuning with exact rollback;
HMAC certificates that refuse unfitted or out-of-band acceptance and
print the claims they do NOT make; a complete synthetic
design-to-certificate campaign (2 trim iterations, ACCEPTED in band,
32-event intact ledger, deterministic per seed). Additive process
cards (printed silica enforced ≠ quartz), MEMS twin with
INTERFACE_ONLY foundry handoff, oscillator models with the
resonator≠oscillator boundary in code, neutron-paper composite-mode
mathematics with computationally verified parity selection and the
angular-Nyquist alias band reported.

**Eye: the census corrected the programme's own headline.** The
unbiased full-domain cluster census (Y03) shows the v4.1
(z=102.24 mm) and v4.2.1 (z=99.78 mm) coordinates are two
resolution-dependent estimates of ONE male-apex feature — with a
symmetric family (female-apex twin z≈4 mm, mid-shaft pair z≈58 mm)
invisible to every earlier nearest-to-candidate analysis. Station
comparison stands (5.1–6.7 mm vs ~1.8 mm halfwidth); eigenspace
tracked <2.7° (no mode switch). Claim card v3 → v4 with the
correction trail appended. Calibrated resource model with range
predictions and preflight refusal; the 150× estimator failure is
preserved as its calibration history.

**Five 2026 papers ingested** with hashes, claim cards, equation
provenance, and per-source transfer firewalls that raise on quartz
claims; five reference models with tested analytic limits (a sign
error in the triangular-transport removal rate was caught by its own
redistribution test during development). Mechanism-discrimination
tree defaults to INCONCLUSIVE; the model playground is structurally
unable to write evidence.

**Policy lanes**: broadcast heritage, product tiers (targeted ≠
measured), Hydrogenuine open-commons/assurance boundary, private-lore
mechanism (content local-only, never tracked), intuition pipeline
with retrospective baseline labelled non-evidence, versioned claim
cards.

Nothing physical exists: no board, fixture, laser, instrument,
printer, or cleanroom. Every physical path is capability-gated and
currently refuses.

Tests: 857 passing (1 archived-environment byte test deselected by
policy D-V3-04).

## [4.2.1] — 2026-07-17

Completeness audit of the v4.2 expansion. The `v4.2.0` tag stays
immutable at `d253c2f` and is recorded as a CI-green tagged expansion
candidate whose release publication was blocked before completion; it
is superseded, not rewritten. All prior tags untouched.

**Why this release exists.** v4.2.0 reported "coverage ledger 248/248,
all gates green". That was true and meaningless at the same time: the
gate verified that every ID had an owner *string* and an artifact
*string*, both satisfiable with any nonempty text. Seven of the QA
prompt's attacks succeeded against it.

**Found and fixed (11 defects, no open P0/P1):**

- **V4X-D-006 (P0)** C05 metrology was a registry of seller values
  wearing an implemented workstream's status; no pipeline existed. New
  `rscs2_core/metrology.py`: seller values cannot become measurements
  (constructor-enforced), XRD returns `INTERFACE_ONLY` rather than
  inferring axes from facets, malformed scans are refused not repaired.
- **V4X-D-007 (P0)** consciousness-lane status laundering: 18 entries
  claimed `REDUCED_ORDER_VALIDATED`, only 6 had models. Implemented 5
  real models (ring attractor with saturation, phase-amplitude coupling
  with surrogates, quantum order effects + parameter-free QQ equality +
  classical comparator, subjective time); **downgraded 7** with the
  reason recorded per entry. `model_symbol` now verified by test.
- **V4X-D-012 (P1)** G42 verified strings → gates **G42A–G42G** verify
  paths exist, symbols import, sources resolve, tests and docs exist,
  status is legal for the delivered depth, and blocked rows name their
  blocker and next action. 268 rows, all pass.
- **V4X-D-010 (P1)** the P02 orphan sweep had never run. 20 orphans
  registered with mandatory dispositions; coverage 248 → **268**.
- **V4X-D-009 (P1)** 47 required standalone documents missing (1/38
  agents complete) → ~50 documents written.
- **V4X-D-005 (P1)** the cusp metric summed over path *samples*; a log
  spiral crowds θ-uniform samples at its centre, so a **uniform** field
  scored 0.695 concentration. Arc-length weighting fixed it, validated
  against an independent analytic target (uniform → 0.0928 = the
  arc-length fraction). Concentrated/uniform = **10.576×**, finite. The
  audit's premise (that the >5× test was changed post-hoc) was wrong —
  git history shows the threshold never moved.
- **V4X-D-013 (P1)** nine frequency entries carried `CORE_VALIDATED` on
  arithmetic identities; `F002: 20.480 kHz = 4096*5` read as a
  validated resonance. Automatic **ARITHMETIC ONLY** note, enforced.
- **V4X-D-008 (P1)** C01 lacked the mandatory strong-coupling
  criterion. Added, verified against the complex eigenvalues.
- **V4X-D-011 (P1)** "sub-millimetre refinement" ran at 8.0/5.5/4.5 mm.
  Renamed honestly; a genuinely finer ladder was run.
- **V4X-D-004 (P1)** release notes said 681 tests, the report said 682.
  Counts now derive from a real pytest run into
  `docs/v4/RELEASE_METADATA.json` and are guard-verified across docs.
- **V4X-D-002 (P1)** the asset builder hardcoded its version.

Also: BVD gains OSL calibration, multi-branch detection, identifiability
reporting and SPICE export; the apparatus twin gains coil
resistance/field/thermal/contact/transducer/cable models with the
Biot-Savart map agreeing with the analytic formula to 1e-4.

**The Eye is resolved, computationally, and the answer changed.** A
finer ladder (3.0/2.0/1.5 mm, 30 816 dof) puts the halfwidth
(1.803 mm) below the separation (6.298 mm) for the first time:
`NEAR_CONVENTIONAL_NODE_BUT_DISTINCT` — the conventional model **does
not explain** the candidate. The candidate also does not converge on
the v4.1 coordinate: its distance from (−0.295, −0.205, 102.240) mm
*grows* with resolution (1.375 → 2.270 → 2.476 mm), settling near
(−0.048, −0.020, 99.78) mm. The canonical record is preserved unchanged
(G07) — it faithfully records a ~4 mm-spacing computation — but it is
resolution-limited, not converged. `cl=1.25` was not attempted:
measured 13.9 GB at cl=1.5, projected ~45–71 GB against 31.6 GB of RAM,
so the run stopped honestly. (The first resource estimate used the
textbook dof^1.5 LU rule and was wrong by ~150x; it was corrected
against the measurement.)

**Unchanged and honest:** no measured data exists anywhere; every
experimental campaign is protocol-only; E06/E07 are ethics-blocked; the
Eye result is computational, on an ideal geometry, for one mode, with
an assumed orientation — it is not evidence that any physical crystal
does anything.

## [4.2.0] — 2026-07-16

Master Research Expansion: the post-v4.1 backlog translated into
equations, protocols, controls, and honest statuses. The v4.1 quartz
core, its corrected Eye verdict, and all prior tags are unchanged.
Nothing in this release is an experimental result.

**Coverage contract.** All 248 master-ledger IDs (A01–A18, F001–F052,
G001–G030, E001–E027, S001–S024, W001–W017, H001–H017, C001–C052,
I001–I011) have an owner, an artifact, and a disposition;
`docs/v4/V4X_COVERAGE_LEDGER.md` is generated and gate G42 is enforced
by `tests/v4/test_v4x_coverage_ledger.py`.

**Eye sub-millimetre refinement (C02) — INSUFFICIENT_RESOLUTION.** A
three-level mesh ladder (clmax 8.0/5.5/4.5 mm, 8 elastic modes) with
complex driven response (`fem.harmonic_field`), D9/D10 phase
diagnostics, and a frequency-sensitivity map. The axial coordinate is
stable (z ≈ 102.05–102.31 mm) and modal frequencies converge, but the
transverse centroid still moves at the mesh scale: halfwidth 4.096 mm
versus separation 4.149 mm. The run therefore does **not** resolve
whether the candidate coincides with the conventional node — it neither
refutes nor establishes distinctness. The canonical v4.1 record
(separation 3.906 mm, halfwidth 3.08 mm) is preserved and not
superseded. No proximity threshold is used; exact coincidence remains
the 1e-6 mm numerical tolerance only.

**Eye D9/D10 guard fix.** The realness guards in
`phase_coherence_field` and `phase_singularities_on_plane` moved from an
absolute `np.allclose(w.imag, 0)` test to a relative one
(`max|Im w| < 1e-12 × scale`). The absolute form rejected genuine complex
driven responses at small amplitude — a solver-scale artifact, not
physics.

**Geometry (G01/G02, S001–S024).** Spiral-cone mathematics (curvature
invariant κ·r = 1/√(1+a²), focus eigenvalues −a ± i, per-turn ratio
e^(−2πa)), pinched twisted-cone variant, clamped-plate Bessel modes,
Mohan spiral inductance, structural-versus-electrical resonance
separation, matched controls, and SCAD/DXF/STL/Gerber/drill exports.
`cusp_response_metric` is now arc-length weighted so concentration does
not depend on path sampling density. Merit functionals are declared ENG
constructs with no physical significance.

**Experimental lane (E001–E027, W001–W017, H001–H017).** Nine campaigns
with channels, control matrices, randomization, blinding,
preregistration, and safety-gate evaluation. E01–E05/E08/E09 are
`PROTOCOL_READY_HARDWARE_REQUIRED`; E06 human loading and E07
operator-state are `ETHICS_APPROVAL_REQUIRED` and the gate enforces that
regardless of engineering safety. Water protocols require a
no-ingestion/no-therapeutic-claims acknowledgement. Synthetic DAQ
analysis validated on planted ring-down fixtures; the schema refuses to
label synthetic data as measured. **No hardware was operated and no data
was measured.**

**Consciousness lane (C001–C052) — quarantined.** New `consciousness_lane/`
package with a layered theory registry (layer, status, evidence tag,
falsification condition per entry) and reduced models: Kuramoto against
its analytic K_c = 2γ, state-change decay, dream–wake constraint with a
quarantined K_ext, and the microtubule causal threshold
(τ_c·η_φ·K_cross > θ), which does not clear at the reference 310 K
decoherence estimate and never upgrades on a favourable parameter guess.
THz/superheterodyne items are analogies only; quantum-probability models
are not a quantum brain; Hydrogenuine items make no consciousness claim;
first-person and private-myth layers are retained non-public, unendorsed
and unrefuted. The package may not import quartz solvers — enforced by
test. No consciousness record is usable as evidence in quartz
computation.

**Adversarial QA (Q01).** Eight attack tests: threshold reintroduction,
source laundering, future-interface coercion, quarantine leakage, ethics
gate bypass, synthetic-as-measured, frequency near-miss rounding, and
stale coverage. All repelled.

Post-rc CI hardening (V4X-D-001/002/003): G51 consciousness-lane
quarantine audit check (structural, AST-verified both directions);
release-asset builder reads the version from pyproject instead of a
hardcoded constant; the coverage contract is snapshotted into the
repository (`docs/v4/V4X_LEDGER_IDS.json`) so CI and fresh clones can
evaluate gate G42 without the gitignored prompt pack.

Tests: 737 passing (1 archived-environment byte test deselected by
policy D-V3-04). Hosted CI 10/10 green at the release commit.

## [4.1.1] — 2026-07-16

Documentation-only patch release (no code, solver, or evidence
changes; v4.1.0 remains tagged and frozen). Reason: the v4.1.0
manuscripts asset shipped four documents (USER_GUIDE_V4,
RELEASE_NOTES_V4, ZENODO_METADATA_V4, EYE_METHODOLOGY) that still
asserted the retired CONVENTIONAL_NODE verdict as current without a
correction marker — contradicting the release's own V4C-D-001
correction. This patch: full documentation consistency audit
(`docs/v4/DOCUMENTATION_AUDIT_V4_1_FINAL.md` + machine-readable JSON);
README rewritten for v4.1 (release, install, CLI quick start, corrected
Eye record with the 3.906 mm separation and uncertainty interpretation,
capability-firewall and reference-system distinctions, unimplemented-
physics list); corrected/labelled the four stale documents; historical
banners on superseded v4.0.0 texts; closeout guard tests
(`tests/v4/test_v4c_docs_closeout.py`) that fail the build if the 4 mm
rule, the retired verdict-as-current, or physical-nonexistence claims
are reintroduced; documentation/asset audit of the release builder.

## [4.1.0] — 2026-07-16

Capability-aware multiphysics completion of v4 (all results
computational; no experimental confirmation exists).

**Corrected (V4C-D-001, user-identified):** the Eye Consensus
node-classification rule that absorbed any candidate within a ~4 mm
physical radius into a "conventional node" verdict is REMOVED and
replaced by an uncertainty-aware comparison
(`rscs2_core.eye.node_coincidence_comparison`): exact coincidence only
within declared numerical tolerance (1e-6 mm); interval overlap and
resolved separations reported at their exact values. The canonical
110 mm candidate (z ≈ 102.240 mm) is PRESERVED and reclassified:
separation 3.906 mm from the nearest conventional station, localization
halfwidth 3.08 mm (mesh-resolution dominated), convergence shift
0.353 mm, draw-cloud rms 0.032 mm → verdict
`UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE`. The published v4.0.0 tag and
bundle are frozen history; this release supersedes their
interpretation.

**Added:** source registry + equation ledger with mechanical
classification ceilings (SRC-V4-00..19, RGCS-V4-EQ-001..015); material
capability firewall (16 records, coupling graph with operator-
capability floors, rgcs.v4.result.1 envelopes, no fake zeros;
MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL is never presented as physical
nonexistence); 12-quantity torsion/circulation/optical-AM/chiral
registry with identity prohibitions; Saint-Venant torsion benchmark;
Frenet-Serret; canonical SAM/OAM/topological-charge diagnostics;
reduced-order reference systems (exciton-magnon, avoided crossing
anchored to frozen v3, block Hamiltonian, dressed spin, dynamic
magnetoelectric tensor, metacrystal g2 transfer, LiNiPO4 IOME with
channel discriminators, MnF2 comparator, nonlinear AFM trajectories,
phonon-controlled exchange with direct/indirect classifier); dynamic
boundaries + symmetry lowering with work-energy closure; deterministic
calibration/inverse design with immutable observation ledgers;
quarantined FDT adapter + source-lore translation companion (import-
firewalled, pre-registered predictions); expanded Eye vote layer with
applicability; binding scope statement (What the Canonical Quartz
Model Does and Does Not Claim); adversarial QA (V4C-D-002 NaN
leakage, V4C-D-003 capability laundering — both closed with
regressions).

Frozen: v2.0.0/v3.0.x/v4.0.0 tags, archives, registries, Zenodo
records.

## [3.0.1] — 2026-07-16

Archival and community patch release (no mathematical or behavioral
changes to the v3.0.0 scientific baseline). Contents since v3.0.0:
figure-rendering fixes D-V3-05/06 (README PNG mathtext; siunitx
scientific notation in the Crystal Application manuscript) with
refreshed manuscript assets; the complete laboratory validation
campaign (Agent 14); the archival/community package incl.
`.zenodo.json` (Agent 15). Published to trigger the Zenodo webhook
(enabled after v3.0.0 shipped) and mint the DOI.

- Agent 14 (post-release): measurement-campaign design (ENG, no new
  physics/equations/ids — D14-001): `LAB_MANUAL.md`,
  `CALIBRATION_GUIDE.md`, `BENCH_HARDWARE.md`,
  `MEASUREMENT_PROTOCOL.md`, `DATA_PIPELINE.md`, `VALIDATION_PLAN.md`
  with per-hypothesis observable/measurement/expected/null/controls/
  confidence rows for H-01..H-30, phase gates (H-29/H-30 first),
  TOST-quantified null acceptance for the pre-registered reciprocity
  nulls, and campaign acceptance/failure criteria (D14-002 phasing).
- Agent 15 (post-release): archival + community package — `.zenodo.json`
  machine metadata + `docs/ZENODO_METADATA.md` (no DOI invented);
  `docs/community/` communication kit (press summary, community
  announcement, forum/reddit/LinkedIn/email posts, release FAQ — all
  stating what RGCS is, is not, current evidence, limitations, and how
  to contribute); `docs/CONTRIBUTOR_ROADMAP.md` (software vs
  experimental lanes explicit); `docs/MODELLING_ROADMAP.md` (v4 tier
  plan under reproducibility invariants: CPU oracle, seeded MC,
  typed I/O); `docs/FINAL_PUBLICATION_REPORT.md` → **PUBLISH COMPLETE**.

## [3.0.0] — 2026-07-15

Final release. Agent 13: GitHub repository bootstrapped
(https://github.com/andrew867/rgcs), hosted CI matrix green
(ubuntu/windows/macos × Python 3.11/3.13 portable + pinned ubuntu
reference), NR3-001 determinism policy completed (D-V3-04: portable
tolerance-aware golden-regeneration test on every platform; byte
equality scoped to the archived v2 environment), versions flipped to
3.0.0, release artifacts rebuilt, tag `v3.0.0`, GitHub release
published, repository public. Agent 12 (publication polish) preceded:
README rewrite, contributor documents, docs index, communication kit,
publication readiness report.

## [3.0.0-rc1] — 2026-07-15

Release candidate: all 12 quality gates GREEN (gate 8 with the documented
Linux-execution limitation). Agent 11 fixed the three QA defects
(D-V3-01 coordinate count, D-V3-02 figure reproducibility via
SOURCE_DATE_EPOCH, D-V3-03 CITATION.cff), rebuilt and repackaged the
manuscripts, and shipped `release/` (source zip, manuscript bundle,
sample-experiments bundle, SHA256SUMS, PROVENANCE.json, release notes
with gate table, limitations, and recommended public wording). Final
3.0.0 is gated only on a green Linux CI run.

## [Unreleased] — 3.0.0 programme (RSCS 1.0)

### Added
- Agent 01: `docs/V2_BASELINE_AUDIT.md` (baseline reproduced: 232/232
  archive files identical, 10/10 release checksums verified, 223/227
  tests pass on Windows with all 4 discrepancies explained).
- Agent 01: `docs/V2_TO_V3_MIGRATION_MAP.md` (all 61 equations and 14
  hypotheses dispositioned; registry/versioning rules for v3).
- Programme control documents: `DECISION_LOG.md`, `CLAIM_REGISTER.md`,
  `SOURCE_REGISTER.md`, `ASSUMPTIONS.md`, `NEGATIVE_RESULTS.md`
  (v2's `INCONSISTENCY_REGISTER.md` and `TRACEABILITY_MATRIX.md`
  continue as living registers).
- v3 skeleton per `EXPECTED_TREE`: `rscs_core/` (10 subpackages),
  `manuscripts/` (4 works), `embedded/`, `references/`,
  `tests/adversarial/`, `experiments/protocols|notebooks`.
- `.gitattributes` line-ending normalization.

- Agent 02: verified source registry, equation-provenance ledger, adaptation
  /exclusion matrices, and the frozen `docs/RSCS_NOTATION_LEDGER.md`
  (RSCS-C.1..14 coordinates, RSCS-O.1..13 operators).
- Agent 03: `rscs_core` mathematical backbone — 14 typed coordinates, 13
  operators, RGCS→RSCS embedding with the Conservative Extension Property
  (reproduces RGCS-M.23/24/28/46/55/56/10-11), a claim/provenance firewall,
  and a machine-readable RSCS registry. 64 new tests; anti-Hermitian coupling
  `K=i·2πg` (QA-D-04) enforced. Docs: `RSCS_MATHEMATICAL_MODEL.md`,
  `RSCS_OPERATOR_REGISTRY.md`, `RSCS_COORDINATE_SCHEMA.md`,
  `AGENT_03_HANDOFF.md`.
- Agent 04: Hydrogenuine memory bridge — RSCS-C.15 HG record (ENG) +
  RSCS-O.14/15/16 store/replay/update; NHT/HAL kept HYP-quarantined;
  falsifiable software claims H-15..H-19. Docs: `NHT_HAL_RSCS_MAPPING.md`,
  `HG_RSCS_MEMORY_ARCHITECTURE.md`.
- Agent 05: anisotropic crystal propagation — RSCS-O.17 Christoffel wave
  speeds (`rscs_core.propagation`) + `rgcs_core/anisotropy` (α-quartz
  elastic constants, closes v2 D-19a); resolves the scalar `v_L`
  Hypothesis into a measured-orientation model reproducing v2 at the
  crystal axes. Doc: `RGCS_CRYSTAL_APPLICATION.md`.
- Agent 06: optical/photon-phonon/nonreciprocal layer — RSCS-C.16/C.17
  coordinates, Jones↔Stokes on C.9, RSCS-O.18..O.23 (dispersion phase,
  conversion selection rules, Autler–Townes, critical coupling,
  state-dependent susceptibility with reciprocal-null default, directional
  betas/beating); `rgcs_core/optics` (quartz optical constants, ray/path
  model, photoelastic/M2 estimates); optical experiment schema +
  generated mechanism comparison table; claims H-20..H-23 (H-21/H-23
  pre-registered nulls, D6-003). Doc:
  `OPTICAL_AND_NONRECIPROCAL_COUPLING.md`.
- Agent 07: synchronized excitation/measurement architecture —
  `rgcs_core/timing` (master clock, exact-cycle closures with golden
  125 ms → 512 & 187, modulation families 20/20.48/21/40.96 Hz, coil A/B
  phases, phase-at-coordinate with six declared delay terms, coil
  electrical model, D7-003 safety envelope + dummy-load-first, sweeps +
  ten-branch factorial control matrix with seeded blinding,
  cross-correlation fidelity, signal-level function-generator presets);
  timing programme schema + example; claims H-24..H-30 (node-menu rows
  H-24..H-28); docs `COIL_LASER_TIMING_AND_PHASE.md`,
  `EXPERIMENTAL_PROGRAMME.md`.
- Agent 08: platform tranche T1 — **V2-WIN-01 fixed** (POSIX zip
  arcnames; vertical slice fully green on Windows), specimen-listing
  defect re-diagnosed as missing `jsonschema` (deps declared), Windows CI
  matrix; `rgcs_core/fea_export` (sha256-verified material-card contract),
  `rgcs_core/crystal_db` (schema-versioned persistence + migration),
  `rscs_core/memory/persistence` (H-15/H-17/H-19 machine-tested);
  headless desktop services (provenance graph, waveform/timing preview,
  phase-budget rows); SCAD v7 fixes D-02 with CAD provenance notes;
  HG Embedded OS contract + app-manifest schema; quantified DDS/TCXO/PLL/
  CPLD roadmap (FPGA explicitly not justified). Docs:
  `SOFTWARE_HARDWARE_ARCHITECTURE.md`, enterprise-doc addenda.
- Agent 09: the four v3 manuscripts (RSCS Foundations, RGCS Crystal
  Application, Software & Hardware Roadmap, Historical & Source
  Companion) — XeLaTeX, shared preamble, every number generated by
  `tools/make_v3_artifacts.py`, packaged with per-manuscript
  CHECKSUMS/VERSIONS/BUILD by `tools/package_manuscripts.py`; layout QA
  0 undefined refs / 0 overfull boxes (`docs/LAYOUT_QA_REPORT_V3.md`);
  README v3 header + public Lessons Learned section; QA-D-02 verified
  fixed in the v2 bib and closed.
- Agent 10: independent adversarial QA — fresh `QA_REPORT_V3.md` (22
  dimensions), `CLAIM_AUDIT_V3.md`, `REPRODUCIBILITY_AUDIT_V3.md`,
  defect-register addendum documenting D-V3-01 (coordinate count 18→17),
  D-V3-02 (figure PDFs carry CreationDate), D-V3-03 (CITATION.cff still
  v2) BEFORE fixes; gate recommendation YELLOW → GREEN after Agent 11
  repairs.

### Changed
- `pyproject.toml`: project renamed `rgcs-v3` 3.0.0a1 (D3-001); missing
  `pyyaml` dependency declared (fixes V2-PKG-01 for v3 builds); `rscs_core`
  packaged with its registry yaml.
- v2 release artifacts moved unchanged to `archive/v2.0.0/release/`;
  top-level `release/` reserved for v3 outputs.

## [2.0.0] — 2026-07-14

Frozen baseline. See `archive/v2.0.0/release/RELEASE_NOTES.md`.




