"""RGCS R10.61 -- archive codec workbench.

Archive bytes propose candidates. Mission metadata defines what the bytes
physically represent. Conventional decoding and RGCS parsing run in
parallel. Nulls and provenance decide what survives.

SCOPE OF THIS PACKAGE AS BUILT
------------------------------
Implemented and tested here:

  wide_envelope   the 126-bit wide-envelope codec, the corrected fixture
                  framing, and all 36 legal left/right splits
  text_lanes      conventional character packings over the payload, at
                  every legal bit offset and bit order
  nulls           matched controls, permutation nulls, multiple-hypothesis
                  correction
  receipts        provenance receipts with source, recipe and commit
  adapters        the typed mission-adapter interface and registry
  cli             parse-long, route, scan-text, verify, mission-list

NOT implemented here, and why:

  catalog/transport/formats -- the HEASARC crawler, the resumable
  downloader and the FITS/PDS readers need astropy, unlzw3 and an HTTP
  stack that are not installed in this environment. The adapter
  interface is in place so those lanes attach without touching the
  codec core, and no mission adapter is registered as available until
  its dependencies exist. See docs/NASA_ARCHIVE_CODEC_QUICKSTART.md.

RESULT CLASSES
--------------
There is deliberately no DISCOVERY or MESSAGE_CONFIRMED state.
"""

RESULT_CLASSES = (
    "NO_PARSE",
    "STRUCTURAL_PARSE_ONLY",
    "CONVENTIONAL_TEXT_CANDIDATE",
    "ERROR_CONTROL_CANDIDATE",
    "RGCS_ENVELOPE_CANDIDATE",
    "RGCS_ROUTE_CANDIDATE",
    "ARCHIVE_ARTIFACT",
    "INSTRUMENT_ARTIFACT",
    "NULL_COMPATIBLE",
    "REPLICATION_REQUIRED",
)

#: States that do not exist by design.
FORBIDDEN_CLASSES = ("DISCOVERY", "MESSAGE_CONFIRMED")

CORE_PRINCIPLE = (
    "Archive bytes propose candidates. Mission metadata defines what the "
    "bytes physically represent. Conventional decoding and RGCS parsing "
    "run in parallel. Nulls and provenance decide what survives.")
