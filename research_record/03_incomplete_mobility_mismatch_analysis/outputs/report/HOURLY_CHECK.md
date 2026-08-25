# RQ3 hour-stratified robustness check

The main model (run_mismatch_analysis.py) pools the whole 18:00-06:00 window into a single per-MSOA total before fitting `log1p(PT) ~ log1p(OD)`. This checks whether that relationship is stable hour-by-hour, or concentrated in specific hours, using the same log1p-OLS specification fit separately per hour (n < 30 valid MSOA-hour cells skipped -- OD's suppression floor makes some hours sparse at the per-MSOA-hour level).

## origin

| hour | n | R² | slope |
|---|---|---|---|
| 18:00 | 979 | 0.520 | 1.148 |
| 19:00 | 979 | 0.474 | 1.087 |
| 20:00 | 974 | 0.463 | 1.049 |
| 21:00 | 962 | 0.463 | 1.002 |
| 22:00 | 922 | 0.453 | 0.971 |
| 23:00 | 767 | 0.413 | 0.945 |
| 00:00 * | 563 | 0.369 | 0.977 |
| 01:00 * | 296 | 0.304 | 0.922 |
| 02:00 * | 193 | 0.288 | 0.836 |
| 03:00 * | 235 | 0.144 | 0.523 |
| 04:00 * | 420 | 0.171 | 0.544 |
| 05:00 * | 764 | 0.154 | 0.466 |

- R² across hours: min=0.144, max=0.520, mean=0.351.
- Deep night (00:00-06:00, marked *, Howard's stated primary interest, 9 Jun): mean R²=0.238 vs. evening (18:00-24:00): mean R²=0.464.

## destination

| hour | n | R² | slope |
|---|---|---|---|
| 18:00 | 979 | 0.365 | 1.074 |
| 19:00 | 979 | 0.324 | 1.024 |
| 20:00 | 978 | 0.298 | 0.916 |
| 21:00 | 975 | 0.295 | 0.843 |
| 22:00 | 952 | 0.245 | 0.770 |
| 23:00 | 874 | 0.194 | 0.664 |
| 00:00 * | 660 | 0.147 | 0.589 |
| 01:00 * | 339 | 0.185 | 0.697 |
| 02:00 * | 220 | 0.210 | 0.704 |
| 03:00 * | 213 | 0.227 | 0.682 |
| 04:00 * | 350 | 0.329 | 0.826 |
| 05:00 * | 674 | 0.367 | 0.821 |

- R² across hours: min=0.147, max=0.367, mean=0.266.
- Deep night (00:00-06:00, marked *, Howard's stated primary interest, 9 Jun): mean R²=0.244 vs. evening (18:00-24:00): mean R²=0.287.
