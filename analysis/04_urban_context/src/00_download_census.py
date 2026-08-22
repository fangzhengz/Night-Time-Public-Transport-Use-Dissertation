"""Download every external table this folder needs, from the Nomis API.

Run once. Writes tidy per-LSOA files into ``data/``; ``01_build_variable_table.py``
picks each one up automatically if present and skips it cleanly if not.

Driven by ``config.DOWNLOAD_SPEC`` (Census 2021 tables) plus ``config.BRES_*``
(BRES 2024). Nothing about which cells to sum lives in this file -- change the
spec, not the code.

THREE TRAPS THIS SCRIPT GUARDS AGAINST, all hit for real while building it:

1. Silent truncation. Nomis caps an unauthenticated response at 25,000 rows and
   truncates WITHOUT error. The first attempt asked for `geography=TYPE151`
   (all ~35,000 LSOAs in England and Wales) and got back 5,000 alphabetically-
   first northern LSOAs and zero London ones, which looked like a filter bug.
   Fixed by requesting `<london>TYPE151` and paging regardless.

2. Silent suppression. TS060 (the 106-category industry table) returns a row
   for every London LSOA with OBS_VALUE empty and OBS_STATUS='Q' ("These
   figures are missing") -- disclosure control at LSOA granularity. Read as
   numbers those become zeros. `to_share` now raises if a whole table is empty.
   TS060A (19 categories, NM_2017_1) is the release that IS published at LSOA.

3. Wrong-level double counting. Several tables carry both headline categories
   ("Private rented") and their sub-breakdowns ("Private rented: Private
   landlord..."). Substring matching would sum both. Entries that need headline
   rows only set `"exact": True`.

CAVEATS FOR THE WRITE-UP
* Census 2021 was taken 21 March 2021, during a national lockdown, and is three
  years older than the 2024/25 transport data. Census counts are integers with
  cell-key perturbation (small +/-noise), not coarse rounding.
* BRES here is the OPEN ACCESS release, not the secure-access version BtC cites
  (UKDA-SN-7463). Open-access values are rounded to multiples of 5.
"""

from __future__ import annotations

import io
import re
import urllib.request

import geopandas as gpd
import pandas as pd

import config as C

BASE = "https://www.nomisweb.co.uk/api/v01/dataset"
TIMEOUT = 600
PAGE = 25_000
LONDON_REGION = "2013265927"


def fetch(dataset: str, dimension: str, cells: str | None = None) -> pd.DataFrame:
    """Paged download of one dataset, London LSOAs only."""
    offset = 0
    chunks: list[pd.DataFrame] = []
    while True:
        url = (
            f"{BASE}/{dataset}.data.csv?geography={LONDON_REGION}TYPE151"
            f"&measures=20100&select=GEOGRAPHY_CODE,{dimension}_NAME,OBS_VALUE"
            f"&RecordOffset={offset}&RecordLimit={PAGE}"
        )
        if cells:
            url += f"&{dimension}={cells}"
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            chunk = pd.read_csv(io.StringIO(response.read().decode("utf-8")))
        if chunk.empty:
            break
        chunks.append(chunk)
        if len(chunk) < PAGE:
            break
        offset += PAGE

    frame = pd.concat(chunks, ignore_index=True)
    frame.columns = ["lsoa", "category", "value"]
    return frame


def resolve(labels: list[str], available: list[str], exact: bool) -> list[str]:
    """Map spec labels onto real category names, failing loudly on ambiguity."""
    resolved = []
    for label in labels:
        if exact:
            hits = [c for c in available if c.strip() == label]
        else:
            hits = [c for c in available if label.lower() in c.lower()]
        if len(hits) != 1:
            raise RuntimeError(
                f"{label!r} matched {len(hits)} categories "
                f"(exact={exact}): {hits}\nAvailable: {available}"
            )
        resolved.append(hits[0])
    return resolved


def to_shares(frame: pd.DataFrame, spec: dict, keep: set[str]) -> pd.DataFrame:
    frame = frame.loc[frame["lsoa"].isin(keep)]
    if frame["value"].isna().all():
        raise RuntimeError(
            f"{spec['table']}: every observation is missing -- this table is "
            "disclosure-suppressed at LSOA level. Check OBS_STATUS before "
            "assuming the request was malformed."
        )
    wide = frame.pivot_table(index="lsoa", columns="category", values="value", aggfunc="sum")
    available = [str(c) for c in wide.columns]

    total_hits = [c for c in available if c.strip() == spec["total"]]
    if len(total_hits) != 1:
        raise RuntimeError(f"{spec['table']}: total {spec['total']!r} -> {total_hits}")
    denominator = wide[total_hits[0]].replace(0, pd.NA)

    out = pd.DataFrame(index=wide.index)
    for name, labels in spec["variables"].items():
        columns = resolve(labels, available, spec.get("exact", False))
        out[name] = wide[columns].sum(axis=1) / denominator
        print(f"    {name}: median={out[name].median():.4f}, "
              f"range {out[name].min():.4f}-{out[name].max():.4f}")
    return out.reset_index()


def download_census(keep: set[str]) -> None:
    for spec in C.DOWNLOAD_SPEC:
        print(f"\n{spec['table']} ({spec['dataset']}) -- {spec['note']}")
        frame = fetch(spec["dataset"], spec["dimension"])
        print(f"  {len(frame):,} rows, {frame['lsoa'].nunique():,} LSOAs, "
              f"{frame['category'].nunique()} categories")
        to_shares(frame, spec, keep).to_csv(spec["path"], index=False)
        print(f"  wrote {spec['path'].name}")

    # Full industry composition kept alongside the derived shares, so the
    # section selection can be revised without re-downloading.
    print("\nTS060A -- full 18-section composition (reference copy)")
    industry = fetch("NM_2017_1", "C2021_IND_19")
    industry = industry.loc[industry["lsoa"].isin(keep)]
    wide = industry.pivot_table(index="lsoa", columns="category", values="value", aggfunc="sum")
    total = next(c for c in wide.columns if str(c).strip().lower().startswith("total"))
    shares = wide.drop(columns=total).div(wide[total].replace(0, pd.NA), axis=0)
    shares.to_csv(C.CENSUS_DIR / "ts060_industry_section_shares_lsoa.csv")
    print(f"  wrote ts060_industry_section_shares_lsoa.csv ({shares.shape[1]} sections)")

    # Two residence-side aggregates split on the leisure-vs-labour axis. See
    # config.HOSPITALITY_SECTIONS / SHIFTWORK_SECTIONS for why these sections
    # and not others -- in short, membership of LNWC's survey-derived night
    # industry list plus a weekend-behaviour criterion that is independent of
    # the transport outcomes, so the split is not selected on its own result.
    available = [str(c) for c in shares.columns]
    out = pd.DataFrame({"lsoa": shares.index})
    for name, wanted in (("hospitality_industry_share", C.HOSPITALITY_SECTIONS),
                         ("shiftwork_industry_share", C.SHIFTWORK_SECTIONS)):
        missing = [w for w in wanted if w not in available]
        if missing:
            raise RuntimeError(f"{name}: sections not found {missing}\navailable: {available}")
        out[name] = shares[wanted].sum(axis=1).to_numpy()
        print(f"    {name}: median={out[name].median():.4f} "
              f"({len(wanted)} section{'s' if len(wanted) > 1 else ''})")
    out.to_csv(C.CENSUS_INDUSTRY, index=False)
    print(f"  wrote {C.CENSUS_INDUSTRY.name} (residence-side, leisure/labour split)")


def download_bres(keep: set[str], areas_km2: pd.Series) -> None:
    """BRES 2024 workplace employment, aggregated from SIC divisions to sections."""
    print(f"\nBRES 2024 ({C.BRES_DATASET}) -- workplace jobs, denominator = jobs in LSOA")
    with urllib.request.urlopen(
        f"{BASE}/{C.BRES_DATASET}/industry.def.sdmx.json", timeout=TIMEOUT
    ) as response:
        import json

        codelist = json.load(response)["structure"]["codelists"]["codelist"][0]["code"]

    division_code = {}
    for entry in codelist:
        match = re.match(r"^(\d{2})\s*:", entry["description"]["value"].strip())
        if match:
            division_code[int(match.group(1))] = str(entry["value"])

    owner, cells = {}, []
    for section, divisions in C.BRES_SECTIONS.items():
        missing = [d for d in divisions if d not in division_code]
        if missing:
            raise RuntimeError(f"BRES section {section}: divisions {missing} absent")
        for division in divisions:
            cells.append(division_code[division])
            owner[division_code[division]] = section
    total_code = "37748736"
    cells.append(total_code)
    owner[total_code] = "total_jobs"
    print(f"  requesting {len(cells)} industry cells x {len(keep):,} LSOAs")

    offset, chunks = 0, []
    while True:
        url = (
            f"{BASE}/{C.BRES_DATASET}.data.csv?geography={LONDON_REGION}TYPE151"
            f"&date=latest&industry={','.join(cells)}&employment_status=1&measure=1"
            f"&measures=20100&select=GEOGRAPHY_CODE,INDUSTRY,OBS_VALUE"
            f"&RecordOffset={offset}&RecordLimit={PAGE}"
        )
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            chunk = pd.read_csv(io.StringIO(response.read().decode("utf-8")))
        if chunk.empty:
            break
        chunks.append(chunk)
        if len(chunk) < PAGE:
            break
        offset += PAGE

    frame = pd.concat(chunks, ignore_index=True)
    frame.columns = ["lsoa", "industry", "value"]
    frame["section"] = frame["industry"].astype(str).map(owner)
    frame = frame.loc[frame["lsoa"].isin(keep)]
    wide = frame.pivot_table(index="lsoa", columns="section", values="value",
                             aggfunc="sum").fillna(0.0)

    out = pd.DataFrame(index=wide.index)
    out["bres_total_jobs"] = wide["total_jobs"]
    denominator = wide["total_jobs"].replace(0, pd.NA)
    area = areas_km2.reindex(wide.index)
    for section in C.BRES_SECTIONS:
        # Both denominators, because the choice is still open: the share is
        # unstable where total jobs is small (40% of LSOAs are under 250 jobs),
        # while jobs/km2 uses a denominator that is exactly known everywhere.
        out[f"bres_{section}_share"] = wide[section] / denominator
        out[f"bres_{section}_per_km2"] = wide[section] / area

    print(f"  London total jobs {wide['total_jobs'].sum():,.0f}; "
          f"jobs per LSOA median {wide['total_jobs'].median():,.0f}")
    for section in C.BRES_SECTIONS:
        print(f"    {section:20} {wide[section].sum() / wide['total_jobs'].sum():6.2%} of jobs")
    out.reset_index().to_csv(C.BRES_INDUSTRY, index=False)
    print(f"  wrote {C.BRES_INDUSTRY.name}")


def main() -> None:
    boundaries = gpd.read_file(C.LSOA_BOUNDARIES).to_crs(C.CRS_BNG)
    boundaries = boundaries.rename(columns={C.LSOA_BOUNDARY_CODE_COLUMN: "lsoa"})
    keep = set(boundaries["lsoa"].astype(str))
    areas = (boundaries.set_index("lsoa").geometry.area / 1e6).rename("area_km2")
    print(f"Filtering to {len(keep):,} London LSOAs from the project boundary file.")

    download_census(keep)
    download_bres(keep, areas)
    print("\nDone.")


if __name__ == "__main__":
    main()
