# Pre-merge archive (superseded)

These are the K=6 vs K=7 stability-battery outputs from before
`01b_merge_colocated_stations.py` existed, when the all-modes pipeline ran
on 432 raw NLC-level stations (13 physical sites, mostly interchanges like
Heathrow's terminals, Canary Wharf, and Euston, were split across two or
three separate NLCs instead of one merged station).

At that point the all-modes data's own BIC-optimal K was **7**, and K=6/K=7
was the closest-competing pair, so that is what the stability battery
tested. After merging co-located cross-mode stations, the all-modes
BIC-optimal K shifted to **6** -- matching canonical's own BIC-optimal K --
so the current (non-archived) stability battery in `outputs/report/`
tests K=5 vs K=6 instead, mirroring canonical's own comparison.

This folder is kept only as a record that the K=7 finding was partly an
artefact of un-merged station accounting, not a reproducibility target.
Do not cite these numbers as the current result; see
`../report/VALIDATION_REPORT_ZH.md` and `../report/STABILITY_K5_K6_ALLMODES_ZH.md`
for the current, merged-station analysis.
