# Data provenance and redistribution boundary

The code is open, but not every input can be redistributed. A clean clone therefore supports two levels of reproducibility: immediate verification of committed aggregate evidence, and a full local rebuild for an authorised holder of the raw data.

| Source | Role | Redistribution in this repository |
|---|---|---|
| TfL NUMBAT 2024 day-type workbooks | observed Rail entries/exits by station and quarter hour | not redistributed |
| TfL BUSTO total-demand files | estimated Bus boardings/alightings by stop and quarter hour | not redistributed |
| NaPTAN Greater London XML and TfL stop lookup | StopPoint/StopArea grouping and coordinates | source must be obtained from the provider; local file hash recorded by preprocessing |
| ONS LSOA 2021 boundaries | spatial allocation and context linkage | not duplicated; obtain from ONS/Open Geography Portal |
| London Night Workers Classification | external area classification | include locally only where its licence permits |
| English Indices of Deprivation 2025 | contextual variables | obtain from the official government release |
| ONS Census 2021 via Nomis | demographic, household, tenure and industry variables | download script and source table definitions are provided |
| OS Points of Interest, June 2026 via EDINA Digimap | POI intensity and diversity | licensed source is not redistributed |

Local raw data and Parquet intermediates are excluded by `.gitignore`. The preprocessing audit records file sizes, row counts and SHA-256 hashes, allowing an authorised rerun to establish that it used the same inputs without publishing those inputs.

For a local full rebuild, place the provider files under the repository-relative
`authorised_data/` directory using the structure documented in
[`authorised_data/README.md`](../authorised_data/README.md). The directory is
ignored by Git, so restricted inputs cannot be committed accidentally. This
default is portable and contains no Windows drive letter.

If an authorised holder stores the same directory tree elsewhere, its common
parent can be supplied on any operating system:

```bash
python scripts/run_pipeline.py --dry-run --source-root "/path/to/authorised_data"
python scripts/run_pipeline.py --full --source-root "/path/to/authorised_data"
```

The resolved source root is propagated to every adopted stage. Generated
intermediates and results remain inside the clone. Always run the dry-run
first; its preflight reports every missing source, including the BUSTO file
pattern.
