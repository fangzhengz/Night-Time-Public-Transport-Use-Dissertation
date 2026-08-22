# -*- coding: utf-8 -*-
"""Back-fill K-selection evidence for the raw-share FINAL runs.

The two raw-share/BtC-lineage runs `lu_rail_FINAL_diag` and
`busto_lsoa_FINAL_gmm_hourly` shipped labels/profiles for a single hard-picked
K but lacked a proper K-diagnostic chart, so the choice of K was unjustified.

This script reads the *exact* feature matrices those runs clustered on
(`*_X.parquet` / `X_*.parquet`, already per-vector normalised raw shares) and,
for rail (weekday/weekend) and bus (weekday/weekend):

  1. K-diagnostics over K=2..15 on the GMM(diag) primary model:
     silhouette (GMM/KMeans/Ward cross-model), Calinski-Harabasz, Davies-Bouldin,
     BIC, and bootstrap GMM stability (mean ARI +/- sd). -> CSV + 2x3 panel PNG.
  2. Per-K candidate deliverables (GMM diag): labels, cluster sizes, and
     temporal entry/exit (rail) or boardings/alightings (bus) profile plots.
  3. Spatial outputs: rail point map (coords joined by NLC from the v1 xy file);
     bus LSOA choropleth.

Faithful to the raw-share approach: NO StandardScaler on the simplex shares
(per PROJECT_CONTEXT s13.9). Reproduction is sanity-checked by ARI against the
existing FINAL labels.
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score, adjusted_rand_score)

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
OUT = ROOT / "outputs"
BASEMAP = ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
XY = {"weekday": OUT/"lu_rail_2000_diag"/"weekday"/"weekday_k5_labels_xy.csv",
      "weekend": OUT/"lu_rail_2000_diag"/"weekend"/"weekend_k6_labels_xy.csv"}
RS = 42
KR = list(range(2, 16))
PURPLE, GREEN, RED, GOLD = "#500778", "#2F6B4F", "#9A3D3D", "#C89B3C"

# (label, X path, index name, existing-labels glob for ARI check, candidate Ks)
RAIL_JOBS = {
    "weekday": dict(X=OUT/"lu_rail_FINAL_diag"/"weekday"/"weekday_X.parquet",
                    ref=OUT/"lu_rail_FINAL_diag"/"weekday"/"weekday_FINAL_k7_labels.csv",
                    cand=[4, 5, 6, 7]),
    "weekend": dict(X=OUT/"lu_rail_FINAL_diag"/"weekend"/"weekend_X.parquet",
                    ref=OUT/"lu_rail_FINAL_diag"/"weekend"/"weekend_FINAL_k8_labels.csv",
                    cand=[5, 6, 7, 8]),
}
BUS_JOBS = {
    "weekday": dict(X=OUT/"busto_lsoa_FINAL_gmm_hourly"/"weekday"/"X_weekday.parquet",
                    ref=OUT/"busto_lsoa_FINAL_gmm_hourly"/"weekday"/"weekday_k4_labels.csv",
                    cand=[3, 4, 5, 6]),
    "weekend": dict(X=OUT/"busto_lsoa_FINAL_gmm_hourly"/"weekend"/"X_weekend.parquet",
                    ref=OUT/"busto_lsoa_FINAL_gmm_hourly"/"weekend"/"weekend_k4_labels.csv",
                    cand=[3, 4, 5, 6]),
}


def gmm(k, X):
    return GaussianMixture(k, covariance_type="diag", n_init=20, reg_covar=1e-6,
                           random_state=RS).fit(X)


def diagnostics(X):
    n = len(X)
    ss = min(2000, n)
    rng = np.random.default_rng(RS)
    rows = []
    for k in KR:
        g = gmm(k, X); lg = g.predict(X)
        lk = KMeans(k, n_init=10, random_state=RS).fit_predict(X)
        lw = AgglomerativeClustering(k, linkage="ward").fit_predict(X)
        sil = lambda l: silhouette_score(X, l, sample_size=ss, random_state=RS)
        aris = []
        for _ in range(15):
            idx = rng.choice(n, n, replace=True)
            g2 = GaussianMixture(k, covariance_type="diag", n_init=3, reg_covar=1e-6,
                                 random_state=int(rng.integers(1e6))).fit(X[idx])
            aris.append(adjusted_rand_score(lg, g2.predict(X)))
        rows.append(dict(K=k, BIC=g.bic(X), GMM_sil=sil(lg), KM_sil=sil(lk),
                         Ward_sil=sil(lw), CH=calinski_harabasz_score(X, lg),
                         DB=davies_bouldin_score(X, lg), ARI=np.mean(aris),
                         ARI_sd=np.std(aris)))
    return pd.DataFrame(rows)


def plot_kdiag(d, title, dest):
    fig, ax = plt.subplots(2, 3, figsize=(14, 8))
    K = d.K
    a = ax[0, 0]
    a.plot(K, d.GMM_sil, "-o", color=PURPLE, label="GMM")
    a.plot(K, d.KM_sil, "-s", color=GREEN, label="KMeans")
    a.plot(K, d.Ward_sil, "-^", color=RED, label="Ward")
    a.set_title("Silhouette (higher = better)"); a.legend(fontsize=8)
    ax[0, 1].plot(K, d.CH, "-o", color=GREEN); ax[0, 1].set_title("Calinski-Harabasz (higher = better)")
    ax[0, 2].plot(K, d.DB, "-o", color=RED); ax[0, 2].set_title("Davies-Bouldin (lower = better)")
    ax[1, 0].plot(K, d.BIC, "-o", color=PURPLE); ax[1, 0].set_title("BIC (lower = better, GMM)")
    a = ax[1, 1]; a.errorbar(K, d.ARI, yerr=d.ARI_sd, fmt="-o", color=PURPLE, capsize=3)
    a.set_title("Bootstrap GMM stability ARI (higher = better)"); a.set_ylim(0, 1.02)
    ax[1, 2].axis("off")
    for row in ax:
        for a in row:
            if a.has_data():
                a.set_xlabel("K"); a.set_xticks(KR); a.grid(color="#eee", lw=.6)
                a.spines[["top", "right"]].set_visible(False)
    fig.suptitle(title, fontsize=14, y=1.0)
    fig.tight_layout(); fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def parse_cols(cols):
    """Return DataFrame[col, direction, minute] for raw-share feature columns."""
    recs = []
    for c in cols:
        parts = c.split("_")
        direction = parts[1]
        binlabel = parts[-1]  # last token; tolerates the optional 'next' marker
        if "-" in binlabel:  # rail HHMM-HHMM label
            hh, mm = int(binlabel[:2]), int(binlabel[2:4])
            minute = hh * 60 + mm + (1440 if hh < 12 else 0)
        else:                # bus extended minute integer
            minute = int(binlabel)
        recs.append((c, direction, minute))
    return pd.DataFrame(recs, columns=["col", "direction", "minute"])


def dir_curve(Xdf, cmap, direction):
    """units x minute matrix: mean share across day-types for one direction."""
    sub = cmap[cmap.direction == direction]
    out = {}
    for minute, g in sub.groupby("minute"):
        out[minute] = Xdf[g.col.tolist()].mean(axis=1)
    m = pd.DataFrame(out)
    return m.reindex(sorted(m.columns), axis=1)


def plot_profiles(Xdf, labels, cmap, dirs, title, dest):
    cls = sorted(pd.unique(labels))
    curves = {d: dir_curve(Xdf, cmap, d) for d, _, _ in dirs}
    fig, axs = plt.subplots(len(cls), 1, figsize=(9, max(2 * len(cls), 4)),
                            squeeze=False, sharey=True)
    for ax, cl in zip(axs[:, 0], cls):
        m = labels == cl
        for d, col, nm in dirs:
            cm = curves[d]
            t = np.array(cm.columns, float)
            sub = cm.loc[m]
            ax.plot(t, sub.median(0).values, color=col, lw=1.5, marker="o", ms=3, label=nm)
            ax.fill_between(t, sub.quantile(.1).values, sub.quantile(.9).values,
                            color=col, alpha=.12, lw=0)
        ax.set_title(f"C{cl} (n={int(m.sum())})", fontsize=9)
        cand = {1080: "18:00", 1200: "20:00", 1380: "23:00", 1440: "00:00",
                1620: "03:00", 1800: "06:00"}
        tmin, tmax = min(t.min() for t in [np.array(c.columns, float) for c in curves.values()]), \
                     max(t.max() for t in [np.array(c.columns, float) for c in curves.values()])
        tk = [k for k in cand if tmin <= k <= tmax]
        ax.set_xticks(tk); ax.set_xticklabels([cand[k] for k in tk], fontsize=8)
        ax.grid(axis="y", color="#eee", lw=.6); ax.spines[["top", "right"]].set_visible(False)
    axs[0, 0].legend(fontsize=8)
    fig.suptitle(title, y=1.002); fig.tight_layout()
    fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def rail_map(labels, idx, group, K, dest, base):
    xy = pd.read_csv(XY[group], dtype={"NLC": str}).set_index("NLC")
    df = pd.DataFrame({"cluster": labels}, index=idx.astype(str)).join(
        xy[["easting", "northing", "Station"]]).dropna(subset=["easting"])
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.easting, df.northing), crs=27700)
    cls = sorted(gdf.cluster.unique())
    cmap = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    for i, cl in enumerate(cls):
        s = gdf[gdf.cluster == cl]
        ax.scatter(s.geometry.x, s.geometry.y, s=42, color=cmap(i), edgecolor="white",
                   linewidth=0.6, label=f"C{cl} (n={len(s)})", zorder=3)
    ax.set_title(f"RAIL {group} FINAL (raw-share GMM) K={K} — station clusters")
    ax.legend(loc="lower right", fontsize=9); ax.set_axis_off()
    minx, miny, maxx, maxy = gdf.total_bounds; pad = 3000
    ax.set_xlim(minx - pad, maxx + pad); ax.set_ylim(miny - pad, maxy + pad)
    fig.tight_layout(); fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)
    return len(gdf), df["Station"].isna().sum() if "Station" in df else 0


def bus_map(labels, idx, group, K, dest, base):
    df = pd.DataFrame({"LSOA21CD": idx.astype(str), "cluster": labels})
    g = base.merge(df, on="LSOA21CD", how="left")
    fig, ax = plt.subplots(figsize=(10, 10))
    g[g.cluster.isna()].plot(ax=ax, color="#efefef", edgecolor="#e2e2e2", linewidth=0.1)
    import matplotlib.patches as mpatches
    cls = sorted(df.cluster.unique())
    cmap = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    handles = []
    for i, cl in enumerate(cls):
        g[g.cluster == cl].plot(ax=ax, color=cmap(i), edgecolor="white", linewidth=0.05)
        handles.append(mpatches.Patch(color=cmap(i), label=f"C{cl} (n={(df.cluster==cl).sum()})"))
    ax.set_title(f"BUS {group} FINAL (LSOA hourly GMM) K={K} — LSOA clusters")
    ax.legend(handles=handles, loc="lower right", fontsize=9); ax.set_axis_off()
    fig.tight_layout(); fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def run(jobs, kind, dirs):
    base = gpd.read_file(BASEMAP).to_crs(27700)
    for group, cfg in jobs.items():
        Xdf = pd.read_parquet(cfg["X"])
        Xdf = Xdf.select_dtypes("number")
        X = Xdf.values.astype(float)
        cmap = parse_cols(Xdf.columns)
        dest = cfg["X"].parent
        cand_dir = dest / "candidates"; cand_dir.mkdir(exist_ok=True)

        d = diagnostics(X)
        d.round(4).to_csv(dest / f"{group}_kdiag_full.csv", index=False)
        plot_kdiag(d, f"{kind.upper()} {group} FINAL (raw-share) — K-diagnostics", dest / f"{group}_kdiag.png")

        # ARI sanity vs existing labels
        try:
            ref = pd.read_csv(cfg["ref"])
            rl = ref["cluster"].values
            refk = len(np.unique(rl))
            my = gmm(refk, X).predict(X)
            print(f"  {kind} {group}: ARI(refit K={refk} vs existing FINAL) = {adjusted_rand_score(rl, my):.3f}")
        except Exception as e:
            print(f"  {kind} {group}: ARI check skipped ({e})")

        for K in cfg["cand"]:
            lab = gmm(K, X).predict(X)
            pd.DataFrame({"unit": Xdf.index, "cluster": lab}).to_csv(
                cand_dir / f"{group}_k{K}_labels.csv", index=False)
            plot_profiles(Xdf, lab, cmap, dirs,
                          f"{kind.upper()} {group} FINAL raw-share K={K} profiles",
                          cand_dir / f"{group}_k{K}_profiles.png")
            if kind == "rail":
                rail_map(lab, Xdf.index, group, K, cand_dir / f"{group}_k{K}_map.png", base)
            else:
                bus_map(lab, Xdf.index, group, K, cand_dir / f"{group}_k{K}_map.png", base)
            sizes = sorted(np.bincount(lab).tolist(), reverse=True)
            print(f"  {kind} {group} K={K}: sizes={sizes}")
        print(f"  {kind} {group}: kdiag + {len(cfg['cand'])} candidate Ks saved -> {dest}")


def main():
    run(RAIL_JOBS, "rail", [("entry", GREEN, "entry"), ("exit", RED, "exit")])
    run(BUS_JOBS, "bus", [("boardings", GREEN, "boardings"), ("alightings", RED, "alightings")])
    print("done")


if __name__ == "__main__":
    main()
