"""Fetch the ONS LSOA(2021)->MSOA(2021)->LAD(2022) lookup, London subset only.

One-off script. Writes a small, versioned CSV to ../data/ so the rest of the
pipeline does not depend on network access on every run. Re-run manually if
the ONS source is ever updated.

Source: see config.ONS_SOURCE_NOTE.
"""

import logging

import pandas as pd
import requests

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def london_lad_codes() -> list[str]:
    df = pd.read_csv(config.LONDON_LAD_LOOKUP)
    codes = sorted(df["LAD22CD"].unique().tolist())
    log.info("Loaded %d London LAD22CD codes from %s", len(codes), config.LONDON_LAD_LOOKUP)
    return codes


def _paginate(service_url: str, where: str, out_fields: str) -> pd.DataFrame:
    page_size = 1000
    offset = 0
    frames = []
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        resp = requests.get(service_url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        if "error" in payload:
            raise RuntimeError(f"ArcGIS query error: {payload['error']}")
        features = payload.get("features", [])
        if not features:
            break
        frames.append(pd.DataFrame([f["attributes"] for f in features]))
        log.info("Fetched %d rows (offset=%d) from %s", len(features), offset, service_url.split("/services/")[1].split("/")[0])
        offset += len(features)
        if len(features) < page_size:
            break
    if not frames:
        raise RuntimeError(f"No rows returned from {service_url}")
    return pd.concat(frames, ignore_index=True)


def fetch_oa_level(lad_codes: list[str]) -> pd.DataFrame:
    where = "LAD22CD IN ({})".format(",".join(f"'{c}'" for c in lad_codes))
    out_fields = "OA21CD,LSOA21CD,MSOA21CD,LAD22CD,LAD22NM"
    return _paginate(config.ONS_OA_LSOA_MSOA_LAD_SERVICE, where, out_fields)


def fetch_msoa11_msoa21_crosswalk(lad_codes: list[str]) -> pd.DataFrame:
    where = "LAD22CD IN ({})".format(",".join(f"'{c}'" for c in lad_codes))
    out_fields = "MSOA11CD,MSOA21CD,CHNGIND,LAD22CD"
    return _paginate(config.ONS_MSOA11_MSOA21_SERVICE, where, out_fields)


def main() -> None:
    lad_codes = london_lad_codes()

    oa_level = fetch_oa_level(lad_codes)
    log.info("Total OA-level rows fetched: %d", len(oa_level))

    lsoa_level = (
        oa_level[["LSOA21CD", "MSOA21CD", "LAD22CD", "LAD22NM"]]
        .drop_duplicates(subset=["LSOA21CD"])
        .sort_values("LSOA21CD")
        .reset_index(drop=True)
    )
    n_lsoa = lsoa_level["LSOA21CD"].nunique()
    n_msoa21 = lsoa_level["MSOA21CD"].nunique()
    log.info("De-duplicated to %d unique LSOA21CD across %d unique MSOA21CD", n_lsoa, n_msoa21)
    assert lsoa_level["LSOA21CD"].is_unique, "Expected exactly one MSOA21 per LSOA21"

    # OD flows are keyed by 2011 MSOA codes -- add an MSOA11CD column so the
    # rest of the pipeline can join straight to the OD data without a second
    # lookup at analysis time.
    crosswalk = fetch_msoa11_msoa21_crosswalk(lad_codes)
    log.info("Fetched %d MSOA11<->MSOA21 crosswalk rows", len(crosswalk))

    dup_msoa21 = crosswalk.groupby("MSOA21CD").size()
    n_ambiguous = int((dup_msoa21 > 1).sum())
    log.info(
        "%d of %d London MSOA21 codes map to more than one MSOA11 code (split/merge cases)",
        n_ambiguous, dup_msoa21.shape[0],
    )
    # Keep first match per MSOA21CD for the primary lookup; ambiguous cases
    # are logged (not silently resolved) via the audit file below.
    crosswalk_primary = (
        crosswalk.sort_values(["MSOA21CD", "CHNGIND"])
        .drop_duplicates(subset=["MSOA21CD"], keep="first")[["MSOA21CD", "MSOA11CD", "CHNGIND"]]
    )

    lsoa_level = lsoa_level.merge(crosswalk_primary, on="MSOA21CD", how="left")
    n_missing_msoa11 = int(lsoa_level["MSOA11CD"].isna().sum())
    log.info("%d/%d LSOA21 rows have no MSOA11CD match (LADs outside the crosswalk query)", n_missing_msoa11, len(lsoa_level))

    lsoa_level.to_csv(config.MSOA_LOOKUP, index=False)
    log.info("Wrote %s (%d rows)", config.MSOA_LOOKUP, len(lsoa_level))

    # Audit: how well does this lookup's MSOA11CD set actually cover the OD
    # flow data's MSOA11 universe? (see README "Design decisions" / caveats)
    od = pd.read_csv(config.OD_FLOWS, usecols=["origin_msoa11cd", "destination_msoa11cd"])
    od_msoa11 = set(od["origin_msoa11cd"]) | set(od["destination_msoa11cd"])
    lookup_msoa11 = set(lsoa_level["MSOA11CD"].dropna())
    overlap = od_msoa11 & lookup_msoa11
    log.info(
        "OD MSOA11 universe: %d unique. Overlap with this lookup: %d (%.1f%%). "
        "In OD but unmatched: %d.",
        len(od_msoa11), len(overlap), 100 * len(overlap) / len(od_msoa11),
        len(od_msoa11 - lookup_msoa11),
    )

    audit_path = config.DATA_DIR / "msoa_lookup_audit.txt"
    audit_path.write_text(
        f"OA-level rows fetched: {len(oa_level)}\n"
        f"Unique LSOA21CD: {n_lsoa}\n"
        f"Unique MSOA21CD: {n_msoa21}\n"
        f"MSOA21 codes with ambiguous (split/merge) MSOA11 match: {n_ambiguous}/{dup_msoa21.shape[0]}\n"
        f"LSOA21 rows with no MSOA11CD match: {n_missing_msoa11}/{len(lsoa_level)}\n"
        f"OD flow data MSOA11 universe: {len(od_msoa11)} unique codes\n"
        f"Overlap between OD MSOA11 universe and this lookup's MSOA11CD set: "
        f"{len(overlap)} ({100 * len(overlap) / len(od_msoa11):.1f}%)\n"
        f"OD MSOA11 codes with no match in this lookup: {sorted(od_msoa11 - lookup_msoa11)}\n",
        encoding="utf-8",
    )
    log.info("Wrote audit note to %s", audit_path)


if __name__ == "__main__":
    main()
