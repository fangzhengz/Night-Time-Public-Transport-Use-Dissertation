# Spatial Signatures 试验结果与写作建议

## 结论

Spatial Signatures 可以保留为 RQ2 的补充背景层。它提供的是区域城市形态与功能分类，能够补充 Census 居民变量无法直接描述 CBD、都市功能强度、郊区住宅环境和仓储/公园用地的问题。它不应作为聚类输入，也不宜与现有 17 个连续社会经济变量混合为同一组 z-score 指标。

## 固定范围与转换

- Rail 继续使用既定 all-modes K=5 标签，Bus 继续使用既定 StopArea CLR K=4 标签；没有重新拟合聚类。
- Spatial Signatures 来源年份为 2020，原始空间单位为 LSOA11。
- 通过 ONS exact-fit V3 lookup 转换到 LSOA21，保留未变化、拆分和合并关系；伦敦 4,994 个 LSOA21 全部覆盖。
- Bus 的 3,372 个拟合 LSOA 全部匹配。
- Rail 沿用现有 RQ2 的严格 Greater London 背景分析范围：404 个聚类站点中 388 个具有可用背景。其余 16 个站点均位于严格 GLA 边界外，且都属于 C3。
- Rail 主分析对 800 m Voronoi-clipped catchment 内相交 LSOA 等权平均；面积加权作为敏感性检验。

## 总体关联

- Bus 主导类型与聚类的 Cramer's V 为 0.226，置换 p=0.001；完整类型构成的置换 R² 为 0.022，p=0.001。
- Rail 主导类型的 Cramer's V 为 0.417，置换 p=0.001；但 65.0% 的期望频数小于 5，因此不宜把列联表的渐近显著性作为核心证据。
- Rail 完整类型构成的置换 R² 为 0.119，p=0.001；面积加权结果为 R²=0.111，p=0.001。
- Rail 两种汇总方式的主导类型一致率为 90.5%，ARI=0.831，说明主要叙述不依赖单一汇总方案。
- 在中心距离五分位内进行条件置换后，Rail 与 Bus 的 p 值均为 0.001。这说明结果不只是简单复现中心—外围距离梯度，但该检验仍不能消除空间自相关。

## 最有价值的结果故事

Rail 的差异较清晰，适合作为正文重点：

- C2 中心出发主导型的 catchment 高度集中于城市功能强度较高的类型。Local、concentrated、regional、metropolitan 和 hyper-concentrated urbanity 合计约占 92.2%，为 CBD/中心活动区的功能解读提供了比居民特征更直接的区域背景。
- C3 外围到达主导型的构成更分散，并较多表现为 dense/connected residential neighbourhoods、accessible suburbia、open sprawl 和 warehouse/park land；上述五类 urbanity 合计仅约 12.9%。该对照支持 C2 与 C3 的中心功能区—外围居住区差异，但仍属于区域情境关联。
- C0 夜间持续型主要由 local urbanity 与 dense urban neighbourhoods 构成，两者合计约 82.9%。这为其内伦敦夜间持续使用提供了城市环境背景，但不能据此识别实际乘客或出行目的。
- C1 样本只有 12 个站点，且类型构成混合，不应强行概括成单一功能类型。其 Heathrow 与其他非典型站点可作为案例解释，但不宜成为总体推断。

Bus 的结果更适合写成连续梯度，而不是逐簇定义：

- C1 高活动、夜间持续型更集中于 dense urban neighbourhoods、local urbanity 与 regional/metropolitan urbanity。
- C3 低活动、外围倾向型具有更高的 accessible suburbia、urban buffer、open sprawl 和 warehouse/park land 构成，并具有更低的 local urbanity。
- C0 和 C2 多数类型构成位于上述两端之间。完整构成 R² 只有 0.022，也与 Bus 聚类边界较模糊、整体更接近连续谱的既有判断一致。

## 正文使用建议

正文可加入一个独立小节，例如 “Urban-form and functional context: Spatial Signatures”。建议用 Rail/Bus 类型构成热图作为主图，以 C2—C3、C0 以及 Bus C1—C3 为选择性叙述对象。主导类型地图和完整列联表放入附录。不要对 15 个类型或每个聚类逐一平摊描述，也不要进行 Rail 与 Bus 效应量的严格高低比较，因为两种模式的分析单位不同。

