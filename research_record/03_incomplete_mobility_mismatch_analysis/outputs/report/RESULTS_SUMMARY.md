# RQ3 mismatch analysis -- night-time PT usage vs. OD movement (provisional)

## Method boundary

Baseline model only: `log1p(PT_total) ~ log1p(OD_total)` (OLS), one model per direction. Both totals are heavily right-skewed (a few very high-volume MSOAs dominate a raw-scale fit), so log1p keeps the regression consistent with the log-log scatter plots and is the standard treatment for this kind of volume comparison. Large negative standardised residual = MSOA has much less captured PT usage than its general OD movement level predicts = candidate mismatch/gap. Explaining residuals further with car-ownership/income covariates is an explicitly optional next step (Esra, 11 Jun 2026), not attempted here.

## Coverage and caveats

- MSOAs with both PT and OD night-window (18:00-06:00) coverage: 979.
- MSOAs with no dominant-LNWC assignment (outside LNWC's LSOA extent): 0.
- OD flow data is 2019; NUMBAT/BUSTO are 2024/25 (5-6 year vintage gap).
- OD flow data is not mode-specific: a gap could reflect car/walk/cycle use, not necessarily unmet PT demand specifically.
- OD flow data has a suppression floor (flow_sum >= 10) and covers only the most prevalent MSOA pairs, not a complete flow census -- likely undercounts peripheral/low-volume MSOAs more than central ones.
- OD data has no weekday/weekend split; compared here against a weekday-only (rail TWT, bus Weekday) PT slice.
- Rail-to-MSOA assignment is simple point-in-polygon (station -> containing LSOA21 -> MSOA11), not catchment-weighted; 16 rail stations outside the LSOA21 extent are excluded (same 16 excluded from RQ2's LNWC analysis).

## Origin: Origin-side (entries + boardings) vs. OD trips starting here

- OLS `log1p(origin_total) ~ log1p(od_origin_total)`: R²=0.535, slope=1.1710 (p=1.273e-164), n=979.
- Mismatch quartile x dominant LNWC: chi-square=199.38, df=18, Cramer's V=0.261, p=1.332e-32, n=979.
- Largest-mismatch quartile (Q1, most negative residual) LNWC enrichment (location quotient, >1 = over-represented): LNWC7 (Night-worker periphery)=2.24, LNWC6 (Low night-worker activity suburban zones)=1.64, LNWC5 (Suburban transport, storage and health business locations with low night-worker activity)=1.42

## Destination: Destination-side (exits + alightings) vs. OD trips ending here

- OLS `log1p(destination_total) ~ log1p(od_destination_total)`: R²=0.369, slope=1.0656 (p=8.909e-100), n=979.
- Mismatch quartile x dominant LNWC: chi-square=184.80, df=18, Cramer's V=0.251, p=1.073e-29, n=979.
- Largest-mismatch quartile (Q1, most negative residual) LNWC enrichment (location quotient, >1 = over-represented): LNWC7 (Night-worker periphery)=2.56, LNWC6 (Low night-worker activity suburban zones)=1.68, LNWC5 (Suburban transport, storage and health business locations with low night-worker activity)=1.23

## Interpretation limits

- Residuals describe MSOA-level association, not individual travel behaviour.
- A negative residual is a *candidate* mismatch signal, not proof of unmet transit demand -- see caveats above (mode, vintage, suppression).
- Top/bottom-20 tables are saved per direction in outputs/data/ for face-validity review before treating any specific MSOA as a finding.