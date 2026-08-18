"""BUSTO feature v2: interpretable behavioural features + clustering comparison
at LSOA level. Mirrors the rail v2 approach.

Direction semantics: boardings = people boarding (origin), alightings =
people alighting (destination) -- analogous to rail entry/exit.

Per day-type group (weekday=Weekday, weekend=Saturday+Sunday):
  1. rebuild night-window LSOA curves (same window/threshold as the GMM run)
  2. compute behavioural features (A_net, F_flip, t_median, persist_00, hump_22, dawn)
  3. standardise; report feature correlation
  4. GMM / KMeans / Ward over K=2..8 (silhouette/CH/DB)
  5. bootstrap-ARI stability K=3,4,5
  6. A-B scatter coloured by existing cluster labels
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
INP = ROOT / "outputs" / "preprocessed_busto" / "busto_lsoa_qhr_night.parquet"
OUTD = ROOT / "outputs" / "busto_lsoa_2000_featv2"
OUTD.mkdir(parents=True, exist_ok=True)

START = 20*60
WIN_END = 30*60          # 06:00 next day
SPLIT = 24*60            # midnight
MIN_TOTAL = 50
RS = 42
GROUPS = {"weekday": ["Weekday"], "weekend": ["Saturday", "Sunday"]}
OLD_LAB = {"weekday": ROOT/"outputs"/"busto_lsoa_2000_gmm"/"weekday"/"weekday_k4_labels.csv",
           "weekend": ROOT/"outputs"/"busto_lsoa_2000_gmm"/"weekend"/"weekend_k4_labels.csv"}
SIL_SAMPLE = 3000


def ratio(num, den):
    return np.where(den > 0, num/den, 0.0)


def build_features(raw, days):
    d = raw[(raw["traffic_minute"] >= START) & (raw["day_type"].isin(days))].copy()
    d["tbin"] = (d["traffic_minute"] // 60) * 60
    g = d.groupby(["lsoa", "tbin"], as_index=False).agg(b=("boardings", "sum"), a=("alightings", "sum"))
    bo = g.pivot_table("b", "lsoa", "tbin", fill_value=0.0)
    al = g.pivot_table("a", "lsoa", "tbin", fill_value=0.0)
    bins = sorted(set(bo.columns) | set(al.columns))
    bo = bo.reindex(columns=bins, fill_value=0.0); al = al.reindex(columns=bins, fill_value=0.0)
    bo, al = bo.align(al, join="outer", fill_value=0.0)
    t = np.array(bins, dtype=float)

    tot = (bo + al).sum(1); keep = tot[tot >= MIN_TOTAL].index
    bo, al = bo.loc[keep], al.loc[keep]
    act = bo + al; A = act.sum(1)
    early = t < SPLIT; late = ~early
    be, ae = bo.loc[:, early].sum(1), al.loc[:, early].sum(1)
    bl, ll = bo.loc[:, late].sum(1), al.loc[:, late].sum(1)
    share_t = act.div(A, axis=0).values
    cum = np.cumsum(share_t, axis=1); med = (cum >= 0.5).argmax(axis=1)

    def at(minute):
        return share_t[:, int(np.argmin(np.abs(t - minute)))]
    feat = pd.DataFrame(index=bo.index)
    feat["A_net"] = ratio((bo-al).sum(1).values, A.values)
    Ae = ratio((be-ae).values, (be+ae).values); Al = ratio((bl-ll).values, (bl+ll).values)
    ok = ((be+ae).values > 20) & ((bl+ll).values > 20)
    feat["F_flip"] = np.where(ok, Ae-Al, 0.0)
    feat["t_median"] = (t[med]-START)/(WIN_END-START)
    pm = t >= SPLIT; feat["persist_00"] = share_t[:, pm].sum(1)
    feat["hump_22"] = at(22*60) - (at(21*60)+at(24*60))/2
    dw = t >= 28*60; feat["dawn"] = share_t[:, dw].sum(1)
    bs = bo.div(bo.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    as_ = al.div(al.sum(1).replace(0, np.nan), axis=0).fillna(0.0)
    return feat, bs, as_, t


def cluster_diag(Xs, kmax=8):
    rows = []
    for k in range(2, kmax+1):
        gm = GaussianMixture(k, covariance_type="diag", n_init=10, random_state=RS).fit_predict(Xs)
        km = KMeans(k, n_init=10, random_state=RS).fit_predict(Xs)
        wd = AgglomerativeClustering(k, linkage="ward").fit_predict(Xs)
        sil = lambda l: round(silhouette_score(Xs, l, sample_size=min(SIL_SAMPLE, len(Xs)), random_state=RS), 3)
        rows.append({"K": k, "GMM_sil": sil(gm), "KM_sil": sil(km), "Ward_sil": sil(wd),
                     "KM_CH": round(calinski_harabasz_score(Xs, km)), "KM_DB": round(davies_bouldin_score(Xs, km), 2)})
    return pd.DataFrame(rows)


def bootstrap_ari(Xs, k, n_boot=20):
    base = KMeans(k, n_init=10, random_state=RS).fit(Xs)
    ref = base.predict(Xs)
    rng = np.random.default_rng(RS); n = len(Xs); aris = []
    for _ in range(n_boot):
        idx = rng.choice(n, n, replace=True)
        km = KMeans(k, n_init=5, random_state=int(rng.integers(1e6))).fit(Xs[idx])
        aris.append(adjusted_rand_score(ref, km.predict(Xs)))
    return np.mean(aris), np.std(aris)


def main():
    raw = pd.read_parquet(INP); raw["lsoa"] = raw["lsoa"].astype(str)
    for group, days in GROUPS.items():
        feat, bs, as_, t = build_features(raw, days)
        feat.to_csv(OUTD / f"{group}_featv2.csv")
        Xs = StandardScaler().fit_transform(feat.values)
        print("\n" + "#"*64 + f"\n# BUS {group}  (n={len(feat)} LSOAs, {feat.shape[1]} features)\n" + "#"*64)
        print("feature correlation:")
        print(feat.corr().round(2).to_string())
        diag = cluster_diag(Xs); diag.to_csv(OUTD / f"{group}_diag_v2.csv", index=False)
        print("\nK-ladder on v2 features:")
        print(diag.to_string(index=False))
        print("\nbootstrap KMeans stability (mean ARI +/- sd):")
        for k in (3, 4, 5):
            m, s = bootstrap_ari(Xs, k); print(f"  K={k}: {m:.3f} +/- {s:.3f}")

        old = pd.read_csv(OLD_LAB[group], dtype={"lsoa": str}).set_index("lsoa")["cluster"].reindex(feat.index)
        fig, ax = plt.subplots(figsize=(7.5, 6))
        sc = ax.scatter(feat["A_net"], feat["F_flip"], c=old.values, cmap="tab10", s=8, alpha=.6)
        ax.set_xlabel("A_net (boardings>0 / alightings<0)"); ax.set_ylabel("F_flip (early-board→late-alight >0)")
        ax.set_title(f"BUS {group}: A_net vs F_flip, coloured by OLD cluster")
        ax.axhline(0, color="#aaa", lw=.7); ax.axvline(0, color="#aaa", lw=.7)
        plt.colorbar(sc, label="old cluster"); fig.tight_layout()
        fig.savefig(OUTD / f"{group}_AF_scatter.png", dpi=160); plt.close(fig)
    print("\nSaved ->", OUTD)


if __name__ == "__main__":
    main()
