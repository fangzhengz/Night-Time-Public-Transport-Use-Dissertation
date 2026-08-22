# CASA_FYP 工作区到最终 GitHub 库的覆盖审计与补录报告

审计日期：2026-08-22
来源工作区：`D:\SDS2025_workspace\CASA_FYP`
目标库：`D:\SDS2025_workspace\CASA_FYP_github`
审计性质：只读来源核查；未推送远程仓库

## 1. 审计问题与结论

本次审计回答两个不同的问题：

1. 目标库是否完整保存了论文最终采用的分析、结果和解释链条？
2. 来源工作区中所有具有研究意义的历史分析，是否都以代码、结果或明确索引的形式进入目标库？

结论并不相同。

- **最终论文证据覆盖：通过。** Rail、Bus、LNWC、20项城市背景变量、论文图表、提交论文及完整重跑入口均有明确对应关系，现有验证也能检查冻结样本、聚类数、主要统计量与论文图件。
- **主要研究过程覆盖：通过补录。** 初次审计时目标库索引22项研究记录；补录后共有35项，覆盖重要模型发展、敏感性分析、替代背景分析、放弃的RQ3和Bus–Rail探索。
- **“所有具有研究意义的结果均得到交代”的声明：有边界地通过。** 独立分析分支以完整或经过说明的精选快照保留；重复运行树、大型可再生中间文件和受许可限制数据通过来源清单或provenance明确交代，而不是无说明缺失。
- **逐文件镜像并非目标，也没有必要。** 原始许可数据、大型Parquet、重复备份、临时排版与审阅缓存应继续排除；问题在于若干有独立研究问题和结果报告的分支也被遗漏，而不只是缓存或重复文件。

因此，当前库既可作为论文复现库，也可作为研究决策过程的完整精选档案。这里的“完整”指每个有独立研究意义的方向均有代码、结果或明确覆盖说明，不指逐字节镜像整个工作区。

## 2. 审计范围与方法

### 纳入范围

- `FYP` 下带有 `src`、`outputs`、README或独立分析含义的当前分析目录；
- `FYP\旧分析归档` 下的各个方法实验；
- `FYP\data_processing`、`FYP\outputs` 和 `_backup_pre_bus_refit_2026-08-03` 下的分析性目录；
- `FYP\analysis code` 与工作区根目录 `scripts`，用于判断早期代码或论文审阅工具是否属于研究证据。

### 排除范围

- Git对象、依赖包、`__pycache__`、LibreOffice临时目录；
- Word/PDF审阅缓存、重复渲染图、纯排版中间文件；
- 参考文献全文库和与分析无关的会议材料；
- 因许可不能发布的NUMBAT、BUSTO、OS POI等原始数据。

### 文件级核对

机器审计识别出78个候选来源目录、4,165个具有分析意义的文件，其中4,164个可计算SHA-256；目标库中共索引1,972个可比较文件。32个来源目录至少有一个完全相同文件进入目标库，46个目录没有完全相同文件。

这些数字不能直接作为“覆盖率”：README叙述化改写、路径重构、配置调整和脚本清理都会改变哈希；相反，一个偶然重复的CSV也不能证明整个研究分支已经保存。因此，哈希结果只用于发现候选遗漏，最终判断同时检查目录主题、README、源代码、结果报告和目标库状态索引。

机器可读明细见 `workspace_coverage_file_audit.csv`。

## 3. 已充分覆盖的部分

### 最终主线

- Rail：NUMBAT预处理、物理站点合并、NaPTAN匹配、403站K=5对角GMM、模型选择与不确定性；
- Bus：BUSTO预处理、StopArea到LSOA分配、3,383个LSOA的CLR特征、K=4全协方差GMM及诊断；
- 后聚类行为指标：正式Rail四指标和Bus五指标；
- LNWC：Rail 800m Voronoi截断集水区与Bus LSOA关联；
- 20项城市背景指标：总体检验、cluster-versus-rest检验、效应量、标准化剖面；
- 论文交付层：提交PDF、LaTeX源、与提交论文逐字节一致的图件及单独保存的重算图。

### 明确进入研究记录的较大分支

- Rail all-modes范围、K值和稳定性电池，包括多个纠错前档案；
- Bus day-type normalisation、activity-tiered core、alpha grid、hub-first reclustering、可靠核心阈值、Bus ILR等；
- 1200m到800m的LNWC半径发展；
- LOAC、Spatial Signatures、设施多样性和20变量开发过程；
- 被放弃的RQ3及最终未写入正文的Bus–Rail空间关系分析。

## 4. 初次审计发现并已补录的分支

下列目录不只是重复缓存。它们具有独立问题、固定实验设计、代码和已形成的结果报告。初次审计发现它们未被独立收录；本轮已全部以“历史/未采用/负结果”身份进入 `research_record`。

| 优先级 | 来源目录 | 研究价值 | 当前覆盖判断 |
|---|---|---|---|
| 高 | `旧分析归档/rq1_bus_hellinger_transform` | 对同一Bus样本检验保留零值的Hellinger几何；预设接受门未通过，是重要负敏感性结果 | 已补入 `bus_hellinger_transform` |
| 高 | `旧分析归档/rq1_rail_ilr_sensitivity` | Rail原始份额与ILR几何敏感性；揭示零模式主导问题 | 已补入 `rail_ilr_sensitivity` |
| 高 | `旧分析归档/巴士15分钟&1小时稳定性验证` | 在同一4,100 LSOA样本上公平比较15分钟与1小时分辨率、种子和bootstrap稳定性 | 已补入 `bus_time_resolution_15min_vs_1h` |
| 高 | `rq1_bus_stoparea_only_isolated_test` | 将StopArea-only与parent-hub-first空间单元严格隔离比较 | 已补入 `bus_stoparea_only_isolated_test` |
| 高 | `rq1_rail_weekend_window_sensitivity` | 检验Rail weekend ratio的时间窗和Friday分组；与最终指标解释直接相关 | 已补入 `rail_weekend_metric_window` |
| 高 | `旧分析归档/rq1_bus_hub_zero_audit` | 判断单方向零值是数据结构还是跨LSOA换乘枢纽拆分造成 | 已补入 `bus_hub_zero_audit` |
| 中高 | `旧分析归档/rq1_bus_hub_first_reorganisation` | 完整记录被放弃的hub-first空间重组及其19.4%活动重新分配影响 | 已补入 `bus_hub_first_reorganisation` |
| 中高 | `旧分析归档/rq1_bus_hub_first_reclustering_alpha_sensitivity` | 固定3,593 LSOA样本比较alpha=0和alpha=5 | 已补入 `bus_hub_first_alpha_fixed_sample` |
| 中 | `旧分析归档/cluster_clean_version_grouped` | 早期按weekday/weekend分别聚类的服务制度方案 | 已补入 `grouped_day_regime_clustering` |
| 中 | `旧分析归档/rail_k_selection_validation` | 早期270站Underground-only的K=5/K=6成对bootstrap与种子验证 | 已补入 `historical_rail_k5_k6_validation` |
| 中 | `旧分析归档/new_bus_LNWC_IMD_test` | 3,365 LSOA CLR K=4的早期LNWC/IMD外部检验 | 已补入 `historical_bus_clr_lnwc_imd` |
| 中 | `rq1_context_metrics_analysis` | 早期后聚类连续行为指标层及显著性检验 | 已补入 `historical_context_metrics` |

## 5. 可合并为一个早期历史层的内容

以下内容不适合逐目录原样复制，现已建立叙述性的 `research_record/00_early_pipeline_history/`，保存早期代码，并以 `legacy_output_inventory.csv` 逐项列出27个旧输出目录：

- `FYP\analysis code` 中的早期Notebook与01–20号脚本；
- `FYP\outputs` 下早期KMeans、CLARA、2000阈值、15/30分钟、feature-v2和诊断输出；
- `旧分析归档/cluster_clean_version`、`cluster_clean_version_15min`、`cluster_clean_version_1h`；
- `旧分析归档/巴士聚类错误修改`；
- `此前的尝试分析文件` 中的早期清洗和pilot EDA代码。

这些材料大多不能与最终样本和方法直接比较，但它们解释了研究如何从早期KMeans/CLARA与不同时间聚合，转向最终的模式分离GMM管道。建议保留代表性代码、核心结果表和一份决策叙事，而不是复制全部重复图片和中间表。

## 6. 合理排除且无需补入的内容

- `_backup_pre_bus_refit_2026-08-03`：属于可恢复的重复备份；只需在覆盖表注明由其更新版本取代；
- 原始及许可数据：继续遵守 `docs/data_provenance.md`，只保留来源、下载定义、哈希和本地路径约定；
- 大型Parquet和模型运行缓存：只要可由公开代码和授权原始数据重建，不应为追求“全部”而上传；
- `_docx_review_*`、`qa_*`、`render_*`、`tmp`、`zotero`：属于写作、排版或工具缓存，不是实证分析结果；
- 内容完全相同的重复图表和报告：保留来源—目标映射即可。

## 7. 初次发现并已修复的文档一致性问题

1. `research_record/STATUS.csv` 已由22项扩展到35项。
2. 以下三个原本缺少README的目录均已补入叙述性说明：
   - `formal_sensitivity_checks/rq1_bus_05cutoff_sensitivity`
   - `02_context_alternatives/independent_variable_development`
   - `02_context_alternatives/loac`
3. RQ3说明已统一为“输出作为历史快照保留，但因早于配置修正而不可引用”。
4. 新增 `research_record/SOURCE_COVERAGE.csv`，明确来源、目标、覆盖方式、保留状态及排除理由。

## 8. 已执行的补全顺序

### 第一批：直接影响最终方法解释（已完成）

1. Rail weekend-window sensitivity；
2. Bus 15分钟与1小时公平比较；
3. Bus Hellinger负敏感性；
4. Rail ILR敏感性；
5. StopArea-only、hub-zero与hub-first空间单元审计。

### 第二批：完整呈现模型发展（已完成）

6. 固定样本alpha敏感性；
7. grouped day-regime版本；
8. 270站历史Rail K验证；
9. 早期Bus CLR × LNWC/IMD结果；
10. 早期context-metrics分支。

### 第三批：压缩保存最早期探索（已完成）

已建立 `research_record/00_early_pipeline_history/`，以代表性代码、来源覆盖表和旧输出目录清单涵盖KMeans/CLARA、15/30分钟和feature-v2试验，不复制所有重复运行产物。

## 9. 最终判定

补录后的目标库足以让审阅者理解和验证论文最终结论，也以明确状态保存了所有已识别、具有独立研究意义的分析方向。大型中间数据、重复备份和临时产物仍被有意排除，但其来源和排除理由可由覆盖表追踪。因此可以作出有边界的完整性声明：这是完整、精选且可解释的研究档案，而不是整个工作磁盘的逐字节镜像。
