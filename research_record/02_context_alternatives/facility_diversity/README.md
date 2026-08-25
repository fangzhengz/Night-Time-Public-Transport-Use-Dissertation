# Early facility-diversity implementation

## Status: archived spatial-method sensitivity

This folder is an early implementation of the facility layer, not an analysis
that was wholly excluded from the dissertation. Two headline measures developed
here—`log1p_poi_count` and nine-Group `shannon_group`—were retained in the final
20-variable context analysis.

What changed was the spatial connection method. This early version assigns POIs
directly to each analytical unit: fitted LSOA polygons for Bus and 800 m
Voronoi-clipped station catchments for Rail. The adopted pipeline instead
calculates both POI measures for every LSOA first, then uses the same established
LSOA-based Rail aggregation procedure as the other contextual variables. That
change places all 20 indicators on a consistent spatial estimand.

The folder is therefore preserved as a backup and spatial-method sensitivity.
Its direct-catchment Rail estimates, POI-density measures, Category-level
Shannon index and no-Transport variants are not the formal dissertation results.
The final values and tests are published under `results/tables/` and generated
by `analysis/04_urban_context/`.

This sidecar reproduces the facility layer described in the BtC paper using
Ordnance Survey Points of Interest (POI). It keeps the adopted Rail K=5 and Bus
K=4 labels fixed and joins facilities only after clustering.

## Metrics

Primary metrics:

- total POI count and `log1p` count;
- Shannon diversity across the nine OS POI Groups.

Sensitivity metrics:

- POI density per square kilometre;
- Shannon diversity across the 52 OS POI Categories;
- count and diversity after excluding OS Group 10 (Transport), reducing the
  risk of circularly treating transport infrastructure as an explanation of
  transport use.

Bus metrics are calculated within fitted LSOA21 polygons. Rail metrics use the
existing 800 m Voronoi-clipped catchments and the established 388-station
Greater-London context universe. Rail and Bus results are interpreted
separately because their analysis units differ.

## Input

Download **Points of Interest** from OS Digimap for a user-defined rectangle
covering Greater London plus at least an 800 m margin. GeoPackage is preferred.
Keep the original Group, Category, Class, reference-number and coordinate
fields. Store the file under `data/source/`; licensed raw data are ignored by
version control.

## Run

```powershell
cd D:\SDS2025_workspace\CASA_FYP\FYP\rq2_facility_diversity_analysis
python src\run_analysis.py --poi data\source\YOUR_OS_POI_FILE.gpkg
```

Outputs are written under `outputs/`. The runner audits classification
coverage, duplicate identifiers, zero-facility units and POI-to-unit spatial
allocation before producing any inferential result.

## Current data release

The completed run uses OS Points of Interest, June 2026, downloaded from EDINA
Digimap on 7 August 2026. The exact source citation and licensed product
documentation are retained under `data/source/`; the raw GeoPackage is excluded
from version control.

For historical interpretation, compare the headline `log1p_poi_count` and
`shannon_group` definitions with the adopted pipeline, but do not substitute the
numerical results in this folder for the final 389-station Rail and 3,383-LSOA
Bus context tables. Treat density, Category-level Shannon diversity and the
no-Transport variants as sensitivity checks. In particular, Rail density partly
reflects the geometry of the Voronoi-clipped catchments and should not be treated
as a primary Rail result.
