"""RAIL feature v2: interpretable behavioural features + clustering comparison.

Replaces the 80-dim raw qhr-share matrix with ~8 hand-crafted scalars that
isolate the *discriminative* signal (directionality, flip, timing, persistence,
nightlife hump, dawn rebound) from the shared night-decline envelope.

Pipeline per day-type group (weekday MON+TWT, weekend FRI+SAT+SUN):
  1. rebuild night-window station curves (same window/threshold as the GMM run)
  2. compute behavioural features
  3. standardise; report feature correlation
  4. GMM / KMeans / Ward over K=2..8 with silhouette/CH/DB
  5. bootstrap-ARI stability for K=3,4,5; cross-model ARI at K=3
  6. save feature table + A-F scatter coloured by the existing cluster labels
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
INP = ROOT / "outputs" / "preprocessed_numbat" / "numbat_lu_station_qhr_all_daytypes.parquet"
OUTD = ROOT / "outputs" / "lu_rail_2000_featv2"
OUTD.mkdir(parents=True, exist_ok=True)

START = 20 * 60
MIN_TOTAL = 50
RS = 42
WINDOW = {"MON": (START, 25*60, None), "TWT": (START, 25*60, None), "SUN": (START, 25*60, None),
          "FRI": (START, 30*60, "SAT"), "SAT": (START, 30*60, "SUN")}
GROUPS = {"weekday": ["MON", "TWT"], "weekend": ["FRI", "SAT", "SUN"]}
SPLIT = {"weekday": 23*60, "weekend": 24*60}          # early/late boundary
WIN_END = {"weekday": 25*60, "weekend": 30*60}
OLD_LAB = {"weekday": ROOT/"outputs"/"lu_rail_2000_diag"/"weekday"/"weekday_k5_labels.csv",
           "weekend": ROOT/"outputs"/"lu_rail_2000_diag"/"weekend"/"weekend_k6_labels.csv"}


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


def safe_ratio(num, den):
    return np.where(den > 0, num / den, 0.0)


def build_features(raw, days, split, win_end):
    long = pd.concat([subset(raw, dt) for dt in days], ignore_index=True)
    # pool day-types: per station x direction x time-bin counts
    g = long.groupby(["NLC", "direction", "extended_minute"], as_index=False)["count"].sum()
    e = g[g["direction"] == "entry"].pivot_table("count", "NLC", "extended_minute", fill_value=0.0)
    x = g[g["direction"] == "exit"].pivot_table("count", "NLC", "extended_minute", fill_value=0.0)
    bins = sorted(set(e.columns) | set(x.columns))
    e = e.reindex(columns=bins, fill_value=0.0)
    x = x.reindex(columns=bins, fill_value=0.0)
    e, x = e.align(x, join="outer", fill_value=0.0)
    t = np.array(bins, dtype=float)

    tot = (e + x).sum(axis=1)
    keep = tot[tot >= MIN_TOTAL].index
    e, x = e.loc[keep], x.loc[keep]
    a = e + x
    A = a.sum(axis=1)

    early = t < split
    late = ~early
    e_e, x_e = e.loc[:, early].sum(1), x.loc[:, early].sum(1)
    e_l, x_l = e.loc[:, late].sum(1), x.loc[:, late].sum(1)

    feat = pd.DataFrame(index=e.index)
    # 1 net directionality
    feat["A_net"] = safe_ratio((e - x).sum(1).values, A.values)
    # 2 direction flip (early - late), guarded by per-segment activity
    A_early = safe_ratio((e_e - x_e).values, (e_e + x_e).values)
    A_late = safe_ratio((e_l - x_l).values, (e_l + x_l).values)
    seg_ok = ((e_e + x_e).values > 20) & ((e_l + x_l).values > 20)
    feat["F_flip"] = np.where(seg_ok, A_early - A_late, 0.0)
    # 3 median activity time (fraction through window, 0..1)
    share_t = a.div(A, axis=0).values
    cum = np.cumsum(share_t, axis=1)
    med_idx = (cum >= 0.5).argmax(axis=1)
    feat["t_median"] = (t[med_idx] - START) / (win_end - START)
    # 4 late-night persistence: share after midnight (>=24:00)
    post_mid = t >= 24*60
    feat["persist_00"] = share_t[:, post_mid].sum(1) if post_mid.any() else 0.0
    # 5 early concentration: share in first hour (20:00-21:00)
    first_h = t < 21*60
    feat["early_conc"] = share_t[:, first_h].sum(1)
    # 6 nightlife hump near 22:00-23:00 vs linear baseline 21:00->00:00
    def at(minute):
        j = int(np.argmin(np.abs(t - minute)))
        return share_t[:, j]
    base = (at(21*60) + at(24*60)) / 2.0
    feat["hump_22"] = ((at(22*60) + at(22*60+30)) / 2.0) - base
    # 7 dawn rebound: share 04:30-06:00 (weekend only meaningful)
    dawn = (t >= 28*60+30) & (t < 30*60)
    feat["dawn"] = share_t[:, dawn].sum(1) if dawn.any() else 0.0

    return feat


def cluster_diag(Xs, kmax=8):
    rows = []
    for k in range(2, kmax+1):
        gm = GaussianMixture(k, covariance_type="diag", n_init=20, random_state=RS).fit_predict(Xs)
        km = KMeans(k, n_init=20, random_state=RS).fit_predict(Xs)
        wd = AgglomerativeClustering(k, linkage="ward").fit_predict(Xs)
        rows.append({
            "K": k,
            "GMM_sil": round(silhouette_score(Xs, gm), 3), "GMM_CH": round(calinski_harabasz_score(Xs, gm)),
            "KM_sil": round(silhouette_score(Xs, km), 3), "KM_CH": round(calinski_harabasz_score(Xs, km)),
            "Ward_sil": round(silhouette_score(Xs, wd), 3),
            "GMM_DB": round(davies_bouldin_score(Xs, gm), 2),
        })
    return pd.DataFrame(rows)


def bootstrap_ari(Xs, k, n_boot=30):
    base = GaussianMixture(k, covariance_type="diag", n_init=10, random_state=RS).fit(Xs)
    ref = base.predict(Xs)
    aris = []
    rng = np.random.default_rng(RS)
    n = len(Xs)
    for _ in range(n_boot):
        idx = rng.choice(n, n, replace=True)
        gm = GaussianMixture(k, covariance_type="diag", n_init=5, random_state=int(rng.integers(1e6))).fit(Xs[idx])
        aris.append(adjusted_rand_score(ref, gm.predict(Xs)))
    return np.mean(aris), np.std(aris)


def main():
    raw = pd.read_parquet(INP)
    raw["day_type"] = raw["day_type"].astype(str)
    raw["NLC"] = raw["NLC"].astype(str)

    for group, days in GROUPS.items():
        feat = build_features(raw, days, SPLIT[group], WIN_END[group])
        feat.to_csv(OUTD / f"{group}_featv2.csv")
        Xs = StandardScaler().fit_transform(feat.values)

        print("\n" + "#"*64 + f"\n# RAIL {group}  (n={len(feat)} stations, {feat.shape[1]} features)\n" + "#"*64)
        print("feature correlation (abs>0.6 flagged):")
        corr = feat.corr()
        print(corr.round(2).to_string())

        diag = cluster_diag(Xs)
        diag.to_csv(OUTD / f"{group}_diag_v2.csv", index=False)
        print("\nK-ladder on v2 features (GMM vs KMeans vs Ward):")
        print(diag.to_string(index=False))

        print("\nbootstrap GMM stability (mean ARI +/- sd):")
        for k in (3, 4, 5):
            m, s = bootstrap_ari(Xs, k)
            print(f"  K={k}: {m:.3f} +/- {s:.3f}")

        # cross-model agreement at K=3
        gm = GaussianMixture(3, covariance_type="diag", n_init=20, random_state=RS).fit_predict(Xs)
        km = KMeans(3, n_init=20, random_state=RS).fit_predict(Xs)
        wd = AgglomerativeClustering(3, linkage="ward").fit_predict(Xs)
        print(f"\ncross-model ARI @K=3: GMM-KM={adjusted_rand_score(gm,km):.3f}  "
              f"GMM-Ward={adjusted_rand_score(gm,wd):.3f}  KM-Ward={adjusted_rand_score(km,wd):.3f}")

        # A-F scatter coloured by OLD labels
        old = pd.read_csv(OLD_LAB[group], dtype={"NLC": str}).set_index("NLC")["cluster"]
        old = old.reindex(feat.index)
        fig, ax = plt.subplots(figsize=(7.5, 6))
        sc = ax.scatter(feat["A_net"], feat["F_flip"], c=old.values, cmap="tab10", s=28,
                        edgecolor="white", linewidth=0.4)
        ax.set_xlabel("A_net  (entry-dominant >0  /  exit-dominant <0)")
        ax.set_ylabel("F_flip  (early-out→late-in >0)")
        ax.set_title(f"RAIL {group}: A_net vs F_flip, coloured by OLD cluster")
        ax.axhline(0, color="#aaa", lw=.7); ax.axvline(0, color="#aaa", lw=.7)
        plt.colorbar(sc, label="old cluster")
        fig.tight_layout(); fig.savefig(OUTD / f"{group}_AF_scatter.png", dpi=160)
        plt.close(fig)

    print("\nSaved feature tables, diagnostics, scatters ->", OUTD)


if __name__ == "__main__":
    main()
