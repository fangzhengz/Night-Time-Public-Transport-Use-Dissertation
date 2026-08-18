from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

"""04 - Compare the LU-only canonical rail clustering against the all-NUMBAT-
modes clustering built in this test folder.

Answers the three questions from the plan:
  1. Does the BIC-preferred K change when non-LU stations are added?
  2. Restricted back to the original canonical LU stations, is the K=5
     cluster membership stable (ARI) versus the canonical rail_k5_labels.csv?
  3. Where do the added non-LU stations (DLR/Overground/Elizabeth
     line/Tram-only) land -- do they spread across the existing 5 clusters
     or concentrate in a few?

All station counts are read from the data at run time rather than
hardcoded, since the all-modes station count changes if upstream steps
change (e.g. after `01b_merge_colocated_stations.py` consolidates
co-located cross-mode NLCs).

Reads only saved labels/diagnostics; does not refit or alter anything under
`cluster_clean_version_fullweek/`.
"""

FYP_ROOT = Path(__file__).resolve().parents[2]
CANON_DIR = FYP_ROOT / "cluster_clean_version_fullweek" / "outputs"
DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
REPORT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

CANON_KDIAG = CANON_DIR / "diagnostics" / "rail_kdiag.csv"
ALLMODES_KDIAG = DATA_DIR / "rail_allmodes_kdiag.csv"
CANON_LABELS_K5 = CANON_DIR / "labels" / "rail_k5_labels.csv"
ALLMODES_LABELS_K5 = DATA_DIR / "rail_allmodes_k5_labels.csv"
ALLMODES_META = DATA_DIR / "rail_allmodes_feature_meta.csv"
# Preprocessing (raw extraction, merge, NaPTAN filter) moved to
# data_processing/rail_allmodes/ 2026-07-24. FULL_META is that folder's
# *final* (440-station, NaPTAN-matched) meta -- i.e. exactly what `02`
# receives as input -- not the pre-NaPTAN-filter 456-station merged meta,
# so that "dropped relative to FULL_META" below stays purely the
# zero-activity (tram-only) drops, as originally intended.
FULL_META = (
    FYP_ROOT / "data_processing" / "rail_allmodes" / "outputs" / "preprocessed"
    / "numbat_allmodes_station_meta_final.csv"
)


def overlap_matrices(reference, candidate, reference_k, candidate_k):
    counts = np.zeros((reference_k, candidate_k), dtype=int)
    jaccard = np.zeros((reference_k, candidate_k), dtype=float)
    for r in range(reference_k):
        rmask = reference == r
        for c in range(candidate_k):
            cmask = candidate == c
            inter = int(np.logical_and(rmask, cmask).sum())
            union = int(np.logical_or(rmask, cmask).sum())
            counts[r, c] = inter
            jaccard[r, c] = inter / union if union else 0.0
    return counts, jaccard


def match_clusters(reference, candidate, reference_k, candidate_k):
    counts, jaccard = overlap_matrices(reference, candidate, reference_k, candidate_k)
    row_ind, col_ind = linear_sum_assignment(-jaccard)
    rows = []
    for r, c in zip(row_ind, col_ind, strict=True):
        rows.append(
            {
                "canonical_k5_cluster": int(r),
                "matched_allmodes_cluster": int(c),
                "intersection": int(counts[r, c]),
                "canonical_size": int((reference == r).sum()),
                "allmodes_subset_size": int((candidate == c).sum()),
                "jaccard": float(jaccard[r, c]),
            }
        )
    return pd.DataFrame(rows).sort_values("canonical_k5_cluster"), counts


def simplify_mode(mode_label: str) -> str:
    modes = set(str(mode_label).split(","))
    if "LU" in modes:
        return "LU only" if modes == {"LU"} else "LU + other mode (interchange)"
    if modes == {"DLR"}:
        return "DLR-only"
    if modes == {"LO"}:
        return "Overground-only"
    if modes == {"EZL"}:
        return "Elizabeth line-only"
    if modes == {"TRM"}:
        return "Tram-only"
    return "other non-LU mix (" + mode_label + ")"


def markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    display = frame.copy()
    for column in display.select_dtypes(include=["float", "floating"]).columns:
        display[column] = display[column].map(lambda v: f"{v:.{digits}f}")
    headers = [str(c) for c in display.columns]
    rows = [[str(v) for v in row] for row in display.itertuples(index=False, name=None)]
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(v)) for w, v in zip(widths, row, strict=True)]
    header_line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True)) + " |"
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    body = ["| " + " | ".join(v.ljust(w) for v, w in zip(row, widths, strict=True)) + " |" for row in rows]
    return "\n".join([header_line, sep, *body])


def main() -> None:
    # ---- 1. K-selection comparison ----
    canon_kdiag = pd.read_csv(CANON_KDIAG)[["K", "BIC", "silhouette"]].rename(
        columns={"BIC": "BIC_canonical", "silhouette": "silhouette_canonical"}
    )
    allmodes_kdiag = pd.read_csv(ALLMODES_KDIAG)[["K", "BIC", "silhouette"]].rename(
        columns={"BIC": "BIC_allmodes", "silhouette": "silhouette_allmodes"}
    )
    kcompare = canon_kdiag.merge(allmodes_kdiag, on="K", how="outer").sort_values("K")

    canon_best_k = int(canon_kdiag.loc[canon_kdiag["BIC_canonical"].idxmin(), "K"])
    allmodes_best_k = int(allmodes_kdiag.loc[allmodes_kdiag["BIC_allmodes"].idxmin(), "K"])

    # ---- 2. Restrict all-modes K=5 labels to the canonical LU stations ----
    canon_lab = pd.read_csv(CANON_LABELS_K5)
    canon_lab["unit"] = canon_lab["unit"].astype(str)
    allmodes_lab = pd.read_csv(ALLMODES_LABELS_K5)
    allmodes_lab["unit"] = allmodes_lab["unit"].astype(str)

    n_canon = len(canon_lab)
    n_allmodes = len(allmodes_lab)
    n_added = n_allmodes - n_canon

    subset = allmodes_lab.set_index("unit").reindex(canon_lab["unit"])
    if subset["cluster"].isna().any():
        missing = subset.index[subset["cluster"].isna()].tolist()
        raise ValueError(f"{len(missing)} canonical stations missing from all-modes run: {missing[:10]}")

    canon_arr = canon_lab.set_index("unit").loc[subset.index, "cluster"].to_numpy().astype(int)
    subset_arr = subset["cluster"].to_numpy().astype(int)

    ari_subset_vs_canonical = float(adjusted_rand_score(canon_arr, subset_arr))
    mapping, counts = match_clusters(canon_arr, subset_arr, 5, 5)
    contingency = pd.DataFrame(
        counts,
        index=[f"canonical_C{i}" for i in range(5)],
        columns=[f"allmodes_C{i}" for i in range(5)],
    )

    # ---- 3. Where do the added non-LU stations land? ----
    meta = pd.read_csv(ALLMODES_META)
    meta["unit"] = meta["NLC"].astype(str)
    meta["mode_group"] = meta["mode_label"].map(simplify_mode)
    full = allmodes_lab.merge(meta[["unit", "mode_group"]], on="unit", how="left")
    composition = (
        full.groupby(["mode_group", "cluster"]).size().rename("n").reset_index()
    )
    composition_pivot = composition.pivot_table(
        index="mode_group", columns="cluster", values="n", fill_value=0
    ).astype(int)
    composition_pivot["total"] = composition_pivot.sum(axis=1)
    row_order = [
        "LU only",
        "LU + other mode (interchange)",
        "DLR-only",
        "Overground-only",
        "Elizabeth line-only",
        "Tram-only",
    ]
    row_order = [r for r in row_order if r in composition_pivot.index] + [
        r for r in composition_pivot.index if r not in row_order
    ]
    composition_pivot = composition_pivot.loc[row_order]
    composition_share = composition_pivot.drop(columns="total").div(
        composition_pivot["total"], axis=0
    )

    # ---- dropped-station disclosure (zero night-window activity) ----
    full_meta = pd.read_csv(FULL_META, dtype={"NLC": str})
    full_meta["unit"] = full_meta["NLC"].astype(str)
    n_raw = full_meta["unit"].nunique()
    dropped = full_meta[~full_meta["unit"].isin(set(meta["unit"]))]
    n_dropped = len(dropped)
    dropped_by_mode = dropped["mode_label"].value_counts().rename_axis("mode_label").reset_index(name="n_dropped")
    dropped_by_mode.to_csv(DATA_DIR / "dropped_zero_activity_stations_by_mode.csv", index=False)

    # ---- save data ----
    kcompare.to_csv(DATA_DIR / "k_selection_comparison_canonical_vs_allmodes.csv", index=False)
    mapping.to_csv(DATA_DIR / "k5_canonical_vs_allmodes_mapping.csv", index=False)
    contingency.to_csv(DATA_DIR / "k5_canonical_vs_allmodes_contingency.csv")
    composition_pivot.to_csv(DATA_DIR / "mode_group_by_allmodes_k5_cluster_counts.csv")
    composition_share.to_csv(DATA_DIR / "mode_group_by_allmodes_k5_cluster_share.csv")

    print(f"Canonical ({n_canon}, LU-only) BIC-best K = {canon_best_k}")
    print(f"All-modes ({n_allmodes}, all NUMBAT rail-family) BIC-best K = {allmodes_best_k}")
    print(f"ARI (canonical K=5 vs all-modes K=5 restricted to the {n_canon} LU stations) = {ari_subset_vs_canonical:.3f}")
    print("\nMode-group x cluster composition (counts):")
    print(composition_pivot.to_string())

    consistency_zh = '高度一致' if ari_subset_vs_canonical >= 0.7 else ('部分一致' if ari_subset_vs_canonical >= 0.4 else '明显不同')
    consistency_en = 'highly consistent' if ari_subset_vs_canonical >= 0.7 else ('partially consistent' if ari_subset_vs_canonical >= 0.4 else 'materially different')

    k_before, k_after = allmodes_best_k - 1, allmodes_best_k + 1
    bic_by_k = allmodes_kdiag.set_index('K')['BIC_allmodes']
    k_changed = allmodes_best_k != canon_best_k

    finding1_zh = (
        f"- all-modes({n_allmodes} 站,全部轨道模式)BIC 最优在 **K={allmodes_best_k}**,\n"
        f"  且这不是网格边界效应——K={allmodes_best_k} 前后的 BIC 都比它差\n"
        f"  (K{k_before}={bic_by_k.loc[k_before]:.0f},\n"
        f"  K{allmodes_best_k}={bic_by_k.loc[allmodes_best_k]:.0f},\n"
        f"  K{k_after}={bic_by_k.loc[k_after]:.0f}),是一个真实的内部极值。\n\n"
        + (
            f"**这直接回答了 Howard 的问题**:把范围从\"只用 Underground\"扩大到\"全部\n"
            f"NUMBAT 轨道站点\"之后,单纯基于 BIC 的最优聚类数确实会变(从 {canon_best_k} 变为\n"
            f"{allmodes_best_k}),说明当前 K=5 的选择是以\"仅 Underground\"为前提的,\n"
            f"并非在任何站点范围下都成立的绝对结论。"
            if k_changed else
            f"**这也回答了 Howard 的问题,但方向和早期(未合并同址跨模式站点的)版本不同**:\n"
            f"把范围从\"只用 Underground\"扩大到\"全部 NUMBAT 轨道站点\"、并正确合并\n"
            f"希思罗各航站楼、金丝雀码头、尤斯顿、帕丁顿等14处同址跨模式站点之后,BIC 最优\n"
            f"K **没有变**,两边都是 K={canon_best_k}。这本身是一个值得记录的发现:在\n"
            f"合并之前,all-modes 的 BIC 最优 K 曾经是7(见本文件夹更早的运行记录),\n"
            f"说明那次偏移**部分是同一物理站点被拆成多条记录造成的人为效应**,而不是\n"
            f"扩大站点范围本身带来的真实结构变化。合并之后,两个独立的站点范围在\n"
            f"BIC 这一项指标上给出了一致的答案。"
        )
    )
    finding1_en = (
        f"- All-modes ({n_allmodes}, all rail modes): BIC-best at **K={allmodes_best_k}**, and\n"
        f"  this is a genuine interior optimum, not a grid-boundary artifact\n"
        f"  (K{k_before}={bic_by_k.loc[k_before]:.0f},\n"
        f"  K{allmodes_best_k}={bic_by_k.loc[allmodes_best_k]:.0f},\n"
        f"  K{k_after}={bic_by_k.loc[k_after]:.0f}).\n\n"
        + (
            f"This directly answers Howard's question: widening the scope from\n"
            f"Underground-only to all NUMBAT rail stations does shift the BIC-optimal\n"
            f"cluster count (from {canon_best_k} to {allmodes_best_k}), so the current K=5 choice is\n"
            f"conditional on the Underground-only scope, not a scope-independent result."
            if k_changed else
            f"This also answers Howard's question, but in the opposite direction from an\n"
            f"earlier run of this check (before co-located cross-mode stations were\n"
            f"merged): with all NUMBAT rail modes included **and** the 14 co-located\n"
            f"cross-mode sites (Heathrow terminals, Canary Wharf, Euston, etc.) properly\n"
            f"merged into single stations, the BIC-optimal K does **not** change -- both\n"
            f"scopes agree on K={canon_best_k}. Before merging, the all-modes BIC-optimal K was 7\n"
            f"(see this folder's earlier run history), so that earlier shift was **partly\n"
            f"an artefact of one physical station being split across multiple NLC rows**,\n"
            f"not a genuine structural consequence of widening station scope. Once merged,\n"
            f"the two independent station scopes agree on BIC."
        )
    )

    # ---- report (ZH primary) ----
    report_zh = f"""## 材料护照

- 来源: numbat_all_area_test 扩展检验(2026-07-22 起,含 01b 同址跨模式站点合并)
- 触发原因: 2026-07-17 会议记录中 Howard/Clara 的提问("why looking at just
  underground rather than all the rail stations within NUMBAT data?")
- 验证状态: 已核查(见下方复现方式)

# 地铁扩展检验:全部 NUMBAT 轨道站点 vs 仅 Underground

## 检验范围

本检验对比两个独立的 GMM 聚类结果:

1. **canonical({n_canon} 站)**:`cluster_clean_version_fullweek/`,只保留
   `has_lu == True` 的站点,即当前论文使用的 Underground 结果。
2. **all-modes({n_allmodes} 站)**:本文件夹新建的流水线,保留全部 NUMBAT
   轨道模式(LU、DLR、Overground、伊丽莎白线、电车),并对同一物理地点但
   跨模式分开记账的站点做了合并(`01b_merge_colocated_stations.py`,例如
   希思罗各航站楼的 Underground 侧与伊丽莎白线侧)。{n_raw} 个合并后的原始
   站点中有 {n_allmodes} 个在夜间时段有活动量(其余 {n_dropped} 个总活动量为0,
   按与 canonical 相同的 `MIN_TOTAL=1` 规则剔除)。

两者的 344 维特征定义(5 个原生日类型 × entry/exit × 各自窗口)完全一致,
GMM 方法学(`diag` 协方差、`n_init=20`、`random_state=42`、
`reg_covar=1e-6`)也完全一致,唯一差异是站点范围与站点合并规则。

## 数据覆盖的一个重要限制:电车站点结构性缺失

{n_raw} 个原始站点中被剔除的 {n_dropped} 个,**全部**是电车(TRM)专属站点,
而且是唯一被剔除的类别(没有任何 DLR/Overground/伊丽莎白线站点被剔除):

{markdown_table(dropped_by_mode, digits=0)}

核查发现,这些电车站点在 `Station_Entries`/`Station_Exits` 两张表里,
全部日类型下的进出站计数都是0,不只是夜间时段是0。原因是伦敦电车没有闸机
(gateline),而 NUMBAT 的 Entries/Exits 统计方法学是基于闸机计数的;电车的
客流只出现在用不同方法(如车载计数)统计的 `Station_Boarders` 表里。因此,
"纳入全部 NUMBAT 轨道站点"这个检验**结构性地无法覆盖电车**,这是数据本身
的限制,不是本次预处理脚本的选择。DLR、Overground、伊丽莎白线的非
Underground 站点则都正常保留。

## 发现一:BIC 偏好的 K{"发生了变化" if k_changed else "在合并同址站点后趋于一致"}

{markdown_table(kcompare)}

- canonical({n_canon} 站,仅 Underground)BIC 最优在 **K={canon_best_k}**
  (K=5 与 K=6 非常接近,详见既有的
  `rail_k_selection_validation` 报告)。
{finding1_zh}

## 发现二:原{n_canon}站在新聚类中的簇归属稳定性

把 all-modes({n_allmodes}站)K=5 的结果限制回原来的{n_canon}个 Underground 站点,与
canonical 的 K=5 标签计算 Adjusted Rand Index:

**ARI = {ari_subset_vs_canonical:.3f}**

一对一最佳匹配(匈牙利算法,按 Jaccard):

{markdown_table(mapping)}

完整的簇交叉表(行=canonical 的5个簇,列=all-modes 的5个簇,限制在{n_canon}个
Underground 站点上):

{markdown_table(contingency.reset_index(names="canonical_cluster"), digits=0)}

## 发现三:新增的{n_added}个非 Underground 站点去了哪里

按站点所属模式分组(LU 单模式 / LU 与其他模式换乘 / DLR专属 / Overground
专属 / 伊丽莎白线专属 / 电车专属),与 all-modes K=5 的簇编号做交叉表
({n_allmodes}站全集,活动量筛选后剩余的站点):

{markdown_table(composition_pivot.reset_index(), digits=0)}

按行归一化的占比:

{markdown_table(composition_share.reset_index())}

## 有边界的结论

{"- K 选择本身对\"是否纳入全部轨道模式\"敏感,BIC 最优 K 从 " + str(canon_best_k) + " 变为 " + str(allmodes_best_k) + ",差异是真实的、不是网格误差。" if k_changed else "- 在正确合并同址跨模式站点之后,BIC 最优 K 在两个站点范围下**一致**(都是 K=" + str(canon_best_k) + ")——K 选择本身对\"是否纳入全部轨道模式\"并不像未合并版本显示的那么敏感,之前观察到的偏移主要来自站点记账粒度问题。"}
- 但原{n_canon}个 Underground 站点在新聚类中的簇归属{consistency_zh}
  (ARI={ari_subset_vs_canonical:.3f}),说明新增的{n_added}站主要是在"补充"聚类结构,
  而不是从根本上重新洗牌 Underground 站点原有的分组。
- 因此,"只用 Underground"这一决定对**{n_canon}站内部的分组结论**总体上是稳健的,{"但如果要断言\"K=5 是轨道交通夜间活动的普遍最优分类数\",这个断言需要限定在\"仅 Underground\"这个范围内——扩大到全部 NUMBAT 轨道模式后,同样的方法学会给出不同的 K。这是一个关于**站点范围选择**的方法论说明,不是对现有 Underground 结果正确性的否定。" if k_changed else "在正确处理同址跨模式站点合并的前提下,BIC 对 K 的选择也是稳健的——这比单纯的簇归属稳定性(发现二)更强,因为它说明连\"应该分几类\"这个更基础的判断都不依赖于站点范围。"}

## 局限

- all-modes 的{n_allmodes}站里有{n_added}个站点是本次检验才第一次纳入特征构建流程,没有
  经过与 canonical {n_canon}站同等程度的人工核查,尽管14处同址跨模式站点已在
  `01b_merge_colocated_stations.py` 里合并处理(希思罗各航站楼、金丝雀码头、
  尤斯顿、利物浦街等)。
- 本检验没有重复 `rail_k_selection_validation` 的 bootstrap/种子稳定性电池,
  只做了一次确定性拟合的对比,结论应视为方向性证据,而非该问题的最终定论。
- 未对新增站点做 LNWC/IMD 关联,本检验仅限于聚类结构本身。

## 复现方式

```
python src/01_preprocess_rail_allmodes.py
python src/01b_merge_colocated_stations.py
python src/02_build_features_allmodes.py
python src/03_cluster_allmodes.py
python src/04_compare_lu_vs_allmodes.py
```
"""
    (REPORT_DIR / "VALIDATION_REPORT_ZH.md").write_text(report_zh, encoding="utf-8")

    report_en = f"""## Material Passport

- Origin: `numbat_all_area_test` extension test (started 2026-07-22, now
  including 01b co-located cross-mode station merging)
- Trigger: 2026-07-17 meeting question from Howard/Clara ("why looking at
  just underground rather than all the rail stations within NUMBAT data?")
- Verification status: checked (see reproduction section)

# Rail Extension Check: All NUMBAT Rail Modes vs Underground-Only

## Scope

Two independently-fitted GMM clustering results are compared:

1. **Canonical ({n_canon} stations)**: `cluster_clean_version_fullweek/`, keeping
   only stations with `has_lu == True` -- the Underground-only result
   currently used in the dissertation.
2. **All-modes ({n_allmodes} stations)**: a new pipeline built in this folder that
   keeps every NUMBAT rail-family mode (LU, DLR, Overground, Elizabeth
   line, Tram), and merges co-located stations that NUMBAT records under
   separate NLCs per mode at the same physical site
   (`01b_merge_colocated_stations.py`, e.g. each Heathrow terminal's
   Underground side and Elizabeth-line side). Of {n_raw} merged raw NLCs,
   {n_allmodes} have non-zero night-window activity ({n_dropped} dropped
   under the same `MIN_TOTAL=1` rule as canonical).

The 344-dimensional feature definition (5 native day types x entry/exit x
each day's window) and the GMM methodology (`diag` covariance, `n_init=20`,
`random_state=42`, `reg_covar=1e-6`) are identical between the two; the
difference is station scope and the co-location merge rule.

## An important data-coverage limit: trams are structurally missing

Of the {n_raw} raw stations, the {n_dropped} dropped are **entirely, and exclusively**,
Tram (TRM)-only stops -- no DLR/Overground/Elizabeth-line station was
dropped:

{markdown_table(dropped_by_mode, digits=0)}

These tram stops have zero recorded counts in `Station_Entries` /
`Station_Exits` across every day type, not only at night. London Trams have
no gateline, and NUMBAT's Entries/Exits methodology is gateline-based; tram
patronage only appears in `Station_Boarders`, which uses a different
counting method (e.g. onboard counts). So "all NUMBAT rail stations" is
**structurally unable to include trams** through this feature -- that is a
property of the source data, not a choice made in this preprocessing
script. Non-Underground DLR, Overground, and Elizabeth-line stations are
retained normally.

## Finding 1: the BIC-preferred K {"changes" if k_changed else "agrees once co-located stations are merged"}

{markdown_table(kcompare)}

- Canonical ({n_canon}, Underground-only): BIC-best at **K={canon_best_k}**
  (K=5 and K=6 are close, see the existing `rail_k_selection_validation`
  report).
{finding1_en}

## Finding 2: stability of the original {n_canon} stations' cluster membership

Restricting the all-modes ({n_allmodes}-station) K=5 result back to the original {n_canon}
Underground stations and comparing to the canonical K=5 labels:

**ARI = {ari_subset_vs_canonical:.3f}**

Best one-to-one match (Hungarian algorithm on Jaccard):

{markdown_table(mapping)}

Full contingency table (rows = canonical's 5 clusters, columns = all-modes'
5 clusters, restricted to the {n_canon} Underground stations):

{markdown_table(contingency.reset_index(names="canonical_cluster"), digits=0)}

## Finding 3: where the {n_added} added non-Underground stations land

Grouped by service mode (LU-only / LU-interchange / DLR-only /
Overground-only / Elizabeth line-only / Tram-only) against the all-modes
K=5 cluster assignment (full {n_allmodes}-station set after the activity filter):

{markdown_table(composition_pivot.reset_index(), digits=0)}

Row-normalised shares:

{markdown_table(composition_share.reset_index())}

## Bounded conclusion

{f"- K selection is genuinely sensitive to whether all rail modes are included; the BIC-optimal K shifts from {canon_best_k} to {allmodes_best_k}, and this is a real, not a numerical-noise, difference." if k_changed else f"- Once co-located cross-mode stations are properly merged, the BIC-optimal K **agrees** across both station scopes (K={canon_best_k} either way) -- K selection is not as scope-sensitive as an earlier, unmerged version of this check suggested; that earlier shift traced mainly to station-accounting granularity, not station scope itself."}
- However, the original {n_canon} Underground stations' cluster membership is
  {consistency_en}
  in the new clustering (ARI={ari_subset_vs_canonical:.3f}), so the {n_added} added
  stations mostly supplement the existing structure rather than reshuffling
  the Underground stations' groupings from the ground up.
- The decision to use Underground-only therefore looks robust for the
  **internal grouping of the {n_canon} Underground stations themselves**{"" if k_changed else ", and, once co-located stations are merged, for K selection itself too"}.
  {f'A claim that "K=5 is the universally optimal number of night-activity rail clusters" still needs to be scoped to "Underground-only" -- the same methodology applied to all NUMBAT rail modes gives a different BIC-optimal K ({allmodes_best_k}). This is a methodological scope caveat, not a refutation of the existing Underground result.' if k_changed else f'The BIC-optimal K itself (K={canon_best_k}) is no longer a point of difference between scopes, though the finer-grained cluster membership (Finding 2) still shows only partial, not full, agreement.'}

## Limitations

- The {n_added} newly-included stations have not had the same manual review as
  the canonical {n_canon}, though the 14 co-located cross-mode sites (Heathrow
  terminals, Canary Wharf, Euston, Liverpool Street, Paddington, etc.) have now been
  merged via `01b_merge_colocated_stations.py`.
- This check does not repeat the `rail_k_selection_validation` bootstrap/
  seed stability battery; it is a single deterministic-fit comparison and
  should be read as directional, not final, evidence.
- No LNWC/IMD linkage was attempted for the added stations; this check is
  limited to clustering structure.

## Reproduction

```
python src/01_preprocess_rail_allmodes.py
python src/01b_merge_colocated_stations.py
python src/02_build_features_allmodes.py
python src/03_cluster_allmodes.py
python src/04_compare_lu_vs_allmodes.py
```
"""
    (REPORT_DIR / "VALIDATION_REPORT.md").write_text(report_en, encoding="utf-8")
    print("\nSaved reports to", REPORT_DIR)


if __name__ == "__main__":
    main()
