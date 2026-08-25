# RQ3 mismatch analysis: night-time PT usage vs. general OD movement

Independent, non-destructive analysis folder. Does not modify any RQ1/RQ2
input or output.

## Motivation

RQ3 was framed across the 12 May, 26 May and 11 Jun supervisor meetings as
the equity payoff of the dissertation: does observed night-time public
transport (PT) usage (NUMBAT + BUSTO) capture the general night-time movement
that independently exists (Mikaella's 2019 MSOA-to-MSOA OD flow data), or are
there places where people are moving at night but PT isn't picking it up
(candidate unmet demand / car dependence)? RQ1 (clustering) and RQ2
(cluster x LNWC/IMD) were always groundwork for this, not the final answer.
This folder implements the method Esra walked through concretely on 11 Jun:
aggregate NUMBAT/BUSTO to MSOA x hour (same units as the OD data), compare
"trips originating/ending in this MSOA" (OD) against "entries/exits captured
by PT in this MSOA," and flag MSOAs where OD movement is high relative to
captured PT usage.

## Method specification

- **Night window**: 18:00-06:00, matching RQ1/RQ2.
- **Day-type**: the OD data has no weekday/weekend split (single 2019
  average-hour profile), so it is compared against a weekday-representative
  PT slice only (rail `TWT`, bus `Weekday`). Cannot test weekend divergence
  against this OD source.
- **Direction mapping**: OD `origin_msoa` <-> rail entries + bus boardings
  (trips *starting* in that MSOA); OD `destination_msoa` <-> rail exits +
  bus alightings (trips *ending* there). Two independent models, not one
  merged number.
- **Geography**: rail stations are assigned to an MSOA by simple
  point-in-polygon (station lon/lat -> containing LSOA21 -> MSOA11 via the
  ONS lookup in `data/`), not the 1200m Voronoi catchment weighting RQ2 uses
  -- MSOA is coarse enough (~5 LSOAs each) that catchment-splitting is
  unnecessary precision here. 16 rail stations outside the LSOA21 extent are
  excluded (same 16 excluded from RQ2's LNWC analysis). Bus stops are
  assigned via the existing `busto_stop_lsoa_lookup.csv` + the same LSOA21->
  MSOA11 lookup.
- **MSOA vintage**: the OD data is keyed by 2011 MSOA codes; NUMBAT/BUSTO are
  joined via 2021 geography. `src/fetch_msoa_lookup.py` builds a London-only
  LSOA21->MSOA21->MSOA11 lookup from two ONS Open Geography Portal sources
  (see the script for exact item IDs) to reconcile this. 982/983 of the OD
  data's MSOA11 codes are matched.
- **Mismatch metric**: `log1p(PT_total) ~ log1p(OD_total)` (OLS), one model
  per direction, across all MSOAs with coverage on both sides. Both totals
  are heavily right-skewed, so log1p avoids a handful of very high-volume
  MSOAs dominating the fit (a raw-scale version was tried first and produces
  a materially different, outlier-driven top-mismatch list -- log1p is
  the version kept). Large negative standardised residual = MSOA has much
  less captured PT usage than its general OD movement level predicts.
  Explaining the residual further with car-ownership/income covariates is an
  explicitly optional extension Esra mentioned (11 Jun) as time-permitting;
  **not attempted in this pass**.
- **Equity closing step**: each MSOA's residual is quartile-binned and
  cross-tabulated against its dominant LNWC group (RQ2's LSOA-level
  `lnc_grp`, aggregated to MSOA by simple mode -- median purity ~0.60, i.e.
  the modal LNWC group typically covers about 60% of the LSOAs in an MSOA;
  not unanimous, logged not resolved).

## Caveats (stated, not silently dropped)

- OD flow data is 2019; NUMBAT/BUSTO are 2024/25 (5-6 year vintage gap).
- OD flow data is not mode-specific: a gap could reflect car/walk/cycle use,
  not necessarily unmet PT demand specifically.
- OD flow data has a suppression floor (`flow_sum >= 10`) and covers only
  the most prevalent MSOA pairs, not a complete flow census -- likely
  undercounts peripheral/low-volume MSOAs more than central ones.
- A negative residual is a *candidate* mismatch signal, not proof of unmet
  transit demand.

## Run

From this folder (Windows, `py -3` launcher; plain `python` also works if
that's what resolves on this machine):

```powershell
python src/fetch_msoa_lookup.py       # one-off; re-run only if the ONS source changes
python src/build_msoa_panels.py
python src/run_mismatch_analysis.py
python src/run_mode_decomposition.py  # bus vs. rail attribution, reuses the totals above
python src/run_hourly_check.py        # robustness check: is the pooled result stable by hour?
python src/plot_mismatch_map.py       # spatial map of the mismatch score
```

## Folder structure

```text
rq3_mismatch_analysis/
├── README.md
├── data/
│   ├── lsoa21_msoa21_lad22_london.csv   # fetched once from ONS Open Geography Portal
│   └── msoa_lookup_audit.txt
├── src/
│   ├── config.py
│   ├── fetch_msoa_lookup.py
│   ├── build_msoa_panels.py
│   ├── run_mismatch_analysis.py
│   ├── run_mode_decomposition.py
│   ├── run_hourly_check.py
│   └── plot_mismatch_map.py
└── outputs/
    ├── data/       # msoa_pt_panel_hourly.csv, msoa_od_panel_hourly.csv, msoa_pt_totals.csv,
    │               # msoa_od_totals.csv, msoa_mismatch_scores.csv,
    │               # {origin,destination}_top20_mismatch_msoas.csv,
    │               # {origin,destination}_{rail,bus}_mismatch.csv, {origin,destination}_r2_by_hour.csv,
    │               # data_audit.txt
    ├── figures/    # {origin,destination}_pt_vs_od_scatter.png, mismatch_score_map.png
    └── report/     # RESULTS_SUMMARY.md, MODE_DECOMPOSITION.md, HOURLY_CHECK.md
```

## Headline result (as of this run -- provisional, see Interpretation below)

Both directions show a strong, highly significant positive log-log
relationship between OD movement and captured PT usage (origin R²=0.56,
destination R²=0.38 -- see `outputs/report/RESULTS_SUMMARY.md` for exact
figures), confirming the join/aggregation is picking up a real signal
before looking at residuals.

The mismatch quartile x dominant-LNWC association is statistically
significant in both directions (Cramer's V ~0.25-0.27). The largest-mismatch
quartile (most PT-usage-shortfall relative to general movement) is enriched
for **low** night-worker-density LNWC groups (7, "Night-worker periphery";
6, "Low night-worker activity suburban zones"), not high-density ones. The
top-20 mismatch MSOAs per direction (see `outputs/data/`) are spread across
genuine outer London boroughs (Hounslow, Sutton, Croydon, Bromley, Harrow,
Bexley, Enfield, Kingston, Newham, Barnet) rather than dominated by a single
outlier, and 0/20 (both directions) have any rail presence at all -- the
flagged gap is a bus-side signal, not a rail one (`MODE_DECOMPOSITION.md`).

**Important robustness caveat**: the pooled headline R² is driven mostly by
the evening hours. `HOURLY_CHECK.md` fits the same model separately per hour
and finds R² declines from ~0.55 (origin, 18:00, n=981 MSOAs) to as low as
~0.15-0.30 in the 01:00-03:00 window (n=194-297 MSOAs -- OD's suppression
floor thins out the deep night). Howard (11 Jun) said 00:00-06:00
specifically, not the evening, is his primary interest -- so the deep-night
evidence for this result, which is what the equity question is actually
about, is noisier and rests on a much smaller sample than the pooled number
suggests.

## Interpretation boundary

This is a real, geographically sensible, and statistically robust pattern,
but it is a **different** finding from the strongest version of the original
May 2026 hypothesis ("places with many identified night workers whose travel
isn't captured by PT service"). What the data show instead is closer to a
general PT-capture gradient by distance/density: outer, lower-night-worker-
density London shows proportionally less of its general night movement
captured by PT than inner London does -- consistent with higher car
dependence in the outer suburbs generally, not specifically with
under-served night-worker hotspots. Both readings are legitimate and
policy-relevant, but they are not the same claim, and which one to lead with
in the write-up is a genuine interpretive choice, not a settled result --
flag this distinction explicitly if discussing this output with supervisors,
rather than defaulting to the more dramatic "hidden unmet night-worker
demand" framing the residuals do not clearly support.
