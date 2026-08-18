# Archived: pre-NaPTAN-filter all-modes rail results (420 stations)

Snapshot of `outputs/data`, `outputs/figures`, `outputs/report` as they
stood immediately before 2026-07-24's input swap: the full 420-station
all-modes rail-family set (LU + DLR + Overground + Elizabeth line,
co-located NLCs merged, zero-activity stations dropped), with no
NaPTAN-match filtering applied.

**Superseded same day**: 16 of these 420 stations have no NaPTAN
Greater-London (area 490) coordinate match at all (Reading, Slough,
Maidenhead, Watford Junction, Shenfield, Brentwood, etc. -- confirmed
genuinely outside Greater London, not a matching bug) and can never
receive an LNWC/IMD value. Checking their cluster membership found they
concentrated disproportionately (17.6%, 12/68) in one K=5 cluster,
alongside several large National Rail interchanges. The corrected pipeline
filters these 16 out of the raw long table *before* feature-building, then
reruns `02`-`07` unmodified -- so `outputs/data`, `outputs/figures`, and
`outputs/report` now contain the 404-station NaPTAN-matched result under
the same filenames as before. This folder preserves the original
420-station versions for provenance/comparison; it is not used by any
current pipeline.

Includes two intermediate correction attempts also superseded the same
day, kept in sibling archive folders:
- `../archive_strict_extent_v1/`: an even stricter (388-station) filter
  that also excluded stations physically outside the Greater London
  boundary even when they DO have a NaPTAN match (e.g. Amersham, Chesham,
  Epping) -- inconsistent with how canonical itself is scoped, reverted.
