# How the mode-specific models developed

The final Rail K=5 and Bus K=4 solutions were not selected from a single diagnostic table. They emerged from two different methodological journeys. Rail began with an Underground-only study and expanded when the research scope was challenged; Bus began with a spatial-allocation problem and then confronted the instability of sparse temporal compositions. In both cases, apparently technical choices—station co-location, StopArea grouping, time-window closure, low-flow thresholds and compositional coordinates—changed what the clusters could reasonably mean.

This section keeps those journeys visible. `method_experiments/` contains the alternatives that isolated individual assumptions or tested possible replacements. `formal_sensitivity_checks/` contains focused checks of geography, K and stability. `rail_scope_and_stability/` records the successive Rail populations and K batteries, while `adopted_bus_diagnostics_snapshot/` preserves the fuller diagnostic evidence surrounding the final Bus route.

The folders should be read chronologically and comparatively. A high ARI, lower BIC or visually coherent map answers only the question posed by that experiment; it does not automatically make that branch the adopted model.
