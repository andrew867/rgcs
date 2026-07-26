# R10.8.5A projection authority

Commit e5864a5 recovered the F5 | Q22 | S3 packet grammar exactly; this
run does NOT reopen it. The failure it corrects is downstream
projection. The authoritative chain is:

decimal transmission number -> fixed-width binary/octal -> typed packet
fields -> recursive non-Cartesian hierarchical address -> full body /
shell / gravity / magnetic / time / ground-reference transform ->
conventional latitude/longitude (final output only).

Codec layers kept separate (Federation/Terra codec only this run):

{
 "wire": "FEDERATION_TERRA_DECIMAL_TRANSMISSION_V1 (radix 10 display of a 30-bit word; civilization-specific)",
 "packet": "F5|Q22|S3 (r12.icosapacket, frozen, reused verbatim)",
 "spatial": "canonical hierarchical icosahedral address (civilization-independent claim, carried not validated)",
 "body": "Terra outer-in gravity-shell projection (this module)",
 "rendering": "conventional latitude/longitude, FINAL output only"
}

Hierarchical X/Y/Z indices are never accepted as latitude, longitude,
Cartesian coordinates, kilometres or decimal altitude
(`HierarchicalAddress` refusals, locked by tests).

The radial reference authority is the OUTER-SHELL GEOMETRY: the
calculation begins at the outermost operational boundary and proceeds
inward along a gravity-field line. The geometric centre is never an
origin in the production path (`refuse_geocentric_spherical_shortcut`).

Stonehenge (`165876523`) is a HARD TRAINING EQUALITY: it calibrates the
frame and is therefore incapable of validating it.
SOURCE_ORIGIN_VALIDATED: no

Verdict: `RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED`
