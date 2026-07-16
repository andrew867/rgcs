# Press Summary — RGCS v3.0.0

*For science journalists and general audiences. Everything here is
checked against the project's own claim registers; nothing is
speculative.*

**One sentence:** An independent researcher has released RGCS, an
open-source framework that takes folklore about "resonant crystals"
seriously enough to test it properly — and is explicit that, so far,
none of its physical hypotheses is confirmed.

**The story is the method, not a discovery.** Research projects that
draw on unconventional sources usually fail in one of two ways: the
claims quietly harden into "facts" through repetition, or the material
is ridiculed and discarded. RGCS demonstrates a third path. Every
statement in its code, documents, and manuscripts carries one of five
machine-checked labels — Established, Derived, Hypothesis, Source
claim, Engineering plan — and a software firewall makes it impossible
to compute a "established" result from unproven inputs. Historical
claims like "the crystal's eye" become measurable definitions with
pre-registered failure conditions. Several of the project's own
experiments are pre-registered to expect *nothing* — the null result
is the prediction.

**What shipped:** a typed mathematics library, an anisotropic
quartz-acoustics model that provably reproduces its predecessor
wherever they overlap, safety-bounded experiment designs, a complete
laboratory validation plan for its 30 registered hypotheses, and four
manuscripts in which no number was typed by a human — all generated
from tested code, all under MIT license, all tested on three operating
systems.

**What did NOT ship:** any confirmed physical effect. The repository
says this on its front page. There are no medical, therapeutic, or
consciousness claims of any kind; a lint in the test suite enforces
the vocabulary.

**Why it might matter to your readers:** the techniques —
claim-classification as a type system, byte-frozen baselines with
machine-verified "conservative extension," pre-registered nulls — are
applicable to any computational-science project, and are documented
for reuse.

**Facts:** MIT license · https://github.com/andrew867/rgcs · author
Andrew Green (independent) · contact me@andrewgreen.ca
