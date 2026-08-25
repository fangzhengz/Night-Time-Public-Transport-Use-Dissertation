# Authorised data directory

This directory is the default local root for provider-restricted and large raw
inputs. The data themselves are ignored by Git and are not redistributed.

The expected local structure is:

```text
authorised_data/
├── 巴士数据/
│   ├── Bus_Stops.csv
│   ├── NaPTAN_data/
│   │   └── 490.xml
│   └── ... BUSTO total-demand CSV files ...
├── 地铁进出站数据/
│   └── 地铁车站空间数据/Underground_Stations.csv
├── map/
│   └── London_LSOA_2021_Boundaries.geojson
├── night_time_work_data/
│   ├── london_night_workers_classification_data.csv
│   └── lnwc_variable_dictionary_pen_portaits.csv
├── IMDdata/
│   └── ons_lsoa11_lsoa21_lad22_london_lookup.csv
├── IMDdata_2025/
│   ├── File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv
│   └── imd2025_lsoa21_london.csv
└── data/raw/os_poi/
    └── poi_6438516.gpkg
```

The repository does not depend on a Windows drive letter. If the authorised
inputs live elsewhere, pass their common parent directory explicitly:

```bash
python scripts/run_pipeline.py --dry-run --source-root "/path/to/authorised_data"
python scripts/run_pipeline.py --full --source-root "/path/to/authorised_data"
```

Every adopted stage receives the resolved path through
`CASA_FYP_SOURCE_ROOT`. Generated intermediates and results remain inside the
repository so that inputs and outputs are not mixed.
