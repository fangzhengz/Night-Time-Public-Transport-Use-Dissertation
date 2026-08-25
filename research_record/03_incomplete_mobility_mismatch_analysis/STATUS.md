# Status: incomplete mobility–public-transport mismatch analysis

This directory records an attempted comparison between area-level mobility/OD activity and observed public-transport use. It was not completed or implemented as a formal question in the submitted dissertation.

The `src/` snapshot contains the later path correction, while the files under `outputs/` were generated before that correction. They are retained because they document the research process, not because they are verified final results. The corrected code and historical outputs therefore do not form one reproducible run.

Any future reuse must begin by verifying the OD coverage, MSOA crosswalk, suppression, temporal comparability, Rail scope and spatial autocorrelation, then rerun every stage. Negative residuals are candidate mobility-use divergences only; they are not evidence of unmet demand or service deficiency.

Some preserved filenames and internal comments use the former working label `RQ3`. They are retained as historical provenance and do not describe the submitted dissertation's research-question structure.
