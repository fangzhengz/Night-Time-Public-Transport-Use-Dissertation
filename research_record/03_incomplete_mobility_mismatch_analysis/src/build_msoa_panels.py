"""Build MSOA-level night-window panels: observed PT usage vs. OD movement.

Aggregates NUMBAT (rail) and BUSTO (bus) night-window, weekday-representative
usage up to MSOA11 (to match the OD flow data's 2011 MSOA keys), and
separately aggregates the OD flow data to the same geography. Writes the
per-MSOA totals both directions need for the mismatch regression in
run_mismatch_analysis.py.

Does not touch any RQ1/RQ2 input or output. See ../README.md.
"""

import logging

import geopandas as gpd
import pandas as pd

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def load_lsoa_to_msoa11() -> pd.DataFrame:
    df = pd.read_csv(config.MSOA_LOOKUP, usecols=["LSOA21CD", "MSOA11CD"])
    return df.dropna(subset=["MSOA11CD"])


def build_rail_station_to_msoa11(lsoa_to_msoa11: pd.DataFrame) -> pd.DataFrame:
    """Point-in-polygon: rail station lon/lat -> containing LSOA21 -> MSOA11."""
    coords = pd.read_csv(config.RAIL_COORDS).rename(columns={"unit": "NLC"})
    stations = gpd.GeoDataFrame(
        coords,
        geometry=gpd.points_from_xy(coords["lon"], coords["lat"]),
        crs="EPSG:4326",
    )
    lsoa = gpd.read_file(config.LSOA_BOUNDARIES)[["LSOA21CD", "geometry"]]

    joined = gpd.sjoin(stations, lsoa, how="left", predicate="within")
    n_total = len(joined)
    n_unmatched = int(joined["LSOA21CD"].isna().sum())
    log.info("Rail: %d/%d stations matched to a containing LSOA21 polygon (%d unmatched)",
             n_total - n_unmatched, n_total, n_unmatched)
    if n_unmatched:
        log.warning("Unmatched rail NLCs (outside all LSOA21 polygons): %s",
                    joined.loc[joined["LSOA21CD"].isna(), "NLC"].tolist())

    joined = joined.drop(columns="geometry").merge(lsoa_to_msoa11, on="LSOA21CD", how="left")
    n_no_msoa = int(joined["MSOA11CD"].isna().sum())
    if n_no_msoa:
        log.warning("%d rail stations matched an LSOA21 with no MSOA11 mapping", n_no_msoa)

    joined["NLC"] = joined["NLC"].astype(str)
    return joined[["NLC", "LSOA21CD", "MSOA11CD"]]


def build_bus_lsoa_to_msoa11(lsoa_to_msoa11: pd.DataFrame) -> pd.DataFrame:
    """BUS_LSOA_HOURLY is already at LSOA grain (the StopArea -> LSOA
    aggregation happens upstream, in data_processing/bus_stoparea/), so this
    is just the LSOA21 -> MSOA11 lookup -- no stop-level step any more."""
    lsoa = pd.read_parquet(config.BUS_LSOA_HOURLY, columns=["lsoa"]).drop_duplicates()
    lsoa = lsoa.rename(columns={"lsoa": "LSOA21CD"})
    merged = lsoa.merge(lsoa_to_msoa11, on="LSOA21CD", how="left")
    n_no_msoa = int(merged["MSOA11CD"].isna().sum())
    log.info("Bus: %d/%d source LSOAs matched to MSOA11 (%d unmatched)",
             len(merged) - n_no_msoa, len(merged), n_no_msoa)
    return merged[["LSOA21CD", "MSOA11CD"]]


def aggregate_rail(station_to_msoa11: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    numbat = pd.read_parquet(config.RAIL_QHR)
    numbat = numbat[
        (numbat["day_type"] == config.RAIL_DAY_TYPE)
        & (numbat["hour"].isin(config.NIGHT_HOURS))
    ].copy()
    numbat["NLC"] = numbat["NLC"].astype(str)
    n_before = numbat["NLC"].nunique()
    numbat = numbat.merge(station_to_msoa11, on="NLC", how="inner")
    numbat = numbat.dropna(subset=["MSOA11CD"])
    n_after = numbat["NLC"].nunique()
    log.info("Rail %s night-window rows: %d stations before MSOA join, %d retained after dropping unmapped stations",
              config.RAIL_DAY_TYPE, n_before, n_after)

    hourly = (
        numbat.groupby(["MSOA11CD", "hour", "direction"], observed=True)["count"]
        .sum()
        .reset_index()
        .pivot_table(index=["MSOA11CD", "hour"], columns="direction", values="count", fill_value=0.0)
        .reset_index()
        .rename(columns={"entry": "rail_entry", "exit": "rail_exit"})
    )
    totals = (
        numbat.groupby(["MSOA11CD", "direction"], observed=True)["count"]
        .sum()
        .reset_index()
        .pivot_table(index="MSOA11CD", columns="direction", values="count", fill_value=0.0)
        .reset_index()
        .rename(columns={"entry": "rail_entry_total", "exit": "rail_exit_total"})
    )
    return hourly, totals


def aggregate_bus(lsoa_to_msoa11_bus: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """BUS_LSOA_HOURLY schema: day_type (Weekday/Saturday/Sunday), direction
    (boardings/alightings), lsoa, hour_bin (extended minutes, e.g. 1080 =
    18:00, wrapping past 1440 for post-midnight hours), count. hour_bin needs
    converting to an actual clock hour (0-23) before the NIGHT_HOURS filter,
    which is defined in clock-hour terms to match rail's "hour" column."""
    busto = pd.read_parquet(config.BUS_LSOA_HOURLY)
    busto["hour"] = (busto["hour_bin"] // 60) % 24
    busto = busto[
        (busto["day_type"] == config.BUS_DAY_TYPE)
        & (busto["hour"].isin(config.NIGHT_HOURS))
    ].copy()
    busto = busto.rename(columns={"lsoa": "LSOA21CD"})
    n_before = busto["LSOA21CD"].nunique()
    busto = busto.merge(lsoa_to_msoa11_bus, on="LSOA21CD", how="inner")
    busto = busto.dropna(subset=["MSOA11CD"])
    n_after = busto["LSOA21CD"].nunique()
    log.info(
        "Bus %s night-window rows: %d LSOAs before MSOA join, %d retained "
        "(%d LSOAs dropped, no MSOA11 mapping)",
        config.BUS_DAY_TYPE, n_before, n_after, n_before - n_after,
    )

    hourly = (
        busto.groupby(["MSOA11CD", "hour", "direction"], observed=True)["count"]
        .sum()
        .reset_index()
        .pivot_table(index=["MSOA11CD", "hour"], columns="direction", values="count", fill_value=0.0)
        .reset_index()
        .rename(columns={"boardings": "bus_boarding", "alightings": "bus_alighting"})
    )
    totals = (
        busto.groupby(["MSOA11CD", "direction"], observed=True)["count"]
        .sum()
        .reset_index()
        .pivot_table(index="MSOA11CD", columns="direction", values="count", fill_value=0.0)
        .reset_index()
        .rename(columns={"boardings": "bus_boarding_total", "alightings": "bus_alighting_total"})
    )
    return hourly, totals


def aggregate_od() -> tuple[pd.DataFrame, pd.DataFrame]:
    od = pd.read_csv(config.OD_FLOWS)
    night = od[od["hour"].isin(config.NIGHT_HOURS)]
    log.info("OD flows: %d/%d rows fall in the night window", len(night), len(od))

    origin = night.groupby("origin_msoa11cd")["flow_sum"].sum().rename("od_origin_total")
    destination = night.groupby("destination_msoa11cd")["flow_sum"].sum().rename("od_destination_total")
    totals = pd.concat([origin, destination], axis=1).reset_index().rename(
        columns={"index": "MSOA11CD"}
    )
    totals = totals.rename(columns={totals.columns[0]: "MSOA11CD"})

    origin_hourly = night.groupby(["origin_msoa11cd", "hour"])["flow_sum"].sum().rename("od_origin").reset_index().rename(columns={"origin_msoa11cd": "MSOA11CD"})
    destination_hourly = night.groupby(["destination_msoa11cd", "hour"])["flow_sum"].sum().rename("od_destination").reset_index().rename(columns={"destination_msoa11cd": "MSOA11CD"})
    hourly = origin_hourly.merge(destination_hourly, on=["MSOA11CD", "hour"], how="outer").fillna(0.0)

    return totals.fillna(0.0), hourly


def main() -> None:
    lsoa_to_msoa11 = load_lsoa_to_msoa11()

    station_to_msoa11 = build_rail_station_to_msoa11(lsoa_to_msoa11)
    lsoa_to_msoa11_bus = build_bus_lsoa_to_msoa11(lsoa_to_msoa11)

    rail_hourly, rail_totals = aggregate_rail(station_to_msoa11)
    bus_hourly, bus_totals = aggregate_bus(lsoa_to_msoa11_bus)
    od_totals, od_hourly = aggregate_od()

    hourly = rail_hourly.merge(bus_hourly, on=["MSOA11CD", "hour"], how="outer").fillna(0.0)
    hourly.to_csv(config.DATA_OUT / "msoa_pt_panel_hourly.csv", index=False)
    log.info("Wrote msoa_pt_panel_hourly.csv (%d rows, %d MSOAs)",
              len(hourly), hourly["MSOA11CD"].nunique())

    od_hourly.to_csv(config.DATA_OUT / "msoa_od_panel_hourly.csv", index=False)
    log.info("Wrote msoa_od_panel_hourly.csv (%d rows, %d MSOAs)",
              len(od_hourly), od_hourly["MSOA11CD"].nunique())

    pt_totals = rail_totals.merge(bus_totals, on="MSOA11CD", how="outer").fillna(0.0)
    for col in ("rail_entry_total", "rail_exit_total", "bus_boarding_total", "bus_alighting_total"):
        if col not in pt_totals.columns:
            pt_totals[col] = 0.0
    pt_totals["origin_total"] = pt_totals["rail_entry_total"] + pt_totals["bus_boarding_total"]
    pt_totals["destination_total"] = pt_totals["rail_exit_total"] + pt_totals["bus_alighting_total"]
    pt_totals.to_csv(config.DATA_OUT / "msoa_pt_totals.csv", index=False)
    log.info("Wrote msoa_pt_totals.csv (%d MSOAs with any PT coverage)", len(pt_totals))

    od_totals.to_csv(config.DATA_OUT / "msoa_od_totals.csv", index=False)
    log.info("Wrote msoa_od_totals.csv (%d MSOAs with any OD coverage)", len(od_totals))

    merged = pt_totals.merge(od_totals, on="MSOA11CD", how="outer")
    n_both = int(merged[["origin_total", "od_origin_total"]].notna().all(axis=1).sum())
    n_pt_only = int(merged["od_origin_total"].isna().sum())
    n_od_only = int(merged["origin_total"].isna().sum())
    log.info(
        "Coverage: %d MSOAs have both PT and OD data, %d PT-only (no OD match), %d OD-only (no PT match)",
        n_both, n_pt_only, n_od_only,
    )

    audit_path = config.DATA_OUT / "data_audit.txt"
    audit_path.write_text(
        f"Rail day-type used: {config.RAIL_DAY_TYPE}\n"
        f"Bus day-type used: {config.BUS_DAY_TYPE}\n"
        f"Night hours: {config.NIGHT_HOURS}\n"
        f"Rail stations matched to MSOA11: {station_to_msoa11['MSOA11CD'].notna().sum()}/{len(station_to_msoa11)}\n"
        f"Bus source LSOAs matched to MSOA11: {lsoa_to_msoa11_bus['MSOA11CD'].notna().sum()}/{len(lsoa_to_msoa11_bus)}\n"
        f"MSOAs with both PT and OD coverage: {n_both}\n"
        f"MSOAs with PT but no OD coverage: {n_pt_only}\n"
        f"MSOAs with OD but no PT coverage (no station/stop in that MSOA at all): {n_od_only}\n",
        encoding="utf-8",
    )
    log.info("Wrote %s", audit_path)


if __name__ == "__main__":
    main()
