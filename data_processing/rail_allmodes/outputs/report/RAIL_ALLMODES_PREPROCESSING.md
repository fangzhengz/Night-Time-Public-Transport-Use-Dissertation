# All-modes rail preprocessing: station-count chain

## Material Passport

- Origin Date: 2026-08-07T03:34:04.088708+00:00
- Verification Status: ANALYZED

## What this covers

This folder converts raw NUMBAT rail-family workbooks (all modes: LU, DLR, Overground, Elizabeth line, Tram) into a single analysis-ready long table, in four steps. It does not build clustering features, fit any model, or decide which stations have non-zero night-time activity -- those remain downstream concerns (see `numbat_all_area_test/`).

## Station-count chain

| step | script | stations | change |
|---|---|---:|---|
| 1 | `01_preprocess_rail_allmodes.py` | 471 | raw NLCs across all NUMBAT rail-family modes |
| 2 | `01b_merge_colocated_stations.py` | 456 | 14 co-located cross-mode site groups (29 NLCs) merged into 14 units |
| 3 | `01c_match_naptan_coords.py` | 440 matched / 16 unmatched | NaPTAN Greater-London (area 490) coordinate match found or not |
| 4 | `01d_filter_naptan_matched.py` (this step) | 440 | unmatched stations dropped |

The **440-station output of this folder is not yet the 403-station clustering population** used by `numbat_all_area_test` -- a further 37 stations (all tram-only, confirmed to have zero recorded activity in every day type, not just at night -- London Trams have no gateline and NUMBAT's Entries/Exits methodology is gateline-based) get dropped by that folder's own `02_build_features_allmodes.py` feature-building step, which this preprocessing folder deliberately does not duplicate. All 37 of those tram stations already have a NaPTAN match (real, served stops, just zero gateline activity), so this step's filter and that later one are independent and do not overlap: 440 - 37 = 403, the final clustering population.

## The 16 NaPTAN-unmatched stations (dropped by this step)

|   unit | Station             | mode_label   |
|-------:|:--------------------|:-------------|
|   1395 | Bushey              | LO           |
|   1402 | Watford Junction    | LO           |
|   1442 | Carpenders Park     | LO           |
|   1455 | Watford High Street | LO           |
|   3147 | Maidenhead          | EZL          |
|   3149 | Reading             | EZL          |
|   3151 | Taplow              | EZL          |
|   3155 | Twyford             | EZL          |
|   3170 | Iver                | EZL          |
|   3171 | Langley             | EZL          |
|   3172 | Slough              | EZL          |
|   3176 | Burnham             | EZL          |
|   6814 | Cheshunt            | LO           |
|   6872 | Brentwood           | EZL          |
|   6888 | Shenfield           | EZL          |
|   6949 | Theobalds Grove     | LO           |

Confirmed genuinely outside Greater London by checking the local `490.xml` NaPTAN extract directly (zero genuine RSE/TMU-type matches for any of these names) -- a structural/geographic fact, not a name-matching bug. They are all in Hertfordshire (Watford DC line and Lea Valley line extensions), Berkshire/Buckinghamshire (Elizabeth line western branch), or Essex (Elizabeth line eastern branch).

## Interpretation boundary

- This is a station-population decision, not a clustering or statistical result -- it does not by itself say anything about night-time transport use.
- The geometric question "is this station's point inside the strict Greater London boundary" (as opposed to "is it in NaPTAN's area-490 list") is intentionally NOT decided here -- canonical's own 270-station Underground clustering includes several stations that fail that stricter geometric test (Amersham, Chesham, Epping, etc.) without excluding them from the clustering itself, only from downstream LNWC/IMD linkage. Downstream analyses that need that distinction should compute it themselves against the LSOA boundary polygon, as `rq2_new_clusters_analysis` does.