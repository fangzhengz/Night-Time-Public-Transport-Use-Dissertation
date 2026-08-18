"""RAIL v2 candidate batch: produce full deliverables for several K so the
choice of K can be made with all evidence (profiles + signatures + maps + sil).

Features are the pruned behavioural set (redundant/dead features removed).
Primary model = KMeans on standardised features (best separability on v2).
For each (group, K): labels CSV, entry/exit temporal profiles, per-cluster
feature signature, spatial map, and silhouette.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
INP = ROOT / "outputs" / "preprocessed_numbat" / "numbat_lu_station_qhr_all_daytypes.parquet"
BASEMAP = ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
XY = {"weekday": ROOT/"outputs"/"lu_rail_2000_diag"/"weekday"/"weekday_k5_labels_xy.csv",
      "weekend": ROOT/"outputs"/"lu_rail_2000_diag"/"weekend"/"weekend_k6_labels_xy.csv"}
OUTD = ROOT / "outputs" / "lu_rail_2000_featv2" / "candidates"
OUTD.mkdir(parents=True, exist_ok=True)

START = 20*60
MIN_TOTAL = 50
RS = 42
WINDOW = {"MON": (START, 25*60, None), "TWT": (START, 25*60, None), "SUN": (START, 25*60, None),
          "FRI": (START, 30*60, "SAT"), "SAT": (START, 30*60, "SUN")}
GROUPS = {"weekday": ["MON", "TWT"], "weekend": ["FRI", "SAT", "SUN"]}
SPLIT = {"weekday": 23*60, "weekend": 24*60}
WIN_END = {"weekday": 25*60, "weekend": 30*60}
FEATS = {"weekday": ["A_net", "F_flip", "t_median", "persist_00", "hump_22"],
         "weekend": ["A_net", "F_flip", "t_median", "persist_00", "hump_22", "dawn"]}
CAND_K = {"weekday": [3, 4, 5], "weekend": [2, 3, 4, 5]}


def app_next(df, focal, nxt):
    e = df[(df["day_type"].astype(str) == nxt) & (df["hour"] >= 5) & (df["hour"] < 6)].copy()
    e["day_type"] = focal; e["extended_minute"] = e["hour"]*60 + e["minute"] + 24*60
    return e


def subset(df, dt):
    s, en, nx = WINDOW[dt]
    b = df[df["day_type"].astype(str) == dt].copy()
    b = b[(b["extended_minute"] >= s) & (b["extended_minute"] < min(en, 29*60))].copy()
    if en > 29*60:
        b = pd.concat([b, app_next(df, dt, nx)], ignore_index=True)
    return b


def ratio(num, den):
    return np.where(den > 0, num/den, 0.0)


def build(raw, days, split, win_end):
    long = pd.concat([subset(raw, dt) for dt in days], ignore_index=True)
    g = long.groupby(["NLC", "direction", "extended_minute"], as_index=False)["count"].sum()
    e = g[g["direction"] == "entry"].pivot_table("count", "NLC", "extended_minute", fill_value=0.0)
    x = g[g["direction"] == "exit"].pivot_table("count", "NLC", "extended_minute", fill_value=0.0)
    bins = sorted(set(e.columns) | set(x.columns))
    e = e.reindex(columns=bins, fill_value=0.0); x = x.reindex(columns=bins, fill_value=0.0)
    e, x = e.align(x, join="outer", fill_value=0.0)
    t = np.array(bins, dtype=float)
    tot = (e + x).sum(1); keep = tot[tot >= MIN_TOTAL].index
    e, x = e.loc[keep], x.loc[keep]
    a = e + x; A = a.sum(1)
    early = t < split; late = ~early
    e_e, x_e = e.loc[:, early].sum(1), x.loc[:, early].sum(1)
    e_l, x_l = e.loc[:, late].sum(1), x.loc[:, late].sum(1)
    share_t = a.div(A, axis=0).values
    cum = np.cumsum(share_t, axis=1); med_idx = (cum >= 0.5).argmax(axis=1)

    def at(minute):
        return share_t[:, int(np.argmin(np.abs(t - minute)))]
    feat = pd.DataFrame(index=e.index)
    feat["A_net"] = ratio((e-x).sum(1).values, A.values)
    Ae = ratio((e_e-x_e).values, (e_e+x_e).values); Al = ratio((e_l-x_l).values, (e_l+x_l).values)
    ok = ((e_e+x_e).values > 20) & ((e_l+x_l).values > 20)
    feat["F_flip"] = np.where(ok, Ae-Al, 0.0)
    feat["t_median"] = (t[med_idx]-START)/(win_end-START)
    pm = t >= 24*60; feat["persist_00"] = share_t[:, pm].sum(1) if pm.any() else 0.0
    feat["hump_22"] = (at(22*60)+at(22*60+30))/2 - (at(21*60)+at(24*60))/2
    dw = (t >= 28*60+30) & (t < 30*60); feat["dawn"] = share_t[:, dw].sum(1) if dw.any() else 0.0
    # per-direction shares for profiles
    es = e.div(e.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    xs = x.div(x.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    return feat, es, xs, t


def plot_profiles(es, xs, t, lab, group, K, dest):
    cls = sorted(pd.unique(lab))
    fig, axs = plt.subplots(len(cls), 1, figsize=(9, max(2*len(cls), 4)), squeeze=False, sharey=True)
    for ax, cl in zip(axs[:, 0], cls):
        m = lab == cl
        for arr, col, name in [(es, "#2F6B4F", "entry"), (xs, "#9A3D3D", "exit")]:
            sub = arr.loc[m]
            med = sub.median(0).values; p10 = sub.quantile(.1).values; p90 = sub.quantile(.9).values
            ax.plot(t, med, color=col, lw=1.5, marker="o", ms=3, label=name)
            ax.fill_between(t, p10, p90, color=col, alpha=.12, lw=0)
        ax.set_title(f"{group} C{cl} (n={int(m.sum())})", fontsize=9)
        cand = {1200: "20:00", 1380: "23:00", 1440: "00:00", 1620: "03:00", 1740: "05:00"}
        tk = [k for k in cand if t.min() <= k <= t.max()]
        ax.set_xticks(tk); ax.set_xticklabels([cand[k] for k in tk], fontsize=8)
        ax.grid(axis="y", color="#eee", lw=.6); ax.spines[["top", "right"]].set_visible(False)
    axs[0, 0].legend(fontsize=8)
    fig.suptitle(f"RAIL {group} v2 K={K} profiles", y=1.002); fig.tight_layout()
    fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_map(labels_xy, group, K, dest, base):
    gdf = gpd.GeoDataFrame(labels_xy, geometry=gpd.points_from_xy(labels_xy.easting, labels_xy.northing), crs=27700)
    cls = sorted(gdf["cluster"].unique())
    cmap = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    base.plot(ax=ax, color="#f2f2f2", edgecolor="#dcdcdc", linewidth=0.2)
    for i, cl in enumerate(cls):
        s = gdf[gdf.cluster == cl]
        ax.scatter(s.geometry.x, s.geometry.y, s=40, color=cmap(i), edgecolor="white",
                   linewidth=0.6, label=f"C{cl} (n={len(s)})", zorder=3)
    ax.set_title(f"RAIL {group} v2 K={K} cluster map"); ax.legend(loc="lower right", fontsize=9)
    ax.set_axis_off()
    minx, miny, maxx, maxy = gdf.total_bounds; pad = 3000
    ax.set_xlim(minx-pad, maxx+pad); ax.set_ylim(miny-pad, maxy+pad)
    fig.tight_layout(); fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    raw = pd.read_parquet(INP)
    raw["day_type"] = raw["day_type"].astype(str); raw["NLC"] = raw["NLC"].astype(str)
    base = gpd.read_file(BASEMAP).to_crs(27700)
    summary = []

    for group, days in GROUPS.items():
        feat_all, es, xs, t = build(raw, days, SPLIT[group], WIN_END[group])
        feat = feat_all[FEATS[group]]
        Xs = StandardScaler().fit_transform(feat.values)
        meta = pd.read_csv(XY[group], dtype={"NLC": str}).set_index("NLC")[["Station", "Fare Zone", "easting", "northing"]]

        for K in CAND_K[group]:
            gm = GaussianMixture(K, covariance_type="diag", n_init=20, reg_covar=1e-6, random_state=RS).fit(Xs)
            lab = gm.predict(Xs)
            post = gm.predict_proba(Xs)
            sil = silhouette_score(Xs, lab)
            labser = pd.Series(lab, index=feat.index, name="cluster")

            # labels + coords + names + GMM soft-assignment confidence
            out = feat.copy(); out["cluster"] = lab
            out["max_posterior"] = post.max(1)
            out["entropy"] = (-np.where(post > 0, post * np.log(post), 0.0).sum(1))
            out = out.join(meta)
            out.to_csv(OUTD / f"{group}_k{K}_labels.csv")

            # feature signature (mean per cluster)
            sig = out.groupby("cluster")[FEATS[group]].mean().round(3)
            sig["n"] = out.groupby("cluster").size()
            sig.to_csv(OUTD / f"{group}_k{K}_signature.csv")

            plot_profiles(es, xs, t, labser.values, group, K, OUTD / f"{group}_k{K}_profiles.png")
            plot_map(out.dropna(subset=["easting"]).reset_index(), group, K,
                     OUTD / f"{group}_k{K}_map.png", base)

            summary.append({"group": group, "K": K, "silhouette": round(sil, 3),
                            "sizes": sorted(np.bincount(lab).tolist(), reverse=True)})
            print(f"{group} K={K}: sil={sil:.3f} sizes={sorted(np.bincount(lab).tolist(),reverse=True)}")

    pd.DataFrame(summary).to_csv(OUTD / "candidate_summary.csv", index=False)
    print("\nSaved candidates ->", OUTD)


if __name__ == "__main__":
    main()
