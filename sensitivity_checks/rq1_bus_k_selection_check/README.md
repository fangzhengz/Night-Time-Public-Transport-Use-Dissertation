# Bus CLR K selection: seed battery + night-cluster survival

Sidecar check, run 2026-08-03. Reads `rq1_bus_stoparea_clustering`'s CLR feature
matrix (3,372 LSOAs x 72 features, full covariance) and its adopted K=4 labels.
Modifies nothing outside this folder.

## Why

The adopted bus result, StopArea CLR K=4, was selected on BIC alone and had
never been seed-checked, while BIC in CLR feature space had been shown to be
seed-unstable on this project's bus data (the 2026-08-01 day-type sidecar, where
a K=5 BIC advantage of +17,401 became -5,476 on another seed). The rail side had
already resolved its own K question with a seed battery plus a night-cluster
survival check. This runs both diagnostics on bus.

## Run

```powershell
py -3 src/run_seed_check.py          # ~17 min
py -3 src/inspect_k4_solutions.py    # ~4 min
py -3 src/profile_best_k4.py         # ~2 min, figures + crosstab
py -3 src/centrality_compare.py      # ~1 min
```

## Findings

**1. K=4 is the BIC optimum in every fit — the day-type failure mode does not
reproduce.** K=4 won 5/5 seeds at n_init=20 and 3/3 at n_init=100. Raising the
restart budget did *not* shift the preference toward higher K, unlike rail.

**2. What is unstable at the adopted budget is the margin, not the ranking.** At
n_init=20 the K=4 advantage over the better of K=3/K=5 was 80.0 / 199.5 /
16,510.9 / 16,576.3 / 17,473.3 across the five seeds — two seeds simply failed to
reach the reported optimum. At n_init=100 it is 15,212 / 16,491 / 19,006, and the
BIC range at K=4 falls from 16,455 to 3,752. The swing is an under-optimisation
artefact of a 20-restart budget, not evidence against K=4.

**3. The adopted labels are not the best K=4 solution found.** n_init=100,
seed 7 reaches BIC -401,814 against the adopted -399,343 (`k4_solution_comparison.csv`).

**4. All seed variation is confined to the low-flow end; the night-persistent
cluster is invariant.** Across all five distinct K=4 solutions, two clusters
recur essentially unchanged — the night-persistent one (n 1,129-1,145,
log activity 8.01-8.02, post-midnight persistence 0.2363-0.2367) and the
moderate-to-high-flow one (n 1,058-1,062, persistence 0.1915-0.1925). The
remaining ~1,150 low-flow LSOAs are split differently each time (610/559,
948/233, 756/412, 677/492), which is what drives ARI-vs-adopted down to
0.847-0.945 (`k4_solution_profiles.csv`).

**5. Night-cluster survival does not discriminate between K=3 and K=4.** The
adopted night cluster is recovered at Jaccard 0.945 already at K=3, 0.995 at
K=4, 0.984 at K=5 (`night_cluster_survival_summary.csv`). A size-matched
reference set built from `post_midnight_persistence` alone, with no clustering
involved, is recovered at ~0.40 at *every* K (0.411 at K=2 down to 0.387 at
K=7) — so no K recovers a persistence-defined night group especially well, and
this diagnostic cannot be used to argue for K=4 the way it was used for rail.

**6. Seed reproducibility alone would favour K=3 or K=5 over K=4.** Mean
pairwise seed ARI at n_init=20: K=2 1.000, K=3 1.000, K=4 0.901, K=5 0.970,
K=6 0.790, K=7 0.890 (`seed_agreement.csv`).

**7. The better-likelihood solution is interpretively equivalent to the adopted
one.** Characterised in `profile_best_k4.py` / `centrality_compare.py` with
cluster ids Hungarian-aligned to the adopted labels:

- *Membership*: 256 of 3,372 LSOAs (7.6%) change cluster, and every one of them
  moves between the two low-flow clusters — 227 from C0 to C3, 29 from C3 to C0.
  C1 keeps 1,142 of 1,145 members and C2 keeps 1,057 of 1,058
  (`best_k4_vs_adopted_crosstab.csv`).
- *Temporal ordering unchanged*: post-midnight persistence runs C1 0.236 >
  C2 0.192 > C0 0.148 > C3 0.100 in the new solution against C1 0.237 >
  C2 0.192 > C0 0.142 > C3 0.089 in the adopted one. The four-tier
  night-persistence reading survives intact.
- *Geography essentially unchanged*: mean km from Charing Cross by cluster is
  14.0 / 10.0 / 12.5 / 15.0 against the adopted 13.9 / 10.0 / 12.5 / 15.4, and
  the share of the distance-to-centre variance explained falls slightly
  (eta² 0.1205 -> 0.1158). The side-by-side map reads as if the new solution
  gives the outer ring to C3 more cleanly, but the distance profiles do not
  support that — the reassigned LSOAs are not preferentially outer ones. The
  central/outer total variation on the four benchmark boroughs is 0.361 ->
  0.354, i.e. Howard's central/outer mixing is neither fixed nor worsened.

So the refit in the note below is a protocol question, not a substantive one:
it changes which borderline low-flow LSOAs sit in which of the two weakest
clusters, and changes nothing about the headline cluster, the temporal story or
the geography.

**8. K=5 is not supported (`evaluate_k5.py`).** Fitted at n_init=100, seed 42:
BIC -382,852 against K=4's best of -401,814, a deficit of ~19,000. What the
fifth component does is split the adopted C0 (the weakest K=4 cluster) into
n=397 and n=235; every other cluster passes through intact, including the
night-persistent one (1,131 of 1,145 retained), so K=5 adds nothing to the night
story. The two halves are barely distinguishable:

| | n | log activity | persistence | weekend ratio | km from centre | silhouette |
|---|---|---|---|---|---|---|
| C0 | 397 | 6.17 | 0.128 | 0.763 | 13.6 | 0.072 |
| C2 | 235 | 6.39 | 0.166 | 0.770 | 14.8 | 0.078 |

And the split does not survive resampling — per-cluster bootstrap Jaccard over
40 replicates is 0.301 for C0 (**minimum 0.000**, i.e. at least one replicate
fails to recover it at all) and 0.640 for C2, against 0.917 for the
night-persistent cluster.

The one criterion that favours K=5 is seed reproducibility (ARI 0.970 at
n_init=20, 0.999 at n_init=100, both above K=4's). That is not a contradiction:
seed ARI asks whether repeated initialisations on *the same data* converge to
the same partition, while the bootstrap asks whether the partition reappears in
*resampled* data. A stable cut through a homogeneous region scores well on the
first and badly on the second. Here they disagree and the bootstrap is the
relevant one.

## What this means for the write-up

The bus K rests on BIC, and the seed battery shows that is safe: the ranking is
reproducible across seeds and across restart budgets. This is the opposite of
rail, where BIC could not resolve K and the choice rests on stability and
night-cluster survival instead. Both are defensible; the chapter should say
which criterion discriminated in each feature space rather than applying one
rule to both.

Two things to disclose rather than resolve:

- The bootstrap min matched cluster Jaccard of 0.401 at K=4 (against 0.883 at
  K=3), already recorded in `rq1_bus_stoparea_clustering/outputs/clr/diagnostics/kdiag.csv`.
  Finding 4 is consistent with that instability sitting in the low-flow split
  rather than in the night-persistent cluster, but this run does not verify which
  cluster carries the minimum — that would need the bootstrap replicate labels.
- ~~Finding 3 argues for refitting the adopted labels under a protocol that
  states the restart budget and retains the best-likelihood solution across
  seeds, rather than a single n_init=20 seed-42 fit.~~ **Done 2026-08-03.**
  `rq1_bus_stoparea_clustering` now refits the candidate Ks at n_init=100 across
  five seeds and keeps the maximum-likelihood solution (`N_INIT_FINAL` /
  `FINAL_SEEDS` in its config.py; provenance in
  `outputs/clr/diagnostics/final_refit.csv`). The retained fit is seed 999,
  BIC -401,817 — slightly better again than the seed-7 solution characterised
  here, and essentially the same partition (ARI 0.998 against
  `best_k4_labels.csv`). The whole downstream RQ2 chain was rerun. As predicted
  by finding 4 the night-persistent cluster was unaffected (n 1,145 -> 1,141)
  and every external association moved by less than 0.003; unexpectedly, the
  bootstrap min matched Jaccard improved from 0.401 to 0.534, so the disclosure
  above is now a weaker caveat than when it was written.

## Outputs

| File | Contents |
|---|---|
| `bic_by_seed.csv` | every fit: grid, n_init, seed, K, BIC, min cluster n, seconds |
| `bic_spread.csv` | per K: BIC mean/min/max/range and how many seeds it won |
| `k4_bic_margin.csv` | per seed: K=4's advantage over the better of K=3/K=5 |
| `seed_agreement.csv` | per K: mean/min/max pairwise seed ARI |
| `night_cluster_survival.csv` / `_summary.csv` | Jaccard of the best-matching cluster against both night reference sets |
| `k4_solution_comparison.csv` | the five distinct K=4 solutions: BIC, ARI vs adopted, sizes |
| `k4_solution_profiles.csv` | per-cluster continuous profile for each of those solutions |
