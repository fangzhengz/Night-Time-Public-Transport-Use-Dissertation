"""BUSTO v2 candidate batch (LSOA level): full deliverables for several K.

Pruned behavioural features (dropped redundant persist_00). Primary = KMeans.
Per (group, K): labels CSV, boarding/alighting temporal profiles, per-cluster
feature signature, choropleth map, silhouette.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
INP = ROOT / "outputs" / "preprocessed_busto" / "busto_lsoa_qhr_night.parquet"
META = ROOT / "outputs" / "preprocessed_busto" / "busto_lsoa_meta.csv"
BASEMAP = ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
OUTD = ROOT / "outputs" / "busto_lsoa_2000_featv2" / "candidates"
OUTD.mkdir(parents=True, exist_ok=True)

START, WIN_END, SPLIT = 20*60, 30*60, 24*60
MIN_TOTAL, RS = 50, 42
GROUPS = {"weekday": ["Weekday"], "weekend": ["Saturday", "Sunday"]}
FEATS = ["A_net", "F_flip", "t_median", "hump_22", "dawn"]
CAND_K = {"weekday": [2, 3, 4], "weekend": [2, 3, 4]}


def ratio(n, d):
    return np.where(d > 0, n/d, 0.0)


def build(raw, days):
    d = raw[(raw["traffic_minute"] >= START) & (raw["day_type"].isin(days))].copy()
    d["tbin"] = (d["traffic_minute"]//60)*60
    g = d.groupby(["lsoa", "tbin"], as_index=False).agg(b=("boardings", "sum"), a=("alightings", "sum"))
    bo = g.pivot_table("b", "lsoa", "tbin", fill_value=0.0)
    al = g.pivot_table("a", "lsoa", "tbin", fill_value=0.0)
    bins = sorted(set(bo.columns) | set(al.columns))
    bo = bo.reindex(columns=bins, fill_value=0.0); al = al.reindex(columns=bins, fill_value=0.0)
    bo, al = bo.align(al, join="outer", fill_value=0.0)
    t = np.array(bins, float)
    tot = (bo+al).sum(1); keep = tot[tot >= MIN_TOTAL].index
    bo, al = bo.loc[keep], al.loc[keep]
    act = bo+al; A = act.sum(1)
    early = t < SPLIT; late = ~early
    be, ae = bo.loc[:, early].sum(1), al.loc[:, early].sum(1)
    bl, ll = bo.loc[:, late].sum(1), al.loc[:, late].sum(1)
    share = act.div(A, axis=0).values
    med = (np.cumsum(share, 1) >= 0.5).argmax(1)

    def at(mn):
        return share[:, int(np.argmin(np.abs(t-mn)))]
    f = pd.DataFrame(index=bo.index)
    f["A_net"] = ratio((bo-al).sum(1).values, A.values)
    Ae = ratio((be-ae).values, (be+ae).values); Al = ratio((bl-ll).values, (bl+ll).values)
    ok = ((be+ae).values > 20) & ((bl+ll).values > 20)
    f["F_flip"] = np.where(ok, Ae-Al, 0.0)
    f["t_median"] = (t[med]-START)/(WIN_END-START)
    f["hump_22"] = at(22*60) - (at(21*60)+at(24*60))/2
    f["dawn"] = share[:, t >= 28*60].sum(1)
    bs = bo.div(bo.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    as_ = al.div(al.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    return f, bs, as_, t


def plot_profiles(bs, as_, t, lab, group, K, dest):
    cls = sorted(pd.unique(lab))
    fig, axs = plt.subplots(len(cls), 1, figsize=(9, max(2*len(cls), 4)), squeeze=False, sharey=True)
    cand = {1200: "20:00", 1380: "23:00", 1440: "00:00", 1620: "03:00", 1740: "05:00"}
    for ax, cl in zip(axs[:, 0], cls):
        m = lab == cl
        for arr, col, nm in [(bs, "#2F6B4F", "boardings"), (as_, "#9A3D3D", "alightings")]:
            sub = arr.loc[m]
            ax.plot(t, sub.median(0).values, color=col, lw=1.5, marker="o", ms=3, label=nm)
            ax.fill_between(t, sub.quantile(.1).values, sub.quantile(.9).values, color=col, alpha=.12, lw=0)
        ax.set_title(f"{group} C{cl} (n={int(m.sum())})", fontsize=9)
        tk = [k for k in cand if t.min() <= k <= t.max()]
        ax.set_xticks(tk); ax.set_xticklabels([cand[k] for k in tk], fontsize=8)
        ax.grid(axis="y", color="#eee", lw=.6); ax.spines[["top", "right"]].set_visible(False)
    axs[0, 0].legend(fontsize=8)
    fig.suptitle(f"BUS {group} v2 K={K} profiles", y=1.002); fig.tight_layout()
    fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_map(base, labser, group, K, dest):
    gdf = base.merge(labser.rename("cluster").reset_index().rename(columns={"index": "lsoa"}),
                     left_on="LSOA21CD", right_on="lsoa", how="left")
    cls = sorted(labser.unique())
    cmap = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf[gdf["cluster"].isna()].plot(ax=ax, color="#ededed", edgecolor="#e2e2e2", linewidth=0.1)
    handles = []
    for i, cl in enumerate(cls):
        gdf[gdf["cluster"] == cl].plot(ax=ax, color=cmap(i), edgecolor="white", linewidth=0.1)
        handles.append(mpatches.Patch(color=cmap(i), label=f"C{cl} (n={int((labser==cl).sum())})"))
    handles.append(mpatches.Patch(color="#ededed", label="no/low data"))
    ax.set_title(f"BUS {group} v2 K={K} LSOA cluster map")
    ax.legend(handles=handles, loc="lower right", fontsize=9); ax.set_axis_off()
    fig.tight_layout(); fig.savefig(dest, dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    raw = pd.read_parquet(INP); raw["lsoa"] = raw["lsoa"].astype(str)
    base = gpd.read_file(BASEMAP).to_crs(27700)
    meta = pd.read_csv(META, dtype={"lsoa": str}).set_index("lsoa")
    summary = []
    for group, days in GROUPS.items():
        feat, bs, as_, t = build(raw, days)
        Xs = StandardScaler().fit_transform(feat[FEATS].values)
        for K in CAND_K[group]:
            gm = GaussianMixture(K, covariance_type="diag", n_init=15, reg_covar=1e-6, random_state=RS).fit(Xs)
            lab = gm.predict(Xs)
            post = gm.predict_proba(Xs)
            sil = silhouette_score(Xs, lab, sample_size=min(3000, len(Xs)), random_state=RS)
            labser = pd.Series(lab, index=feat.index)
            out = feat.copy(); out["cluster"] = lab
            out["max_posterior"] = post.max(1)
            out["entropy"] = (-np.where(post > 0, post * np.log(post), 0.0).sum(1))
            out = out.join(meta[["lsoa_name", "rep_stop", "n_stops"]])
            out.to_csv(OUTD / f"{group}_k{K}_labels.csv")
            sig = out.groupby("cluster")[FEATS].mean().round(3); sig["n"] = out.groupby("cluster").size()
            sig.to_csv(OUTD / f"{group}_k{K}_signature.csv")
            plot_profiles(bs, as_, t, lab, group, K, OUTD / f"{group}_k{K}_profiles.png")
            plot_map(base, labser, group, K, OUTD / f"{group}_k{K}_map.png")
            summary.append({"group": group, "K": K, "silhouette": round(sil, 3),
                            "sizes": sorted(np.bincount(lab).tolist(), reverse=True)})
            print(f"{group} K={K}: sil={sil:.3f} sizes={sorted(np.bincount(lab).tolist(),reverse=True)}")
    pd.DataFrame(summary).to_csv(OUTD / "candidate_summary.csv", index=False)
    print("\nSaved ->", OUTD)


if __name__ == "__main__":
    main()
