"""Aggregate OA-level LOAC Supergroups up to LSOA level.

OA nests exactly inside LSOA (no spatial overlap ambiguity, unlike the rail
catchment case), so this is a plain table join followed by a groupby --
no area-weighting is needed here. For each LSOA we keep:
  - the modal Supergroup across its constituent OAs (primary; mirrors how
    bus currently joins LNWC directly as a single category per LSOA)
  - the fractional Supergroup composition (share of OAs per Supergroup;
    secondary/diagnostic, parallels LNWC's rail-side composition view)

Writes ``data/loac_lsoa_supergroup.csv``. Read-only on all of its inputs.
"""

from __future__ import annotations

import pandas as pd

from config import LOAC_LOOKUP, LOAC_SUPERGROUPS, OA_LSOA_LOOKUP, ROOT

OUT_PATH = ROOT / "data" / "loac_lsoa_supergroup.csv"


def modal_supergroup(shares: pd.Series) -> str:
    """Return the Supergroup with the largest share; ties broken alphabetically."""
    top = shares[shares == shares.max()].index
    return sorted(top)[0]


def main() -> None:
    loac = pd.read_csv(LOAC_LOOKUP).rename(columns={"OA": "OA21CD"})
    if set(loac["SG"].unique()) - set(LOAC_SUPERGROUPS):
        raise ValueError(
            f"Unexpected LOAC Supergroup values: {set(loac['SG'].unique()) - set(LOAC_SUPERGROUPS)}"
        )

    oa_lsoa = pd.read_csv(OA_LSOA_LOOKUP)[["OA21CD", "LSOA21CD"]]

    merged = loac.merge(oa_lsoa, on="OA21CD", how="left", validate="one_to_one")
    unmatched = merged["LSOA21CD"].isna().sum()
    if unmatched:
        raise ValueError(
            f"{unmatched} of {len(merged)} LOAC OAs did not match the OA21->LSOA21 "
            "lookup -- check vintage/extent alignment before proceeding."
        )

    counts = (
        merged.groupby(["LSOA21CD", "SG"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=LOAC_SUPERGROUPS, fill_value=0)
    )
    shares = counts.div(counts.sum(axis=1), axis=0)
    shares.columns = [f"loac_{sg}_share" for sg in LOAC_SUPERGROUPS]

    dominant = counts.apply(modal_supergroup, axis=1).rename("loac_dominant_supergroup")
    n_oas = counts.sum(axis=1).rename("n_oas")

    out = pd.concat([n_oas, dominant, shares], axis=1).reset_index()

    share_cols = [c for c in out.columns if c.startswith("loac_") and c.endswith("_share")]
    share_sums = out[share_cols].sum(axis=1)
    if not (share_sums.sub(1.0).abs() < 1e-9).all():
        raise AssertionError("LOAC Supergroup shares do not sum to one for every LSOA")

    out.to_csv(OUT_PATH, index=False)
    print(
        f"Wrote {len(out)} LSOAs to {OUT_PATH} "
        f"(from {len(merged)} OAs, {merged['LSOA21CD'].nunique()} unique LSOAs)."
    )


if __name__ == "__main__":
    main()
