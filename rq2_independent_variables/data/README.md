# Downloaded source data — provenance

All files here are produced by `src/00_download_census.py` from the **Nomis API**
(`https://www.nomisweb.co.uk/api/v01/dataset/`), ONS's official distribution
channel, no registration required. Re-running that script regenerates every file
in this directory. Downloaded **2026-07-31**.

Every request uses `geography=2013265927TYPE151` — Nomis's London region code
crossed with 2021 lower-layer super output areas — which returns all **4,994**
London LSOAs. Results are then filtered against the project's own boundary file
(`FYP/map/London_LSOA_2021_Boundaries.geojson`) rather than trusting Nomis to
define "London" for us.

| File | Source table | Nomis dataset | Denominator |
|---|---|---|---|
| `ts045_car_van_availability_lsoa.csv` | TS045 Car or van availability | NM_2063_1 | households; traceability only, excluded from formal set |
| `ts011_household_deprivation_lsoa.csv` | TS011 Households by deprivation dimensions | NM_2031_1 | households |
| `ts054_tenure_lsoa.csv` | TS054 Tenure | NM_2072_1 | households |
| `ts021_ethnicity_lsoa.csv` | TS021 Ethnic group | NM_2041_1 | usual residents |
| `ts003_household_composition_lsoa.csv` | TS003 Household composition | NM_2023_1 | households |
| `ts007b_age_bands_lsoa.csv` | TS007B Age by broad age bands | NM_2018_1 | usual residents |
| `ts066_economic_activity_lsoa.csv` | TS066 Economic activity status | NM_2083_1 | residents aged 16+ |
| `ts060_industry_lsoa.csv` | TS060A Industry (3-section night aggregate) | NM_2017_1 | employed residents 16+ |
| `ts060_industry_section_shares_lsoa.csv` | TS060A Industry (all 18 sections) | NM_2017_1 | employed residents 16+ |
| `bres2024_industry_sections_lsoa.csv` | BRES 2024, 8 SIC sections | NM_189_1 | jobs in LSOA **and** km² |

## Three traps found while building this, worth knowing before re-running

**1. Nomis truncates silently at 25,000 rows.** The first attempt requested
`geography=TYPE151` (all ~35,000 LSOAs in England and Wales) and received 5,000
alphabetically-first northern LSOAs and zero London ones — with no error. The
download script pages unconditionally and reports the LSOA count each time.

**2. TS060 is disclosure-suppressed at LSOA level.** The 106-category industry
table (NM_2077_1) returns a row for every London LSOA with `OBS_VALUE` empty and
`OBS_STATUS='Q'` ("These figures are missing"). Parsed naively those become
zeros. **TS060A** (NM_2017_1, 19 sections) is the release actually published at
LSOA. The script raises if a whole table comes back empty.

**3. Several tables nest headline rows above their own sub-breakdowns.** TS054
carries both "Private rented" and "Private rented: Private landlord or letting
agency"; TS003 carries "One-person household" above ": Aged 66 and over" and
": Other"; TS066 writes aggregate rows without spaces after the colons and leaf
rows with them. Substring matching double-counts. Entries needing headline rows
only are marked `"exact": True` in `config.DOWNLOAD_SPEC`, and every label match
is asserted unique — a change to Nomis's wording fails loudly rather than
silently summing the wrong cells.

## Why two industry sources

`ts060_*` is **residence-based** (Census: where people who work in an industry
*live*). `bres2024_*` is **workplace-based** (BRES: where the *jobs* are). They
are not substitutes:

* Residence-side predicts night-travel **origins and home-bound destinations** —
  people leaving home for a night shift, or returning from one.
* Workplace-side predicts night-travel **destinations and work-bound origins**.

That distinction is what lets the rail `direction_balance` finding (entry- vs
exit-dominant clusters) be tested rather than asserted. LNWC already covers the
workplace/business side as a composite; BRES decomposes it into specific
industries.

## BRES caveats

* This is the **open-access** release, not the secure-access version
  (UKDA-SN-7463) cited by Peiret-García, Kimani & Suel. Open-access values are
  rounded to multiples of 5.
* BRES has no SIC section (letter) level; the eight sections are summed from
  2-digit divisions (manufacturing = 10–33, wholesale/retail 45–47,
  transport/storage 49–53, accommodation/food 55–56, info/comms 58–63,
  professional/scientific 69–75, education 85, health/social 86–88). Verified
  2026-07-31: every division exists, values are published at LSOA, and the
  result reproduces London's known structure (manufacturing 1.85%,
  professional/scientific 13.80%, 5,737,530 total jobs).
* **Jobs per LSOA range 0 to 412,000 (median 300)**, because LSOAs are drawn on
  resident population, not employment. So BRES *shares* are unstable in the ~40%
  of LSOAs with under 250 jobs. Both a share and a per-km² version of every
  section are stored; the per-km² twin divides by an exactly-known denominator
  and degrades gracefully. Which to use is not yet settled.

By contrast the Census denominators are near-constant by construction — employed
residents per LSOA run 334–1,769 (median 844, CV 0.22) — which is why
residence-based shares are stable everywhere and workplace-based ones are not.

## Vintage

Census 2021 was taken **21 March 2021**, during a national lockdown, and is
three years older than the 2024/25 transport data. BRES 2024 and IoD 2025 are
much closer to it. State this in Chapter 3.

## OS Points of Interest facility layer

The formal variable set additionally uses **OS Points of Interest, June 2026**,
downloaded from EDINA Digimap on 7 August 2026. The licensed GeoPackage and its
source citation are retained under
`FYP/rq2_facility_diversity_analysis/data/source/` and are not duplicated here.

The pipeline validates 393,530 unique POI records in the downloaded rectangle
and assigns 329,993 of them to 4,988 of London's 4,994 LSOAs. Two formal
variables are derived:

* `log1p_poi_count`: natural-log transform of one plus total POI count;
* `shannon_group`: unnormalised Shannon diversity across the nine OS POI
  Groups, `H = -sum(p_i ln p_i)`.

For Bus these are direct LSOA values. For Rail, raw LSOA POI count and Shannon H
are averaged across the distinct LSOAs intersecting the established 800 m
Voronoi-clipped catchment; the mean count is then log-transformed. Both are
post-clustering area-context variables, not clustering inputs.
