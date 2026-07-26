# Reverse encoding

Chain: chosen conventional location -> epoch and ground frame ->
magnetically corrected gravity shells -> outer-in shell address ->
hierarchical path -> F5|Q22|S3 -> octal -> decimal transmission number.

Stonehenge at its decoded height, per declared profile:

{
 "UNIFORM_100KM_V1": {
  "decoded_height_km": 90.1367,
  "word": 165876523,
  "reproduces_packet": true,
  "octal": "1170611453",
  "aliasing_note": "the word stores face, 11 path levels and a 3-bit shell register only: every point of the same terminal cell and shell band encodes to this same word (explicit aliasing; the in-shell zeta and octree split are NOT independently settable by the encoder)."
 },
 "ATMOSPHERIC_LADDER_V1": {
  "decoded_height_km": 10.8164,
  "word": 165876523,
  "reproduces_packet": true,
  "octal": "1170611453",
  "aliasing_note": "the word stores face, 11 path levels and a 3-bit shell register only: every point of the same terminal cell and shell band encodes to this same word (explicit aliasing; the in-shell zeta and octree split are NOT independently settable by the encoder)."
 },
 "GEOMETRIC_DOUBLING_V1": {
  "decoded_height_km": 22.5342,
  "word": 165876523,
  "reproduces_packet": true,
  "octal": "1170611453",
  "aliasing_note": "the word stores face, 11 path levels and a 3-bit shell register only: every point of the same terminal cell and shell band encodes to this same word (explicit aliasing; the in-shell zeta and octree split are NOT independently settable by the encoder)."
 }
}

All profiles reproduce the original packet exactly
(True). Aliasing is intrinsic and explicit: the word
stores face + 11 path levels + a 3-bit shell register, so every point
of the same terminal cell and shell band encodes to the same word.

Inverse from the site's PHYSICAL height
(-0.738 km relative to land-zero, i.e. below it):
REFUSED: height -0.738 km above land-zero is outside the operational stack (0..600.0 km under UNIFORM_100KM_V1); shells 0..2 below the land-zero surface are not addressable by this codec.

That refusal is the radial-lane misfit seen from the other side: the
codec cannot address sub-land-zero heights (shells 0..2 undeclared),
so the monument's physical elevation is outside the operational stack.

Per the R10.8.5A instruction, no new source-style coordinate is
generated: the forward and inverse transforms pass the training
equality laterally but the radial lane misfit stands, so a generated
number would still be the product of an incomplete projection.
