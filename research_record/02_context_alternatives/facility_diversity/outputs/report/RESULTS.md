# Early direct-catchment facility results

> **Archived method-development output.** These values come from the early
> direct-catchment spatial implementation and are retained as a backup and
> sensitivity record. The final dissertation did retain `log1p_poi_count` and
> nine-Group `shannon_group`, but recalculated them through the common
> LSOA-first 20-variable context pipeline. Use `results/tables/` for the formal
> Rail (n = 389) and Bus (n = 3,383) results; do not cite the historical Rail
> values below as final results.

| mode   | variable        |    n |     kw_h |      p_value |   epsilon_squared |   distance_band_conditional_p |   q_value_bh |
|:-------|:----------------|-----:|---------:|-------------:|------------------:|------------------------------:|-------------:|
| Bus    | log1p_poi_count | 3383 | 518.165  | 5.52029e-112 |         0.152461  |                         0.001 | 1.10406e-111 |
| Bus    | shannon_group   | 3383 | 163.029  | 4.06742e-35  |         0.04736   |                         0.001 | 4.06742e-35  |
| Rail   | log1p_poi_count |  387 |  33.6521 | 8.78205e-07  |         0.0776233 |                         0.114 | 1.17094e-06  |
| Rail   | shannon_group   |  387 |  41.933  | 1.72234e-08  |         0.0993011 |                         0.001 | 4.59291e-08  |
