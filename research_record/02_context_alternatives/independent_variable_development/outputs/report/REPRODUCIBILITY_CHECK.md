# Reproducibility check

- Formal variable count: 18
- Bus analysis units: 3,372 fitted LSOAs
- Rail association-test units: 390 stations with complete formal variables
- Fixed cluster labels: Bus K=4; Rail K=5
- Formal facility variables: `log1p_poi_count`, `shannon_group`
- Excluded from formal combination: `no_car_household_share`

The complete sequence `01_build_variable_table.py` through
`06_build_cluster_panels.py` was run twice with unchanged inputs. SHA-256 hashes
for all output data CSVs, all eight PNG figures and `outputs/report/RESULTS.md`
were byte-identical between runs.
