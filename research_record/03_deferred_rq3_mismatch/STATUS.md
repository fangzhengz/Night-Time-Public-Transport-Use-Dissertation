# Status: deferred RQ3; historical outputs are stale

This directory records the proposed RQ3 on mismatch between area-level mobility/OD activity and observed public-transport use. The question was removed from the final dissertation scope.

The `src/` snapshot contains the later path correction, while the files under `outputs/` were generated before that correction. They are retained because they document the research process, not because they are verified final results. The corrected code and historical outputs therefore do not form one reproducible run.

Any future reuse must begin by verifying the OD coverage, MSOA crosswalk, suppression, temporal comparability, Rail scope and spatial autocorrelation, then rerun every stage. Negative residuals are candidate mobility-use divergences only; they are not evidence of unmet demand or service deficiency.
