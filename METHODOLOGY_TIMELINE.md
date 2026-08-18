# Methodology Timeline: From Early Prototypes to Adopted Approach

This document summarises the evolution of clustering and analysis methods across the project. It is archived primarily for transparency and reproducibility—readers and reviewers should cite the **adopted** methods described in the main dissertation, not these intermediate attempts.

## Phase 1: Early Bus Clustering Experiments (Jun–Jul 2026)

The initial approach tested multiple allocation rules and distributional assumptions on bus data:

- **Hub-first allocation** (`archive_methodology/rq1_bus_hub_first_*`): Early rule-based stop-to-LSOA assignment using NaPTAN's ParentStopAreaRef hierarchy. Resulted in systematic central/outer mixing artifacts that were masked by low silhouette scores (GMM silhouette ~0.02). Formal diagnosis in `rq1_bus_hub_first_reclustering/` (ARI = 0.570 vs later adopted method).
  - Explored alpha-grid sensitivity and reliable-core filtering, but mixing persisted (ε² for activity = 0.58 after filtering, worse than unadjusted).
  
- **Coordinate transforms** (`archive_methodology/rq1_bus_ilr_transform`, `rq1_bus_hellinger_*`): Tested Isometric Log-Ratio (ILR) and Hellinger distance in hopes of reducing zero-bin dominance. None resolved the substantive central/outer segregation, only changed the noise floor. Ruled out as a root cause.

- **Alternative feature sets** (`archive_methodology/rq1_bus_daytype_normalisation`): Tested day-type-normalised (padded) windows vs full-week. Daytype padding reduced zero-bin eta² but made K-identifiability worse; kept full-week as primary per estimand argument.

**Why discarded**: All were methods-in-search-of-a-problem. The actual problem (central/outer mixing) was structural, not a statistical transformation away.

## Phase 2: Adopted Bus Method (Jul 22–Aug 3, 2026)

**Official solution**: StopArea-level clustering with CLR (Centered Log-Ratio) composition algebra, K=4, 18:00–05:00 window.

- **StopArea allocation** (`data_processing/bus_stoparea/`): Replaces hub-first with a simpler rule: assign stops to their geometric StopArea polygon, then aggregate demand to LSOA. This is more deterministic, fewer ambiguous hierarchical decisions.
  
- **Window selection** (`sensitivity_checks/rq1_bus_05cutoff_sensitivity/`): Tested 18:00–05:00 (adopted) vs 18:00–06:00 (earlier version still in `outputs/`). The 05:00 cutoff is tighter to true night hours and slightly reduces noise; both are defensible, but 05:00 is formal choice.
  
- **K selection** (`sensitivity_checks/rq1_bus_k_selection_check/`): Seed-stability test (n_init=100 for K=2–8) showed K=4 is optimal and reproducible (ARI=0.727 bootstrap vs K=3's mixed stability).
  
- **CLR transform** (component of adopted output): Compositional algebra applied post-hoc to the feature matrix, not as a coordinate change but as a significance test. Zero-bin eta² = 0.54–0.58 (lower than hub-first but not eliminated); this is now known to be inherent to GMM+compositional geometry, not a defect (see literature in `sensitivity_checks/`).

**Key outcome**: Bus clustering now explains ~52% of activity variance and 29% of timing metrics (deliberate trade-off), and matches all downstream LNWC/IMD association magnitudes (ρ = 0.254).

## Phase 3: Rail Clustering Refinement (Jul 22–Aug 2, 2026)

Rails method was simpler but had one critical fix mid-project:

- **Pre-Paddington** (through 08-01): Rail clustering used 404 stations, but manual inspection found Paddington is co-located at two different TfL grid codes (NR platform vs TfL Underground platform). Treating these as separate inflated K=6 as optimum and caused central-inner discrepancies.
  
- **Post-Paddington merge** (08-02 onward): Merged the two Paddington records; now 403 stations. K=5 is optimal and stable (seed ARI=0.964 primary, 0.859 validation).
  
- **Window alignment**: Adopted 18:00–05:00 to match bus, across all 5 day-types, with equal padding to 440 dimensions per day-type.

**Scope note**: `numbat_all_area_test/outputs/archive_*` contains pre-Paddington versions (420 and 404 station attempts) kept for audit trail. Do not cite these; use `outputs/data/rail_allmodes_k5_labels.csv` (403 stations post-merge).

## Phase 4: RQ2 Association Methods (Jul–Aug 2026)

### LNWC Enrichment and Independent Variables

- **Early version** (`archive_methodology/rq2test analysis/`): Provisional clustering with provisional rail (K=6 diagonal GMM), bus (full-GMM K=4). Adopted canonical rail/bus K-values and updated.
  
- **Variable set evolution** (`rq2_independent_variables/src/config.py`, lines 1–50): 20-variable two-layer method. Rationale for each variable and drop/re-add decisions documented in file. Key decisions:
  - Dropped `no_car_household_share` (2026-08-07) → re-added 2026-08-08 because it anchors Discussion's car-dependency argument
  - Added TS011 (2026-08-03) as tight proxy for night workers in BRES when LNWC categories align
  - Refused LOAC as a single composite (2026-07-31) because it masks the ecological-fallacy vulnerability; instead analysed LOAC separately (see `rq2_loac_analysis/`)

### Catchment Sensitivity

- **Primary** (`rq2_new_clusters_analysis/outputs/`): LNWC/IMD association at 800 m equal-weight radius (rail stations), LSOA-direct join (bus).
  
- **Sidecar** (`rq2_new_clusters_analysis/outputs_800m/`): Area-weighted rail catchment (stations weighted by LSOA overlap %). Results stable (ρ ranged 0.215→0.254; IMD 0.050→0.060). Both reported, but equal-weight is primary.

- **Historical sensitivity** (not in this repo by default, archived notes in `WORKSPACE_AUDIT_AND_GITHUB_PLAN.md`): 1,200 m tested early; results were stable but 800 m is tighter to walking distance and clearer. Adoption was a design choice, not a result of fishing.

### Facility Diversity and Spatial Signatures

- **Facility diversity** (`rq2_facility_diversity_analysis/`): OS POI point-in-polygon facility count + diversity sidecar. Not a main text result but included as sensitivity check on LOAC-like external variables.
  
- **Spatial Signatures** (`rq2_spatial_signatures_analysis/`): External validation using published GB Spatial Signatures classification (EESECTOR). Joins post-clustering; shows broad alignment but is descriptive, not causal.

## Dropped and Archived

### RQ3: Mismatch Analysis (Formally Dropped 2026-08-05)

- **Scope**: Night-worker residence (LNWC) vs night-activity cluster mismatch.
- **Finding**: Some LSOAs have residents coded as night workers but sit in low-activity clusters, and vice versa.
- **Why dropped**: Supervisor decision (2026-07-17) reframed this as an ecological-fallacy **vulnerability**, not an independent research question. Moved to Discussion. Bug in original config.py was fixed 2026-08-08 but outputs were generated pre-fix, so code is kept but outputs are not included.
- **In repo**: `rq3_mismatch_analysis/src/` (code only) + `README.md` (explanation).

### Context Metrics Interpretation (Stale, Not Included)

- `rq1_context_metrics_analysis/` analysed temporal/directional context using the **retired** `cluster_clean_version_fullweek` clustering (pre-StopArea, K=5 underground-only rail). Numbers will not match the dissertation's current results. Referenced here only for historical completeness; not included in the repo. If future work needs activity/timing context, this folder's code structure can be adapted to the new clustering.

## Related Robustness Tests (Included in `sensitivity_checks/`)

1. **Window choice** (`rq1_bus_05cutoff_sensitivity/`): Reprocesses bus data under 18:00–06:00 (old) vs 18:00–05:00 (adopted). Same K=4 structure, slightly different feature distribution.

2. **K-selection stability** (`rq1_bus_k_selection_check/`): Seed battery (n_init=100) for K=2–8, showing K=4 reproducibility.

3. **Central/outer geography** (`rq1_bus_geography_diagnostic/`): Diagnoses whether central/outer LSOA mixing is real (it is) and stable (it is) under the adopted StopArea allocation.

## How to Navigate This Repository

**For readers of the dissertation**: Ignore `archive_methodology/` unless you are reviewing methodology choices. Citation should always refer to the adopted methods documented in the main repository:
- Bus clustering: `rq1_bus_stoparea_clustering/outputs_1805_min33/` (K=4, CLR, StopArea, 18:00–05:00)
- Rail clustering: `numbat_all_area_test/outputs/` (K=5, all-modes, 18:00–05:00)
- RQ2 associations: `rq2_new_clusters_analysis/outputs/` (primary), `rq2_independent_variables/outputs/data/` (20-variable set)

**For methodologists or supervisors auditing decisions**: See this file and the decision logs in `dissertation/narrative_arc_and_source_index.md` for rationale on each pivot.

**For future replication or extension**: Methodology once adopted should not be re-explored in a new project without good reason. If you believe a discarded approach (e.g., ILR transform, hub-first, daytype padding) is worth revisiting, check `archive_methodology/` for past diagnostics first.
