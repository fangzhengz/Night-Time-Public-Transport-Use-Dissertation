# Archived: strict-Greater-London-extent London-only refit (v1, 2026-07-24)

This was the first attempt at excluding out-of-scope stations before
refitting the all-modes rail clustering. It used "station point is
geometrically inside the Greater London/LNWC boundary polygon" as the
inclusion criterion, which excluded 32 stations (16 with no NaPTAN
coordinate match at all, plus 16 that DO have a NaPTAN Greater-London
(area 490) coordinate match but whose point falls just outside the strict
boundary -- e.g. Amersham, Chesham, Epping, Watford, Chorleywood).

**Superseded same day**: the user pointed out this was inconsistent with
how canonical's own 270-station Underground-only clustering is scoped --
canonical also includes those same border stations (Amersham, Chesham,
Epping, etc., which are part of the LU network) in its clustering universe,
and only excludes them *downstream* from the LNWC/IMD linkage step (where
they fail the same geometric extent check). The corrected criterion is
"has a NaPTAN Greater-London (area 490) coordinate match" -- i.e. is part
of the same official transport-network dataset canonical's own scope is
drawn from -- which only excludes the 16 stations with no match at all,
keeping 404 (not 388) stations for the clustering refit. The downstream
LNWC/IMD exclusion of the geometrically-outside-extent stations still
happens exactly as before, just at the LNWC/IMD step, not the clustering
step -- matching canonical's own precedent exactly.

Kept here for provenance, not used by any current pipeline.
