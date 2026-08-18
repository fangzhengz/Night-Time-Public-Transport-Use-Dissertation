# Reproducibility check

- Formal input: `poi_6438516.gpkg`, layer `Points of Interest 2026_06`
- Input release: OS Points of Interest, June 2026
- Valid unique POIs: 393,530
- Fixed analysis units: 3,372 Bus LSOAs and 388 Rail station catchments
- Seed for conditional permutations: 42
- Permutations: 999

The formal pipeline was run repeatedly with unchanged inputs and configuration.
SHA-256 hashes for every CSV under `outputs/data/` were identical before and
after the final verification run. The fixed cluster labels were not refitted.
