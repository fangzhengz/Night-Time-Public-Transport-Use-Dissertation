# Rail weekend metric: time-window and day-grouping sensitivity

After the Rail time series had been padded to a common 18:00–05:00 frame, one descriptive metric still retained an older convention: it compared weekend and weekday activity only within 18:00–01:00 and excluded Friday. This sidecar asks whether widening that metric to the full window—or aligning its Friday grouping more closely with the Bus convention—would materially change the interpretation of the fixed Rail K=5 clusters.

The clustering is never refitted. The study recomputes only the weekend ratio, compares cluster medians and Kruskal–Wallis effect sizes, and checks station-level rank stability. The variants remain highly rank-correlated, while the full-window definition mechanically incorporates more genuine Friday/Saturday Night Tube activity. The result therefore qualifies the meaning of the descriptor rather than replacing the submitted Rail typology.

Primary evidence is in `outputs/report/REPORT.md`; compact tables and the reproduction figure are retained under `outputs/data/` and `outputs/figures/`. Historical paths in `src/` must be updated before rerunning.
