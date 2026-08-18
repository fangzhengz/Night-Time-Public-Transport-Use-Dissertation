# 数据与方法部分更新提醒

本次正式变量组合已经发生变化，提交前必须同步修改“Data and Methods”以及所有变量表、图题和附录说明。

## 必须修改的项目

1. 将原文中的“17项区域变量”改为“18项正式区域背景变量”，其中包含17项解释性背景指标和1项人口密度控制变量。若你的计数方式把控制变量单列，应明确写成“17项背景指标，另加人口密度控制变量”，全文保持一致。
2. 从正式变量清单中删除车辆拥有/无车家庭指标 `no_car_household_share`。原始 TS045 数据仅为分析追溯保留，不再进入 Kruskal-Wallis、cluster-versus-rest 检验、热图、箱线图、相关矩阵或 cluster panels。
3. 在 Urban function / Facilities 数据段加入 OS Points of Interest：June 2026 release；EDINA Digimap 下载日期为 7 August 2026；GeoPackage 图层为 `Points of Interest 2026_06`。
4. 增加两个正式设施指标：`log1p_poi_count` 与 `shannon_group`。
5. 将只写“社会经济变量”的地方改成“区域背景变量”或“社会经济、就业、家庭、住房与设施背景”，因为正式组合现在包含设施功能层。
6. 更新方法流程图、变量表、图注和附录中的检验数量：Bus 为 4 x 18 = 72 个 cluster-versus-rest cells；Rail 为 5 x 18 = 90 个。

## 可直接改写进方法部分的中文草稿

为补充 LNWC 和 LOAC 对夜间工作地理及综合地区类型的刻画，研究进一步引入 Ordnance Survey Points of Interest 数据描述不同交通使用类型所处地区的设施活动强度与功能多样性。所用数据为 OS Points of Interest June 2026 release，通过 EDINA Digimap 下载。数据中的八位设施分类编码被汇总至九个顶层 POI Groups。对于每个 LSOA，设施强度以 POI 总量表示，并在统计检验前采用 `log(1+x)` 转换；设施多样性则采用未经归一化的 Shannon 指数计算：`H = -sum(p_i ln p_i)`，其中 `p_i` 为第 i 类 POI Group 在该空间单元全部设施中的比例。指数越高，表示设施类型的丰富度和均衡度越高。

Bus 分析直接采用各 LSOA 的设施指标。Rail 分析首先在 LSOA 层面计算 POI 总量与 Shannon 指数，再按照既有800米 Voronoi-clipped station catchment 所相交的不同 LSOA 进行等权平均；POI 总量在完成 Rail catchment 汇总后再作 `log(1+x)` 转换。该处理与其他区域背景变量的 Rail 汇总口径保持一致，也避免改变既有 Rail 和 Bus 聚类样本及标签。设施变量仅在聚类完成后用于外部背景刻画，不参与聚类模型拟合。

最终正式变量组合取消了无车家庭比例。该指标与伦敦中心—外围地区的居住结构高度重合，且容易将中心区较少常住人口、家庭结构和车辆拥有情况误读为交通脆弱性或乘客特征。TS045 原始变量仍保留于可追溯数据表中，但不进入正式统计检验和图形。新的正式组合包含18项变量，并分别使用 Kruskal-Wallis 检验和 epsilon-squared 效应量评估各变量与聚类的总体关联；随后采用 cluster-versus-rest Mann-Whitney U 检验描述各簇相对于其余区域的特征，并在每种交通模式内对全部 cells 进行 Benjamini-Hochberg 校正。

## 解释边界

设施总量与 Shannon 指数描述的是空间单元的地区功能背景，而不是乘客实际访问的设施，也不证明设施构成造成某种夜间交通使用模式。Rail 与 Bus 的空间单元和汇总方式不同，结果应分别解释，不能把效应量直接当作严格的跨模式比较。
