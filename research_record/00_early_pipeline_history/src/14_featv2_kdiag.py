# -*- coding: utf-8 -*-
"""K-selection diagnostic charts for the v2 (engineered-feature) clustering.

For rail (LU stations) and bus (LSOA), weekday & weekend, computes across K=2..8:
  silhouette (GMM / KMeans / Ward), Calinski-Harabasz, Davies-Bouldin (KMeans),
  and bootstrap KMeans stability (mean ARI ± sd).
Saves a 2x2 panel per group with the chosen K marked, plus a combined CSV.
Uses the same pruned feature sets as the candidate clustering.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score, adjusted_rand_score)

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
RAIL = ROOT / "outputs" / "preprocessed_numbat" / "numbat_lu_station_qhr_all_daytypes.parquet"
BUS = ROOT / "outputs" / "preprocessed_busto" / "busto_lsoa_qhr_night.parquet"
RS = 42
KR = range(2, 9)
START = 20*60


def ratio(n, d):
    return np.where(d > 0, n/d, 0.0)


# ---------- RAIL feature build (matches script 08) ----------
RWIN = {"MON": (START, 25*60, None), "TWT": (START, 25*60, None), "SUN": (START, 25*60, None),
        "FRI": (START, 30*60, "SAT"), "SAT": (START, 30*60, "SUN")}


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
    return f[feats]


# ---------- BUS feature build (matches script 10) ----------
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
    return f[feats]


def diagnostics(Xs):
    rows = []
    sample = min(3000, len(Xs))
    sil = lambda l: silhouette_score(Xs, l, sample_size=sample, random_state=RS)
    for k in KR:
        gm = GaussianMixture(k, covariance_type="diag", n_init=10, random_state=RS).fit_predict(Xs)
        km = KMeans(k, n_init=10, random_state=RS).fit_predict(Xs)
        wd = AgglomerativeClustering(k, linkage="ward").fit_predict(Xs)
        # stability: bootstrap GMM (diag) -- matches the primary model
        ref = gm
        rng = np.random.default_rng(RS); aris = []
        nb = 25 if len(Xs) < 1000 else 15
        for _ in range(nb):
            idx = rng.choice(len(Xs), len(Xs), replace=True)
            g2 = GaussianMixture(k, covariance_type="diag", n_init=3, reg_covar=1e-6, random_state=int(rng.integers(1e6))).fit(Xs[idx])
            aris.append(adjusted_rand_score(gm, g2.predict(Xs)))
        rows.append({"K": k, "GMM_sil": sil(gm), "KM_sil": sil(km), "Ward_sil": sil(wd),
                     "CH": calinski_harabasz_score(Xs, km), "DB": davies_bouldin_score(Xs, km),
                     "ARI": np.mean(aris), "ARI_sd": np.std(aris)})
    return pd.DataFrame(rows)


def plot(diag, title, chosen, dest):
    fig, ax = plt.subplots(2, 2, figsize=(10, 7.5))
    K = diag.K
    a = ax[0, 0]
    a.plot(K, diag.GMM_sil, "-o", label="GMM", color="#500778")
    a.plot(K, diag.KM_sil, "-s", label="KMeans", color="#2F6B4F")
    a.plot(K, diag.Ward_sil, "-^", label="Ward", color="#9A3D3D")
    a.set_title("Silhouette (higher = better)"); a.legend(fontsize=8)
    a = ax[0, 1]; a.plot(K, diag.CH, "-o", color="#2F6B4F"); a.set_title("Calinski-Harabasz (higher = better)")
    a = ax[1, 0]; a.plot(K, diag.DB, "-o", color="#9A3D3D"); a.set_title("Davies-Bouldin (lower = better)")
    a = ax[1, 1]
    a.errorbar(K, diag.ARI, yerr=diag.ARI_sd, fmt="-o", color="#500778", capsize=3)
    a.set_title("Bootstrap stability ARI (higher = better)"); a.set_ylim(0, 1.02)
    for row in ax:
        for a in row:
            a.axvline(chosen, color="#C89B3C", ls="--", lw=1.5, alpha=.8)
            a.set_xlabel("K"); a.grid(color="#eee", lw=.7); a.spines[["top", "right"]].set_visible(False)
            a.set_xticks(list(KR))
    fig.suptitle(title + f"   (chosen K = {chosen}, dashed)", fontsize=13, y=0.99)
    fig.tight_layout(); fig.savefig(dest, dpi=160, bbox_inches="tight"); plt.close(fig)


def main():
    # RAIL
    rraw = pd.read_parquet(RAIL); rraw["day_type"] = rraw.day_type.astype(str); rraw["NLC"] = rraw.NLC.astype(str)
    RF = {"weekday": ["A_net", "F_flip", "t_median", "persist_00", "hump_22"],
          "weekend": ["A_net", "F_flip", "t_median", "persist_00", "hump_22", "dawn"]}
    rail_jobs = [("weekday", ["MON", "TWT"], 23*60, 25*60, 4), ("weekend", ["FRI", "SAT", "SUN"], 24*60, 30*60, 3)]
    outd = ROOT / "outputs" / "lu_rail_2000_featv2"
    for grp, days, split, we, ck in rail_jobs:
        f = rail_feat(rraw, days, split, we, RF[grp])
        Xs = StandardScaler().fit_transform(f.values)
        diag = diagnostics(Xs); diag.round(3).to_csv(outd / f"{grp}_kdiag_v2.csv", index=False)
        plot(diag, f"RAIL {grp} — v2 K-diagnostics", ck, outd / f"{grp}_kdiag_v2.png")
        print(f"rail {grp}: saved kdiag (chosen K={ck})")
    # BUS
    braw = pd.read_parquet(BUS); braw["lsoa"] = braw.lsoa.astype(str)
    BF = ["A_net", "F_flip", "t_median", "hump_22", "dawn"]
    bus_jobs = [("weekday", ["Weekday"], 3), ("weekend", ["Saturday", "Sunday"], 3)]
    outd = ROOT / "outputs" / "busto_lsoa_2000_featv2"
    for grp, days, ck in bus_jobs:
        f = bus_feat(braw, days, BF)
        Xs = StandardScaler().fit_transform(f.values)
        diag = diagnostics(Xs); diag.round(3).to_csv(outd / f"{grp}_kdiag_v2.csv", index=False)
        plot(diag, f"BUS {grp} — v2 K-diagnostics", ck, outd / f"{grp}_kdiag_v2.png")
        print(f"bus {grp}: saved kdiag (chosen K={ck})")
    print("done")


if __name__ == "__main__":
    main()
