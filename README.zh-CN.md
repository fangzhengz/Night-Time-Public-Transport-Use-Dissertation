# 仓库说明（中文）

伦敦入夜后的公共交通并不是一种均质的活动。不同 Rail 站点和 Bus 服务地区在活动强度、方向性、持续时间以及周末变化上呈现出不同节奏，而这些节奏又嵌入不同的城市功能与社会空间背景。本仓库沿着论文的实际研究逻辑展开：先分别识别 Rail 与 Bus 的夜间使用类型，再考察这些类型与夜间工作和更广泛地区特征之间的联系。

它既是已提交论文的复现入口，也是研究过程的保存空间。主目录只呈现论文最终采用的分析路线；另设的研究记录则保留试错、稳定性与敏感性检验、替代背景分析和后来放弃的问题。仓库继续使用论文中已经引用的原 GitHub 地址。

最终口径为：18:00–05:00；Rail 403 个站点、对角协方差 GMM K=5；Bus 3,383 个 LSOA、CLR 转换、全协方差 GMM K=4；Rail 情境使用 800m Voronoi 截断缓冲区，389 个站点进入正式情境分析。

最方便的阅读顺序是：

1. [`README.md`](README.md)：研究口径和仓库入口；
2. [`docs/analysis_manifest.md`](docs/analysis_manifest.md)：论文结果—代码—数据—输出的逐项映射；
3. [`docs/metric_dictionary.md`](docs/metric_dictionary.md)：解释原始值、z-score、效应量和检验统计量之间的区别；
4. [`results/tables/`](results/tables/)：最终统计表；
5. [`results/figures/`](results/figures/)：按内容命名的最终图；
6. [`research_record/`](research_record/)：与最终管路隔离的35项试验、敏感性、弃用 RQ3 和探索性分析记录；
7. [`paper/CASA0010_dissertation_FangzhengZhou.pdf`](paper/CASA0010_dissertation_FangzhengZhou.pdf)：原样保留的已提交论文。

GitHub 不分发受许可限制的原始 NUMBAT、BUSTO 和 OS Points of Interest 数据；仓库提供来源、校验边界和完整代码。分析代码按论文顺序位于 `analysis/01_data_preparation` 至 `analysis/05_reporting`。原始数据默认从仓库相对目录 [`authorised_data/`](authorised_data/README.md) 读取，不依赖任何 Windows 盘符；导师也可以使用 `--source-root` 指向其电脑上的任意授权数据目录。`python scripts/validate_repository.py` 可快速验证已提交结果，配置本地原始数据后可使用 `python scripts/run_pipeline.py --full` 完整重跑。

`research_record/` 中的内容不由正式管路执行，也不表示论文采用了相应结果。每项研究均保留其当时的样本、设定与局限，并通过状态索引区分已完成检验、负结果、被替代方案、未运行阶段及正式放弃的方向。[`SOURCE_COVERAGE.csv`](research_record/SOURCE_COVERAGE.csv)进一步说明原工作区各分析分支是完整收录、代表性保留还是因重复、许可或临时性质而明确排除；[`docs/workspace_coverage_audit.md`](docs/workspace_coverage_audit.md)记录了本次覆盖审计。
