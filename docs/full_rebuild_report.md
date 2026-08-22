# Full rebuild report

The adopted analysis was rerun end to end in an isolated copy of this repository on 22 August 2026. All stages completed and the frozen-evidence validator passed.

## Reproduced analytical state

- Bus preprocessing read 12 BUSTO files and produced 1,873,645 stop-quarter-hour rows for 19,579 stops in the 18:00–05:00 window.
- StopArea allocation conserved the source activity totals; 3,383 LSOAs met the minimum of 33 estimated boardings and 33 estimated alightings.
- Bus CLR/full-covariance GMM K=4 reproduced the adopted labels exactly (ARI=1.000 against the prior final labels) and cluster sizes 604, 1,134, 1,069 and 576.
- Rail preprocessing reduced 471 raw NLC units to 456 co-located sites, 440 NaPTAN-matched sites and 403 active analytical stations.
- Rail diagonal-covariance GMM K=5 reproduced cluster sizes 89, 26, 90, 31 and 167.
- LNWC and the 20-variable urban-context analyses completed for Rail n=389 and Bus n=3,383.
- Rail LNWC composition permutation R-squared was 0.2629202279 with p=0.001 (999 permutations); Bus Cramer's V was 0.2525849041.

## Reporting-layer consistency

The active Bus behavioural signature contains the five adopted descriptors only. The diagnostic aggregate `timing_mean_eta2` is therefore calculated from those same five metrics. This reporting-layer alignment does not change the K=4 labels, cluster sizes or final result tables.

Recomputed urban-context CSV values can differ from the earlier exported copies in the final decimal places (maximum observed difference below 5e-8) because the former tables were rounded. This is serialization precision, not a change in the substantive result.
