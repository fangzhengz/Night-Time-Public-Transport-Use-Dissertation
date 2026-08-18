## 材料护照

- 来源: numbat_all_area_test 扩展检验(2026-07-22 起,含 01b 同址跨模式站点合并)
- 触发原因: 2026-07-17 会议记录中 Howard/Clara 的提问("why looking at just
  underground rather than all the rail stations within NUMBAT data?")
- 验证状态: 已核查(见下方复现方式)

# 地铁扩展检验:全部 NUMBAT 轨道站点 vs 仅 Underground

## 检验范围

本检验对比两个独立的 GMM 聚类结果:

1. **canonical(270 站)**:`cluster_clean_version_fullweek/`,只保留
   `has_lu == True` 的站点,即当前论文使用的 Underground 结果。
2. **all-modes(420 站)**:本文件夹新建的流水线,保留全部 NUMBAT
   轨道模式(LU、DLR、Overground、伊丽莎白线、电车),并对同一物理地点但
   跨模式分开记账的站点做了合并(`01b_merge_colocated_stations.py`,例如
   希思罗各航站楼的 Underground 侧与伊丽莎白线侧)。457 个合并后的原始
   站点中有 420 个在夜间时段有活动量(其余 37 个总活动量为0,
   按与 canonical 相同的 `MIN_TOTAL=1` 规则剔除)。

两者的 344 维特征定义(5 个原生日类型 × entry/exit × 各自窗口)完全一致,
GMM 方法学(`diag` 协方差、`n_init=20`、`random_state=42`、
`reg_covar=1e-6`)也完全一致,唯一差异是站点范围与站点合并规则。

## 数据覆盖的一个重要限制:电车站点结构性缺失

457 个原始站点中被剔除的 37 个,**全部**是电车(TRM)专属站点,
而且是唯一被剔除的类别(没有任何 DLR/Overground/伊丽莎白线站点被剔除):

| mode_label | n_dropped |
| ---------- | --------- |
| TRM        | 37        |

核查发现,这些电车站点在 `Station_Entries`/`Station_Exits` 两张表里,
全部日类型下的进出站计数都是0,不只是夜间时段是0。原因是伦敦电车没有闸机
(gateline),而 NUMBAT 的 Entries/Exits 统计方法学是基于闸机计数的;电车的
客流只出现在用不同方法(如车载计数)统计的 `Station_Boarders` 表里。因此,
"纳入全部 NUMBAT 轨道站点"这个检验**结构性地无法覆盖电车**,这是数据本身
的限制,不是本次预处理脚本的选择。DLR、Overground、伊丽莎白线的非
Underground 站点则都正常保留。

## 发现一:BIC 偏好的 K在合并同址站点后趋于一致

| K  | BIC_canonical | silhouette_canonical | BIC_allmodes | silhouette_allmodes |
| -- | ------------- | -------------------- | ------------ | ------------------- |
| 2  | -966684.406   | 0.316                | -1480613.702 | 0.316               |
| 3  | -971849.720   | 0.160                | -1490429.361 | 0.149               |
| 4  | -972699.323   | 0.183                | -1496338.960 | 0.130               |
| 5  | -974893.293   | 0.142                | -1499102.374 | 0.116               |
| 6  | -975013.528   | 0.141                | -1501451.394 | 0.087               |
| 7  | -974472.051   | 0.112                | -1499670.261 | 0.113               |
| 8  | -972937.521   | 0.104                | -1501283.843 | 0.092               |
| 9  | -971510.379   | 0.110                | -1499155.465 | 0.095               |
| 10 | -969691.461   | 0.119                | -1498731.701 | 0.060               |
| 11 | -967004.959   | 0.109                | -1496826.636 | 0.067               |
| 12 | -964990.499   | 0.121                | -1495004.701 | 0.083               |

- canonical(270 站,仅 Underground)BIC 最优在 **K=6**
  (K=5 与 K=6 非常接近,详见既有的
  `rail_k_selection_validation` 报告)。
- all-modes(420 站,全部轨道模式)BIC 最优在 **K=6**,
  且这不是网格边界效应——K=6 前后的 BIC 都比它差
  (K5=-1499102,
  K6=-1501451,
  K7=-1499670),是一个真实的内部极值。

**这也回答了 Howard 的问题,但方向和早期(未合并同址跨模式站点的)版本不同**:
把范围从"只用 Underground"扩大到"全部 NUMBAT 轨道站点"、并正确合并
希思罗各航站楼、金丝雀码头、尤斯顿等13处同址跨模式站点之后,BIC 最优
K **没有变**,两边都是 K=6。这本身是一个值得记录的发现:在
合并之前,all-modes 的 BIC 最优 K 曾经是7(见本文件夹更早的运行记录),
说明那次偏移**部分是同一物理站点被拆成多条记录造成的人为效应**,而不是
扩大站点范围本身带来的真实结构变化。合并之后,两个独立的站点范围在
BIC 这一项指标上给出了一致的答案。

## 发现二:原270站在新聚类中的簇归属稳定性

把 all-modes(420站)K=5 的结果限制回原来的270个 Underground 站点,与
canonical 的 K=5 标签计算 Adjusted Rand Index:

**ARI = 0.570**

一对一最佳匹配(匈牙利算法,按 Jaccard):

| canonical_k5_cluster | matched_allmodes_cluster | intersection | canonical_size | allmodes_subset_size | jaccard |
| -------------------- | ------------------------ | ------------ | -------------- | -------------------- | ------- |
| 0                    | 0                        | 118          | 119            | 153                  | 0.766   |
| 1                    | 3                        | 9            | 15             | 9                    | 0.600   |
| 2                    | 1                        | 15           | 44             | 16                   | 0.333   |
| 3                    | 2                        | 38           | 38             | 61                   | 0.623   |
| 4                    | 4                        | 30           | 54             | 31                   | 0.545   |

完整的簇交叉表(行=canonical 的5个簇,列=all-modes 的5个簇,限制在270个
Underground 站点上):

| canonical_cluster | allmodes_C0 | allmodes_C1 | allmodes_C2 | allmodes_C3 | allmodes_C4 |
| ----------------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| canonical_C0      | 118         | 0           | 0           | 0           | 1           |
| canonical_C1      | 0           | 1           | 5           | 9           | 0           |
| canonical_C2      | 13          | 15          | 16          | 0           | 0           |
| canonical_C3      | 0           | 0           | 38          | 0           | 0           |
| canonical_C4      | 22          | 0           | 2           | 0           | 30          |

## 发现三:新增的150个非 Underground 站点去了哪里

按站点所属模式分组(LU 单模式 / LU 与其他模式换乘 / DLR专属 / Overground
专属 / 伊丽莎白线专属 / 电车专属),与 all-modes K=5 的簇编号做交叉表
(420站全集,活动量筛选后剩余的站点):

| mode_group                    | 0   | 1  | 2  | 3 | 4  | total |
| ----------------------------- | --- | -- | -- | - | -- | ----- |
| LU only                       | 133 | 15 | 47 | 6 | 27 | 228   |
| LU + other mode (interchange) | 20  | 1  | 14 | 3 | 4  | 42    |
| DLR-only                      | 10  | 18 | 6  | 2 | 2  | 38    |
| Overground-only               | 27  | 1  | 27 | 1 | 24 | 80    |
| Elizabeth line-only           | 14  | 0  | 1  | 3 | 10 | 28    |
| other non-LU mix (DLR,EZL)    | 1   | 0  | 0  | 0 | 0  | 1     |
| other non-LU mix (DLR,LO)     | 0   | 1  | 0  | 0 | 0  | 1     |
| other non-LU mix (EZL,LO)     | 1   | 0  | 0  | 0 | 0  | 1     |
| other non-LU mix (LO,TRM)     | 0   | 0  | 0  | 0 | 1  | 1     |

按行归一化的占比:

| mode_group                    | 0     | 1     | 2     | 3     | 4     |
| ----------------------------- | ----- | ----- | ----- | ----- | ----- |
| LU only                       | 0.583 | 0.066 | 0.206 | 0.026 | 0.118 |
| LU + other mode (interchange) | 0.476 | 0.024 | 0.333 | 0.071 | 0.095 |
| DLR-only                      | 0.263 | 0.474 | 0.158 | 0.053 | 0.053 |
| Overground-only               | 0.338 | 0.013 | 0.338 | 0.013 | 0.300 |
| Elizabeth line-only           | 0.500 | 0.000 | 0.036 | 0.107 | 0.357 |
| other non-LU mix (DLR,EZL)    | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| other non-LU mix (DLR,LO)     | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| other non-LU mix (EZL,LO)     | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| other non-LU mix (LO,TRM)     | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |

## 有边界的结论

- 在正确合并同址跨模式站点之后,BIC 最优 K 在两个站点范围下**一致**(都是 K=6)——K 选择本身对"是否纳入全部轨道模式"并不像未合并版本显示的那么敏感,之前观察到的偏移主要来自站点记账粒度问题。
- 但原270个 Underground 站点在新聚类中的簇归属部分一致
  (ARI=0.570),说明新增的150站主要是在"补充"聚类结构,
  而不是从根本上重新洗牌 Underground 站点原有的分组。
- 因此,"只用 Underground"这一决定对**270站内部的分组结论**总体上是稳健的,在正确处理同址跨模式站点合并的前提下,BIC 对 K 的选择也是稳健的——这比单纯的簇归属稳定性(发现二)更强,因为它说明连"应该分几类"这个更基础的判断都不依赖于站点范围。

## 局限

- all-modes 的420站里有150个站点是本次检验才第一次纳入特征构建流程,没有
  经过与 canonical 270站同等程度的人工核查,尽管13处同址跨模式站点已在
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
