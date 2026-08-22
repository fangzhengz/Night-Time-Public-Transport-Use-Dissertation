# -*- coding: utf-8 -*-
"""Alternative weekday/weekend definition (weekend = Fri+Sat; Sunday -> weekday).

Mirrors the lu_rail_2000_featv2 pipeline (engineered features -> K-diagnostics
-> candidate clustering with profiles/signatures/maps) for BOTH rail and bus,
under the new day grouping. Outputs to *_featv2_FS dirs (FS = Fri-Sat weekend).

Day mapping (data-constrained):
  RAIL  weekday = MON+TWT+SUN   weekend = FRI+SAT
  BUS   weekday = Weekday+Sunday weekend = Saturday   (Friday not separable in BUSTO)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score, adjusted_rand_score)

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
RAILP = ROOT/"outputs"/"preprocessed_numbat"/"numbat_lu_station_qhr_all_daytypes.parquet"
BUSP = ROOT/"outputs"/"preprocessed_busto"/"busto_lsoa_qhr_night.parquet"
XY = ROOT/"outputs"/"lu_rail_2000_diag"/"weekday"/"weekday_k5_labels_xy.csv"   # static coord lookup
BUSMETA = ROOT/"outputs"/"preprocessed_busto"/"busto_lsoa_meta.csv"
BASEMAP = ROOT/"map"/"London_LSOA_2021_Boundaries.geojson"
START, RS = 20*60, 42
KR = range(2, 9)
RAIL_OUT = ROOT/"outputs"/"lu_rail_2000_featv2_FS"
BUS_OUT = ROOT/"outputs"/"busto_lsoa_2000_featv2_FS"
RWIN = {"MON": (START, 25*60, None), "TWT": (START, 25*60, None), "SUN": (START, 25*60, None),
        "FRI": (START, 30*60, "SAT"), "SAT": (START, 30*60, "SUN")}
TIME_TICKS = {1200: "20:00", 1380: "23:00", 1440: "00:00", 1620: "03:00", 1740: "05:00"}


def ratio(n, d):
    return np.where(d > 0, n/d, 0.0)


def rail_feat(raw, days, split, win_end, feats):
    def app_next(df, focal, nxt):
        e = df[(df.day_type.astype(str) == nxt) & (df.hour >= 5) & (df.hour < 6)].copy()
        e["day_type"] = focal; e["extended_minute"] = e.hour*60 + e.minute + 24*60
        return e
    def subset(df, dt):
        s, en, nx = RWIN[dt]; b = df[df.day_type.astype(str) == dt].copy()
        b = b[(b.extended_minute >= s) & (b.extended_minute < min(en, 29*60))].copy()
        if en > 29*60:
            b = pd.concat([b, app_next(df, dt, nx)], ignore_index=True)
        return b
    long = pd.concat([subset(raw, dt) for dt in days], ignore_index=True)
    g = long.groupby(["NLC", "direction", "extended_minute"], as_index=False)["count"].sum()
    e = g[g.direction == "entry"].pivot_table("count", "NLC", "extended_minute", fill_value=0.0)
    x = g[g.direction == "exit"].pivot_table("count", "NLC", "extended_minute", fill_value=0.0)
    bins = sorted(set(e.columns) | set(x.columns))
    e = e.reindex(columns=bins, fill_value=0.0); x = x.reindex(columns=bins, fill_value=0.0)
    e, x = e.align(x, join="outer", fill_value=0.0); t = np.array(bins, float)
    tot = (e+x).sum(1); keep = tot[tot >= 50].index; e, x = e.loc[keep], x.loc[keep]
    a = e+x; A = a.sum(1); early = t < split; late = ~early
    ee, xe = e.loc[:, early].sum(1), x.loc[:, early].sum(1)
    el, xl = e.loc[:, late].sum(1), x.loc[:, late].sum(1)
    sh = a.div(A, axis=0).values; med = (np.cumsum(sh, 1) >= 0.5).argmax(1)
    at = lambda m: sh[:, int(np.argmin(np.abs(t-m)))]
    f = pd.DataFrame(index=e.index)
    f["A_net"] = ratio((e-x).sum(1).values, A.values)
    Ae = ratio((ee-xe).values, (ee+xe).values); Al = ratio((el-xl).values, (el+xl).values)
    ok = ((ee+xe).values > 20) & ((el+xl).values > 20)
    f["F_flip"] = np.where(ok, Ae-Al, 0.0)
    f["t_median"] = (t[med]-START)/(win_end-START)
    f["persist_00"] = sh[:, t >= 24*60].sum(1)
    f["hump_22"] = at(22*60) - (at(21*60)+at(24*60))/2
    f["dawn"] = sh[:, (t >= 28*60+30) & (t < 30*60)].sum(1) if (t >= 28*60+30).any() else 0.0
    es = e.div(e.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    xs = x.div(x.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    return f[feats], es, xs, t, ("entry", "exit")


def bus_feat(raw, days, feats):
    d = raw[(raw.traffic_minute >= START) & (raw.day_type.isin(days))].copy()
    d["tbin"] = (d.traffic_minute//60)*60
    g = d.groupby(["lsoa", "tbin"], as_index=False).agg(b=("boardings", "sum"), a=("alightings", "sum"))
    bo = g.pivot_table("b", "lsoa", "tbin", fill_value=0.0); al = g.pivot_table("a", "lsoa", "tbin", fill_value=0.0)
    bins = sorted(set(bo.columns) | set(al.columns))
    bo = bo.reindex(columns=bins, fill_value=0.0); al = al.reindex(columns=bins, fill_value=0.0)
    bo, al = bo.align(al, join="outer", fill_value=0.0); t = np.array(bins, float)
    tot = (bo+al).sum(1); keep = tot[tot >= 50].index; bo, al = bo.loc[keep], al.loc[keep]
    act = bo+al; A = act.sum(1); early = t < 24*60; late = ~early
    be, ae = bo.loc[:, early].sum(1), al.loc[:, early].sum(1)
    bl, ll = bo.loc[:, late].sum(1), al.loc[:, late].sum(1)
    sh = act.div(A, axis=0).values; med = (np.cumsum(sh, 1) >= 0.5).argmax(1)
    at = lambda m: sh[:, int(np.argmin(np.abs(t-m)))]
    f = pd.DataFrame(index=bo.index)
    f["A_net"] = ratio((bo-al).sum(1).values, A.values)
    Ae = ratio((be-ae).values, (be+ae).values); Al = ratio((bl-ll).values, (bl+ll).values)
    ok = ((be+ae).values > 20) & ((bl+ll).values > 20)
    f["F_flip"] = np.where(ok, Ae-Al, 0.0)
    f["t_median"] = (t[med]-START)/(30*60-START)
    f["hump_22"] = at(22*60) - (at(21*60)+at(24*60))/2
    f["dawn"] = sh[:, t >= 28*60].sum(1)
    bs = bo.div(bo.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    as_ = al.div(al.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    return f[feats], bs, as_, t, ("boardings", "alightings")


def diagnostics(Xs):
    rows = []; sample = min(3000, len(Xs))
    sil = lambda l: silhouette_score(Xs, l, sample_size=sample, random_state=RS)
    for k in KR:
        gm = GaussianMixture(k, covariance_type="diag", n_init=10, random_state=RS).fit_predict(Xs)
        km = KMeans(k, n_init=10, random_state=RS).fit_predict(Xs)
        wd = AgglomerativeClustering(k, linkage="ward").fit_predict(Xs)
        rng = np.random.default_rng(RS); aris = []; nb = 25 if len(Xs) < 1000 else 15
        for _ in range(nb):
            idx = rng.choice(len(Xs), len(Xs), replace=True)
            g2 = GaussianMixture(k, covariance_type="diag", n_init=3, reg_covar=1e-6, random_state=int(rng.integers(1e6))).fit(Xs[idx])
            aris.append(adjusted_rand_score(gm, g2.predict(Xs)))
        rows.append({"K": k, "GMM_sil": sil(gm), "KM_sil": sil(km), "Ward_sil": sil(wd),
                     "CH": calinski_harabasz_score(Xs, km), "DB": davies_bouldin_score(Xs, km),
                     "ARI": np.mean(aris), "ARI_sd": np.std(aris)})
    return pd.DataFrame(rows)


def plot_kdiag(diag, title, dest):
    fig, ax = plt.subplots(2, 2, figsize=(10, 7.5)); K = diag.K
    a = ax[0, 0]
    a.plot(K, diag.GMM_sil, "-o", label="GMM", color="#500778")
    a.plot(K, diag.KM_sil, "-s", label="KMeans", color="#2F6B4F")
    a.plot(K, diag.Ward_sil, "-^", label="Ward", color="#9A3D3D")
    a.set_title("Silhouette (higher = better)"); a.legend(fontsize=8)
    ax[0, 1].plot(K, diag.CH, "-o", color="#2F6B4F"); ax[0, 1].set_title("Calinski-Harabasz (higher = better)")
    ax[1, 0].plot(K, diag.DB, "-o", color="#9A3D3D"); ax[1, 0].set_title("Davies-Bouldin (lower = better)")
    ax[1, 1].errorbar(K, diag.ARI, yerr=diag.ARI_sd, fmt="-o", color="#500778", capsize=3)
    ax[1, 1].set_title("Bootstrap stability ARI"); ax[1, 1].set_ylim(0, 1.02)
    for row in ax:
        for a in row:
            a.set_xlabel("K"); a.grid(color="#eee", lw=.7); a.spines[["top", "right"]].set_visible(False); a.set_xticks(list(KR))
    fig.suptitle(title, fontsize=13, y=0.99); fig.tight_layout(); fig.savefig(dest, dpi=160, bbox_inches="tight"); plt.close(fig)


def plot_profiles(d1, d2, t, lab, names, title, dest):
    cls = sorted(pd.unique(lab))
    fig, axs = plt.subplots(len(cls), 1, figsize=(9, max(2*len(cls), 4)), squeeze=False, sharey=True)
    for ax, cl in zip(axs[:, 0], cls):
        m = lab == cl
        for arr, col, nm in [(d1, "#2F6B4F", names[0]), (d2, "#9A3D3D", names[1])]:
            sub = arr.loc[m]
            ax.plot(t, sub.median(0).values, color=col, lw=1.5, marker="o", ms=3, label=nm)
            ax.fill_between(t, sub.quantile(.1).values, sub.quantile(.9).values, color=col, alpha=.12, lw=0)
        ax.set_title(f"C{cl} (n={int(m.sum())})", fontsize=9)
        tk = [k for k in TIME_TICKS if t.min() <= k <= t.max()]
        ax.set_xticks(tk); ax.set_xticklabels([TIME_TICKS[k] for k in tk], fontsize=8)
        ax.grid(axis="y", color="#eee", lw=.6); ax.spines[["top", "right"]].set_visible(False)
    axs[0, 0].legend(fontsize=8); fig.suptitle(title, y=1.002); fig.tight_layout()
    fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def rail_map(labels_xy, title, dest, base):
    gdf = gpd.GeoDataFrame(labels_xy, geometry=gpd.points_from_xy(labels_xy.easting, labels_xy.northing), crs=27700)
    cls = sorted(gdf.cluster.unique()); cmap = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10)); base.plot(ax=ax, color="#f2f2f2", edgecolor="#dcdcdc", linewidth=0.2)
    for i, cl in enumerate(cls):
        sdf = gdf[gdf.cluster == cl]
        ax.scatter(sdf.geometry.x, sdf.geometry.y, s=40, color=cmap(i), edgecolor="white", linewidth=0.6, label=f"C{cl} (n={len(sdf)})", zorder=3)
    ax.set_title(title); ax.legend(loc="lower right", fontsize=9); ax.set_axis_off()
    mnx, mny, mxx, mxy = gdf.total_bounds; pad = 3000; ax.set_xlim(mnx-pad, mxx+pad); ax.set_ylim(mny-pad, mxy+pad)
    fig.tight_layout(); fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def bus_map(base, labser, title, dest):
    gdf = base.merge(labser.rename("cluster").reset_index().rename(columns={"index": "lsoa"}), left_on="LSOA21CD", right_on="lsoa", how="left")
    cls = sorted(labser.unique()); cmap = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf[gdf.cluster.isna()].plot(ax=ax, color="#ededed", edgecolor="#e2e2e2", linewidth=0.1)
    handles = []
    for i, cl in enumerate(cls):
        gdf[gdf.cluster == cl].plot(ax=ax, color=cmap(i), edgecolor="white", linewidth=0.1)
        handles.append(mpatches.Patch(color=cmap(i), label=f"C{cl} (n={int((labser==cl).sum())})"))
    handles.append(mpatches.Patch(color="#ededed", label="no/low data"))
    ax.set_title(title); ax.legend(handles=handles, loc="lower right", fontsize=9); ax.set_axis_off()
    fig.tight_layout(); fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def run_group(feat, d1, d2, t, names, cand_ks, outdir, tag, mapper):
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir/"candidates").mkdir(exist_ok=True)
    feat.to_csv(outdir/f"{tag}_featv2.csv")
    Xs = StandardScaler().fit_transform(feat.values)
    diag = diagnostics(Xs); diag.round(3).to_csv(outdir/f"{tag}_kdiag_v2.csv", index=False)
    plot_kdiag(diag, f"{tag} (Fri-Sat weekend) — v2 K-diagnostics", outdir/f"{tag}_kdiag_v2.png")
    summ = []
    for K in cand_ks:
        gm = GaussianMixture(K, covariance_type="diag", n_init=20, reg_covar=1e-6, random_state=RS).fit(Xs)
        lab = gm.predict(Xs)
        post = gm.predict_proba(Xs)
        sil = silhouette_score(Xs, lab, sample_size=min(3000, len(Xs)), random_state=RS)
        labser = pd.Series(lab, index=feat.index)
        out = feat.copy(); out["cluster"] = lab
        out["max_posterior"] = post.max(1)
        out["entropy"] = (-np.where(post > 0, post * np.log(post), 0.0).sum(1))
        out.to_csv(outdir/"candidates"/f"{tag}_k{K}_labels.csv")
        sig = out.groupby("cluster")[list(feat.columns)].mean().round(3); sig["n"] = out.groupby("cluster").size()
        sig.to_csv(outdir/"candidates"/f"{tag}_k{K}_signature.csv")
        plot_profiles(d1, d2, t, lab, names, f"{tag} FS K={K} profiles", outdir/"candidates"/f"{tag}_k{K}_profiles.png")
        mapper(labser, K, outdir/"candidates"/f"{tag}_k{K}_map.png")
        summ.append({"group": tag, "K": K, "silhouette": round(sil, 3), "sizes": sorted(np.bincount(lab).tolist(), reverse=True)})
        print(f"  {tag} K={K}: sil={sil:.3f} sizes={sorted(np.bincount(lab).tolist(),reverse=True)}")
    pd.DataFrame(summ).to_csv(outdir/"candidates"/f"{tag}_candidate_summary.csv", index=False)


def main():
    base = gpd.read_file(BASEMAP).to_crs(27700)
    # ---- RAIL ----
    rraw = pd.read_parquet(RAILP); rraw["day_type"] = rraw.day_type.astype(str); rraw["NLC"] = rraw.NLC.astype(str)
    coords = pd.read_csv(XY, dtype={"NLC": str}).set_index("NLC")[["Station", "Fare Zone", "easting", "northing"]]
    RF = {"weekday": ["A_net", "F_flip", "t_median", "persist_00", "hump_22"],
          "weekend": ["A_net", "F_flip", "t_median", "persist_00", "hump_22", "dawn"]}
    rail_jobs = [("weekday", ["MON", "TWT", "SUN"], 23*60, 25*60, [3, 4, 5]),
                 ("weekend", ["FRI", "SAT"], 24*60, 30*60, [2, 3, 4])]
    print("RAIL (Fri-Sat weekend):")
    for tag, days, split, we, cks in rail_jobs:
        feat, es, xs, t, names = rail_feat(rraw, days, split, we, RF[tag])
        def mapper(labser, K, dest, feat=feat):
            lx = feat.join(coords); lx["cluster"] = labser
            rail_map(lx.dropna(subset=["easting"]).reset_index(), f"RAIL {tag} FS K={K}", dest, base)
        run_group(feat, es, xs, t, names, cks, RAIL_OUT, tag, mapper)
    # ---- BUS ----
    braw = pd.read_parquet(BUSP); braw["lsoa"] = braw.lsoa.astype(str)
    BF = ["A_net", "F_flip", "t_median", "hump_22", "dawn"]
    bus_jobs = [("weekday", ["Weekday", "Sunday"], [2, 3, 4]), ("weekend", ["Saturday"], [2, 3, 4])]
    print("BUS (Fri-Sat weekend; bus weekend=Saturday only):")
    for tag, days, cks in bus_jobs:
        feat, bs, as_, t, names = bus_feat(braw, days, BF)
        def mapper(labser, K, dest):
            bus_map(base, labser, f"BUS {tag} FS K={K}", dest)
        run_group(feat, bs, as_, t, names, cks, BUS_OUT, tag, mapper)
    print("done ->", RAIL_OUT, "|", BUS_OUT)


if __name__ == "__main__":
    main()
