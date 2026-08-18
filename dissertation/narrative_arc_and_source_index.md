# Claude 讨论笔记:论述弧线共识、修改清单与参考资料索引

版本:2026年8月14日,与 Claude 多轮审查 Main_body_partV6.docx 后整理
用途:记录当前已达成的共识、恢复的论述弧线、待执行的具体修改,**并索引支撑这些结论的本地原始资料**,使得跨对话窗口、或换用其他AI工具时,能够只凭本文件+下列资料路径重新恢复完整的上下文理解,不需要重新翻找或重新论证一遍。
取代:`NARRATIVE_ARC_CONSENSUS_AND_CHECKLIST_2026-08-14.md`(同目录,内容并入本文件并扩充)。

---

## 零、如何使用本文件

1. 第一至六节是**结论层**:核心诊断、恢复的论述弧线、章节修改清单——直接说明"我们现在要做什么、为什么"。
2. 第七节是**证据层**:列出所有支撑上述结论的本地文件,包括原始路径、文件类型、核心内容摘要、以及它在论证链条里扮演的角色。如果需要复核某个结论,或者换一个AI工具/新开一个对话窗口,应该先读这一节,再按需去读具体文件。
3. 多数原始材料是 `.docx` / `.pdf`,不能直接被文本工具读取,需要先转换。本机可用的转换方式记在第七节末尾的"工具备注"里。
4. 所有文件路径均为绝对路径,按 Windows 路径书写。

---

## 一、核心诊断(已达成共识)

1. **失败模式已被导师明确点名**:Esra Suel(2026-08-04会议)——"dissertations usually fail" 的原因通常是缺少贯穿全文的 narrative arc,不是解读错误。当前稿件的问题属于这一类。

2. **反复修改导致内容被稀释的具体机制**:聚类版本、变量集合、K值在过去一个月经历多轮独立调整(rail all-modes K=5、bus StopArea CLR K=4、变量从15到18到20、no_car_household_share 反复增删)。每次调整后为了让数字保持一致,写作习惯性地把上一版较尖锐、较具体的解读句替换成更通用、更不依赖具体数字的表述,长期下来把有解释力的具体论点磨平了。这个机制在 Discussion 和 Results 两章都发生过,但表现形式不同:
   - **Discussion**:具体解读句被替换成通用、安全但空洞的句子。
   - **Results**(4.2.1/4.2.2):写作逻辑滑向"证明这个簇为什么该独立成类"(taxonomy-justification),而不是"这个簇代表了什么现实图景"。这消耗了本该留给 Discussion 做批判性解读的内容空间,是 Discussion 感觉"没东西讲"的直接上游原因。

3. **"太多数字"反馈导致的过度修剪**:早期 `result part draft.docx` 数字密度过高被导师批评,重写后 4.2/4.3 几乎删光了所有统计量,后来的修复尝试又矫枉过正,变成只提最强的3-5个变量、完全不提数字。

---

## 二、20个独立社会经济变量的功能定位(重要修正)

**不恢复 ε² 数值到正文**——现有 Figure 4.8/4.9 效应量图已经足够清晰。

**效应量排序和逐簇画像是两个不同层级,不要混为一谈**:
- **层级A(mode级,效应量排序)**:回答"整体而言,哪些因素最影响这个交通系统的簇间分化",由图表负责。
- **层级B(簇级,变量画像)**:回答"这个具体的簇所在的地区是什么样的",由文字负责,应**灵活调用全部20个变量**,不局限效应量最高的那几个。

选20个独立变量而非LOAC的初衷就是为了更精确地画像,效应量排序只是附带产物。"多数指标接近均值"本身就是有效的画像结论(例如 Rail C4 对应"相对混合的城市功能区"),不需要因为没有突出变量就跳过。

**已确认关闭**:Heathrow/LNWC 独立印证片段,聚类版本调整后已不适用,不再追。

---

## 三、恢复的论述弧线

对应最初 `伦敦夜间交通论文故事与研究设计_讨论稿.docx`(2026-07-27版)第六章大纲,现已用当前官方聚类版本的数据重新验证。

### 弧线第1点:夜间交通不只是中心夜生活现象

- **C3(夜间持续型,n=31,距中心8.4km)= 剥夺主导型**:imd_health z=+0.754(最高)、imd_education z=+0.348(最高)、deprived_1plus_share z=+0.287(最高)、social_rented_share z=+0.736(最高)、unemployed_share z=+0.740(最高)、accom_food_share z=+0.690(最高)。
- **C0(外围到达型,n=89,距中心17.8km)= "经济压力相对较低的家庭化郊区情境"**:no_car_household_share z=−1.11(车辆拥有率最高)、dependent_children_share z=+0.818(最高)、剥夺类指标全部为负或接近全表最低。

### 弧线第2点:Rail 与 Bus 揭示不同的夜间城市组织逻辑

- 已有机制解释(4.2.3/5.2):节点数据保留方向不对称,LSOA聚合抹平方向信号。
- **新发现**:Rail 的社会经济关联分裂成两条独立故事(剥夺型 C3 vs 车辆充足家庭型 C0);Bus 是一条捆绑梯度——Bus C1 在剥夺指标、无车比例、年轻人口比例上**同时**最高,没有分裂成两个独立机制。这是 Rail/Bus 组织逻辑差异在社会经济层面的对称性证据。
- 待恢复:bus-rail 空间共位分析(见第五节)。

### 弧线第3点:夜间交通活动更多与城市功能、家庭背景联系,而非贫困,这与传统交通研究存在差异

- 家庭结构类变量区分度整体强于剥夺类变量,但**车辆拥有率需单独谨慎处理**:no_car_household_share 在 Rail C1(中心区出发型,最高活动)最高(+1.017),不是在剥夺程度最高的 C3(仅+0.525),说明该变量更多追踪城市中心度/建成环境密度,不能直接算作"家庭背景"或"贫困对照"证据,需单独讨论其混淆问题。

### 弧线第4点:潜在交通脆弱性、政策含义与限制

对应现有5.5/5.6,基本不需要大改,只需补一条方法论贡献(见第四节)。

---

## 四、待补充的方法论贡献(纯写作任务)

**"聚类独立识别城市功能,为交通规划提供新方法"**:本研究的聚类完全基于夜间时序数据本身,LNWC、IMD、设施数据是聚类完成后才引入做外部验证,不是聚类输入。补进 Conclusion 的"Methodologically"贡献段落,或5.5开头。

---

## 五、Bus-Rail 空间共位分析:已在当前数据上重新跑通(2026-08-14)

**状态:已完成**,不再是待办项。2026-08-14用当前官方标签(Rail 403站点 all-modes K=5、Bus StopArea CLR K=4,3,383 LSOA)重新跑了 `bus_rail_relation_analysis` 的完整四步流程,脚本自带的一致性检查(站点数/LSOA数核对)全程未报错,确认输入是当前稳定版本。旧记忆记录(2026-07-30版,54.8%/33.8%)已过时并被下方新记忆取代。

**当前结果(供正文/附录引用)**:
- **Test A2(推荐引用的主结果)**:距最近rail站点400m内,54.3%的bus LSOA属于C1(高活动、强夜间持续)簇,为全样本基准33.5%的1.6倍;2km外降至15.4%,不到基准一半。效应在400m处是陡峭台阶,非渐变梯度。控制中心度分层后依然成立(内圈+12.5pp/1.26x、中圈+19.2pp/1.57x、外圈+14.0pp/1.78x),且相对提升幅度在外圈最大——恰是"纯中心度效应"解释最弱的地方。
- **Test B(簇类型共现)**:Cramér's V=0.158(1200m敏感性0.154,稳定),permutation p=0.0001。高活动持续型bus簇(C1)最常与Rail中心换乘型(C2)、内中圈混合型(C4)相邻;低活动/目的地导向型bus簇更多与外围到达型Rail簇相邻。
- **方法论提示(报告已写好,可直接引用)**:Test A的epsilon-squared(0.096)单独看会显得比中心度对照变量(0.118)还弱,容易被误读为纯中心度副产品,但这是统计量问反了方向;应引用Test A2的反向条件概率和分层控制结果作为主证据,而不是Test A的epsilon-squared。

**产出文件**:
- `D:\SDS2025_workspace\CASA_FYP\FYP\bus_rail_relation_analysis\outputs\report\RESULTS.md`(完整报告,可直接摘录进附录)
- `D:\SDS2025_workspace\CASA_FYP\FYP\bus_rail_relation_analysis\outputs\figures\`下三张图(overlay地图、距离分布图、按距离带的簇构成图)

**写入位置(2026-08-15更新,降级为条件项)**:2026-08-15核实 main_body_V7 全文(Ch1-4正文约9,200-10,100词 + Discussion/Conclusion草稿4,122词)合计约13,300-14,200词,已超12,000词上限。用户决定:先完成整体压缩,bus-rail共位分析在5.2的引用句**能加则加,加不进去就不勉强加**,优先级低于5.4的方法论贡献句(见第四节)。完整分析结果仍保留在附录候选材料中(`bus_rail_relation_analysis/outputs/report/RESULTS.md`),即使正文最终没有引用句,附录本身不计入字数,可以保留作为完整存档,不算浪费。

---

## 六、章节级修改清单

### Results(第4章)
- [ ] 4.2.1 / 4.2.2:逐簇描述从"和别的簇有什么不同"换成"代表了什么现实图景",参考 `result part draft.docx` 已有的正确语气(如"These are the places people leave from at night")。
- [ ] 4.2.3:检查是否与 Discussion 5.2 重复,决定精简此处或各有侧重。
- [ ] 4.3.2:按第二节原则重写,灵活调用全部20变量;Rail C4"多数指标接近均值"要明确写出并解释为"相对混合的城市功能区"。
- [ ] 不需要:恢复ε²数值到正文;排序式陈述。

### Discussion(第5章)
- [ ] 5.2:先分别解释Rail/Bus各自机制,让差异作为结论浮现;补入"Rail社会经济关联分裂成两条故事、Bus是单一捆绑梯度"新发现;结尾加一句指向附录的bus-rail共位分析引用句。
- [ ] 5.3:重写为承载弧线第1点,C3/C0对照折叠进论证句,不逐簇罗列。
- [ ] 5.4:重写为承载弧线第3点,car ownership 的中心度混淆问题单独处理。
- [ ] 5.5:补入"聚类独立识别城市功能,为规划提供新方法"。
- [ ] 5.6:基本保留。

### Conclusion(第6章)
- [ ] 已基本重写到位(24114779模板)。补入"独立识别城市功能"这一句,其余等5.x重写完成后同步微调措辞。

### 附录
- [x] bus-rail 空间共位分析已重新跑通(见第五节),数字可用;仍需把 RESULTS.md 的内容整理成附录格式的方法+结果+图表小节,并在5.2末尾加引用句。

---

## 七、参考资料索引(证据层——跨窗口/换AI时的恢复入口)

### 7.1 导师会议记录(原始 .docx,按时间顺序)

| 文件路径 | 日期 | 出席者 | 核心内容 |
|---|---|---|---|
| `D:\SDS2025_workspace\CASA_FYP\FYP\meeting\Fangzheng + Clara Catch Up.docx` | 2026-06-25 | Fangzheng, Clara | 纯方法论讨论(时间粒度、LSOA聚合、是否剔除低流量站点),叙事相关内容很少,只有零星铺垫("building up your story") |
| `D:\SDS2025_workspace\CASA_FYP\FYP\meeting\TfL + CASA - Night Travel Project (4).docx` | 2026-07-17 | Fangzheng, Clara, Howard | **关键决策会议**:Howard首次明确要求"good story to tell";Clara建议聚焦RQ1+RQ2、暂缓OD/RQ3;Howard质疑Rail/Bus为何分开分析、Bus K=3是否可信 |
| `D:\SDS2025_workspace\CASA_FYP\FYP\meeting\TfL Night travel meeting7.29.docx` | 2026-07-28(文件名标注7.29,但转录头显示28 July) | Fangzheng, Clara | 讨论是否保留低流量站点、聚类噪音处理;Clara提出"if you come up with a narrative using the patterns...that will give you a lot to talk about" |
| `D:\SDS2025_workspace\CASA_FYP\FYP\meeting\TfL + CASA - Night Travel Project (5).docx` | 2026-08-04 | Fangzheng, Clara, Howard, Esra | **全篇最关键的会议**:Esra明确点出"叙事弧线缺失是论文失败的通常原因";Fangzheng当面汇报car ownership发现,Howard转给Esra/Clara讨论;Esra提醒无车比例的生态谬误风险(不能从地区特征跳到乘客行为);Howard直接问"Rail和Bus讲不讲同一个故事",Clara回应"两个不同故事也可以,但要relate起来";Howard明确要求收缩范围、不追OD mismatch |

**注意**:这四个文件是原始转录稿,充满口语和停顿词,直接读取效率低。之前用 `pdftotext`/`pandoc` 转换为纯文本后用子代理提取过一次关键内容,提取结果已经整合进本文件第一、三节,不需要重新提取,除非要复核具体逐字原话。

### 7.2 早期思路整理文档(用户本人撰写,Chinese/English混合)

| 文件路径 | 内容与价值 |
|---|---|
| `D:\SDS2025_workspace\CASA_FYP\FYP\伦敦夜间交通论文故事与研究设计_讨论稿.docx`(2026-07-27版) | 完整研究策略文档,**当前恢复的论述弧线的原始出处**(第六章Discussion大纲四条),记录了2026-07-17导师会议后"从供需公平转向模式特异性/社会空间嵌入"这一定位决策的完整推理过程,以及研究问题的正式表述、文献缺口定位、写作措辞边界表(哪些词该用哪些该避免) |
| `C:\Users\fangz\Desktop\Attempt to organise the line of reasoning and the narrative structure.docx` | 早期RQ表述草稿、章节大纲雏形,英文为主 |
| `C:\Users\fangz\Desktop\结果部分整理.docx` | **当前"经济压力相对较低的家庭化郊区情境"这类画像语言的原始出处**,包含具体ε²数值的中文Results草稿,对每个簇有比当前Main_body更具体的社会经济背景描述 |
| `C:\Users\fangz\Desktop\result part draft.docx` | 更早期的英文Results草稿,**叙事语气比当前版本更鲜明**(如"These are the places people leave from at night"),包含17变量完整ε²排序表、Heathrow/LNWC独立印证段落(已确认不再适用)、bus-rail共位分析的旧数字(已确认过时需重跑)。这份文件的具体数字大多已被后续聚类版本更新覆盖,**只应参考其写作语气和论证结构,不应直接引用其数字** |

### 7.3 数据与分析溯源文件(分析代码库,含决策记录)

| 文件路径 | 内容与价值 |
|---|---|
| `D:\SDS2025_workspace\CASA_FYP\FYP\rq2_independent_variables\src\config.py` | **信息密度最高的单个文件**,文件头部注释完整记录了20个独立变量的增删决策历史,包括 no_car_household_share 在2026-08-07被删、2026-08-08因"打断了Discussion论证链条"被加回的完整理由,以及为什么选独立变量而不是LOAC(直接回应BtC论文对"预设复合分类"的方法论批评) |
| `D:\SDS2025_workspace\CASA_FYP\FYP\rq2_independent_variables\outputs\data\rail_cluster_matrix_z.csv` | 当前官方Rail聚类(403站点,K=5)的20变量z-score矩阵,2026-08-12生成,**本文件第三节弧线1/3的数字全部来自这里** |
| `D:\SDS2025_workspace\CASA_FYP\FYP\rq2_independent_variables\outputs\data\bus_cluster_matrix_z.csv` | 同上,Bus版本,**弧线2里"Bus是单一捆绑梯度"的数字来自这里** |
| `D:\SDS2025_workspace\CASA_FYP\FYP\rq2_new_clusters_analysis\README.md` | 记录官方聚类版本的采纳历史(Rail all-modes K=5、Bus StopArea CLR K=4 的采纳时间和理由),用于核对任何一版数字是否为当前官方版本 |
| `D:\SDS2025_workspace\CASA_FYP\FYP\rq2_independent_variables\data\README.md` | 20个变量的数据来源、下载口径、Census/BRES两套就业数据的选择理由 |
| `D:\SDS2025_workspace\CASA_FYP\FYP\bus_rail_relation_analysis\README.md` | Bus-Rail共位分析的方法说明,Clara在2026-07-28会议提出的要求的直接对应产出,**第五节恢复方案的方法依据** |

### 7.4 当前稿件

| 文件路径 | 说明 |
|---|---|
| `D:\SDS2025_workspace\CASA_FYP\FYP\dissertation_working\Main_body_partV6.docx` | 当前正文,本文件所有修改清单都是针对这一版 |
| `D:\SDS2025_workspace\CASA_FYP\FYP\dissertation_working\TRANSFORM_MAP.md`、`VERSION_LOCK_PHASE01.md`、`TM008_*`、`TM009_*` 等同目录文件 | 更早期版本(V4/V5)的修订审计记录,如果需要追溯某处措辞在V4→V6之间是怎么变化的,可以查这些文件,本次讨论未逐一核对 |

### 7.5 对照参考文献(用于结构/文风基准)

| 文件路径 | 用途 |
|---|---|
| `D:\微信储存\xwechat_files\wxid_tb6ol65ajltn22_3ab3\msg\file\2026-08\main.pdf`(Zimo Du, CASA0010) | Discussion/Conclusion结构模板:论证在前、证据折叠、每节显式承接上一节,是本次判定"5.2/5.3/5.4叙事逻辑问题"的主要对照依据 |
| `D:\SDS2025_workspace\CASA_FYP\FYP\往期和参考论文\2021-2022 Sample Dissertation - Chng.pdf` | Discussion按论点组织(非按数据类别平铺)的范例 |
| `D:\SDS2025_workspace\CASA_FYP\FYP\往期和参考论文\24114779_MSc_Dissertation.pdf` | 当前Conclusion重写所依据的具体模板(重述贡献→统一论点段→三类贡献标注→limitations+future work合并) |
| `D:\SDS2025_workspace\CASA_FYP\FYP\参考文献\BtC_paper.pdf` / `BtC_full.txt` | Peiret-García, Kimani & Suel论文,是选用20个独立变量而非LOAC的方法论依据出处,也是Discussion主题式组织(而非按cluster/mode平铺)的范例 |
| `D:\SDS2025_workspace\CASA_FYP\FYP\论文手册与评分标准\CASA Dissertation Handbook 2025-26.pdf`(纯文本版:`D:\SDS2025_workspace\CASA_FYP\_handbook_dump.txt`) | 字数上限(10,000-12,000词,超12,000扣10%)、Discussion/Conclusion的官方评分要求原文出处 |

### 7.6 相关历史记忆记录(Claude本地记忆,纯文本文件,任何工具均可直接读取)

路径前缀:`C:\Users\fangz\.claude\projects\D--SDS2025-workspace-CASA-FYP\memory\`

| 文件名 | 相关性 |
|---|---|
| `project_results_numeric_density_balance_2026-08-12.md` | "太多数字"反馈及修复方案的原始记录,第一节诊断3的出处 |
| `project_rq2_18var_facility_poi_update_2026-08-07.md` | 20变量集合的最近一次版本更新 |
| `project_bus_rail_relation_analysis_2026-07-30.md` | Bus-Rail共位分析的原始(现已过时)结果记录 |
| `project_2026-08-04_supervisor_meeting_outcomes.md` | 8月4日会议结论摘要 |
| `project_research_questions_final_2026-08-05.md` | RQ最终定稿,RQ3/mismatch正式放弃的记录 |
| `project_rail_lnwc_enrichment_staleness_fix_2026-08-07.md` | 提醒:任何rail重新聚类后,rq2_new_clusters_analysis 和 rq2_independent_variables 两条下游管线都要同步核对 |
| `feedback_percluster_contextual_writeup_style_2026-08-07.md` | 逐簇写作风格的既有反馈(高密度z-score+星号,但不用树状图分组) |
| `MEMORY.md` | 索引文件,列出全部记忆条目一行摘要,快速定位相关记忆的入口 |

### 7.7 工具备注(读取这些文件的方法)

- `.docx` → 文本:`pandoc -t markdown 文件.docx -o 输出.md`。本机 pandoc 路径:`C:\Users\fangz\AppData\Local\Programs\Quarto\bin\tools\pandoc.exe`(未加入系统PATH,需写全路径或用 Quarto 自带环境)。
- `.pdf` → 文本:`pdftotext -layout 文件.pdf 输出.txt`(本机已装 poppler,`pdftotext` 在 PATH 里可直接用)。
- 会议记录等大文件转换后建议用关键词搜索定位,不要整篇通读,原始转录稿口语内容占比很高。

---

## 八、明确不做的事(避免重新讨论)

- 不补 LOAC(20个独立变量已承担相似角色)。
- 不追 Heathrow/LNWC 独立印证片段(聚类版本调整后已不适用)。
- 不把 ε² 数值搬回正文(图表已经足够清晰)。
- 不在正文大幅扩写 bus-rail 共位分析(超出字数预算,放附录)。

---

## 九、下一步(已被第十节取代为当前优先级)

第六节的Results/Discussion章节清单和bus-rail共位分析的产出仍然有效,但执行顺序被第十节的TM-016事后诊断取代——语言风格与引用缺失问题必须先于任何进一步的内容微调处理。

---

## 十、TM-016 事后诊断与重构指令(2026-08-14,当前最高优先级)

### 10.1 结论:TM-016 架构对、散文错,重构应保留架构、丢弃散文

TM-016(Codex执行,2026-08-14 04:08版本)正确解决了此前诊断的结构性问题:Results 4.2.1/4.2.2 的taxonomy-justification语言被修掉、5.2改为按节奏主题(方向/持续性/空间)组织而非按mode平铺、Results/Discussion的分工(现实图景在前、比较降级为支撑证据)被显式执行、正文字数从约11,500词压缩到约10,855词。**这部分架构决定是对的,重构时应该保留,不应该推翻。**

但这一批在**句子层面**引入了两个新问题,而且是严重问题:

1. **全文献引用被清空**:Chapter 5 Discussion(5.1-5.6,约1,298词)**引用文献数量为零**,对比TM-016之前的版本有十几处引用(Schwanen et al. 2012、Gan et al. 2020、Mavrogeni et al. 2025等)。这直接对应 `Markscheme2022.pdf` 的"Analysis and critical reflection of findings"评分项(占Smart Cities/Urban Analytics方向30%、Spatial Data Science方向25%总分),该项D档(40-49%)的描述原文是"no or scant reference to academic or policy debates"——零引用精确匹配这个描述,不管内部逻辑多顺,这一项会被摁在这个分数段。
2. **AI化的自指元评论句式**:例如"the contrast with balanced interchange and later-persistent stations **is supporting evidence rather than the purpose of the classification**"——这类句子不描述现实世界,而是向读者解释"这句话在论证结构里的地位是什么"。这是把内部写作规则暴露进正文,不是自然的学术散文写法。同时统计出1,298词的Discussion里出现了15次"rather than/not a/does not/without"这类自我否定式防御句,平均每87词一次。

**这两个问题是同一个根源**:一旦引用被拿掉,自我否定句就成了唯一还能用来托住论证分量的手段,导致读起来又压缩又充满防御性。

### 10.2 重构指令

**保留(不要重新设计)**:
- 六节Discussion架构(5.1主答案→5.2节奏→5.3背景对应→5.4候选功能→5.5规划启示→5.6限制)。
- Results 4.2.1/4.2.2/4.3.2 的"现实图景优先、比较降级为支撑证据"这个原则本身,以及4.3.2"效应量排序(图表)+ 灵活簇级画像(正文)"两层分工。
- 5.2按节奏主题(而非按mode)组织的段落安排。
- 字数纪律(正文应控制在10,000-12,000词区间)。

**丢弃(不要在现有句子上打补丁,直接从底层证据重写)**:
- 当前 Chapter 4.2/4.3/Chapter 5 的具体句子。不要编辑现有措辞,以免AI化的语言基因通过增量修改残留下来。每一段应该直接从对应的证据来源(见第七节参考资料索引:z-score矩阵、LNWC enrichment表、聚类descriptor CSV)和本文件第三节的论述弧线重新写,不参照TM-016现有文本的句子结构。

**写作时必须遵守的规则**(已同步写入 `feedback_discussion_prose_register_and_citation_anchoring.md` 项目记忆):
1. **句子主语是现实世界的现象或地名,不是簇/模型/分类本身**。避免"C1 captures..."、"The profile shows..."这类以分析对象作主语的句式。
2. **每一个超出裸观察的解读性判断,都必须配一篇参考文献列表里已有的具体引用**,格式参照 `BtC_paper.pdf` §5.3 的写法:具体数字 → 现实世界解读 → 引用锚定的谨慎表述,写在同一句话里,不要拆成"观察句+单独的免责声明句"。
3. **认识论上的谨慎(比如"这是地区特征不是乘客行为")要靠引用锚定的措辞实现**("consistent with accounts of X (Author, Year), expressed here as Y rather than Z"),不要用单独一整个分句去做自我旁白式的元评论。
4. **不设引用密度的数字指标**(2026-08-15修正:此前建议过"每60-70词一处""不低于15处"这类配额,是错的——引用该出现在哪里由论证本身决定,不是由词数触发,把它变成配额会诱导为凑数而堆砌装饰性引用,恰好违背评分标准要的是"批判性反思与学术讨论的实质连接",不是引用出现频率)。唯一的硬性判断是:**当前"整章零引用"这个极端情况必须改变**——不是因为词数不够,是因为这意味着5.2-5.5里每一个解读性论点都没有和任何文献发生实质对话。检查方式改为逐条判断:5.2-5.5里的每一个主要解读性论点,是否配了一篇能起到支撑/限定/延伸/对照作用的具体文献,而不是数一数全章出现了几次"(Author, Year)"。
5. 补上之前核实过还缺的具体内容:Rail C1 的"年轻"(age_20_34_share)维度、Rail社会经济关联分裂成两条独立故事(C3剥夺型 vs C0家庭型)而Bus是单一捆绑梯度这条本轮新发现、bus-rail共位分析(见第五节,已就绪待写入5.4+附录)。

### 10.3 校准示例(可直接作为目标写法参考,但引用需逐段核实,不要照搬示例里的具体文献)

> C1 comprises 26 central-London stations concentrated around the West End, including Oxford Circus, Piccadilly Circus and Charing Cross. Activity is concentrated earlier in the evening and strongly departure-oriented (directional balance +0.32), with the highest average activity of any Rail cluster and the strongest enrichment for LNWC 1, "Thriving night-worker central hubs" (ER=3.98). The catchment context is amenity-rich, younger, private-rented and markedly low-car. This pattern is consistent with accounts of the urban night as a period of concentrated evening and entertainment activity radiating outward from central business and leisure districts (Schwanen et al., 2012; Shaw, 2022), here expressed as a departure signature rather than a claim about individual visitors' purposes.

对比原句(TM-016版本):"C1 captures central evening departure-oriented station activity around the West End...the contrast with balanced interchange and later-persistent stations is supporting evidence rather than the purpose of the classification."——新版本信息量更高(补了年龄和LNWC数字)、有引用锚定、没有自指元评论,且篇幅相近,不是靠堆字数解决问题。

### 10.4 执行顺序(取代第九节)

1. 把这份重构指令(10.1-10.3)转给Codex,明确"重写不是编辑"这个前提。
2. Codex逐段重写 4.2.1/4.2.2/4.3.2/5.1-5.6,每段配引用,禁止自指元评论句式。
3. 重写完成后做一次引用回归检查:确认不是整章又变回零引用(防止被静默清空),并逐条核对5.2-5.5的主要论点是否各自配了起实质论证作用的文献,不是数引用总数对比某个基准数字。
4. 整合 bus-rail 共位分析(第五节)进5.4+附录。
5. 微调 Conclusion 保持措辞一致,同样按"零引用"这个极端情况检查,不设数字目标。

---

## 十一、Results / Discussion 分工判断标准(2026-08-15定案,不再重新讨论)

这条规则由 main_body_V7_backup 的一次具体争议(Results 4.2.1里新增了"we believe city residents go to these areas for nighttime leisure and entertainment"这类段落)倒逼厘清,以下判断标准是最终版本,后续任何一版如果再出现类似争议,直接引用本节,不需要重新论证。

### 11.1 Results 可以讲、应该讲的内容

- **具体地点+具体数字组成的画像**:地名、z-score、enrichment ratio等观测事实自然组织成的描述性叙事,这类"叙事"是被鼓励的,不是要避免的东西。
- **分析单位本身的构造性质/方法论事实**:例如"节点数据保留entry/exit方向对比,LSOA聚合抹平方向信号"——这类内容回答的是"这套方法能测到什么、为什么",是方法论事实,不是对现实世界的社会学解读,可以在Results直接陈述,**不需要留到Discussion**(2026-08-15修正了此前过严的判断:此前曾建议这类机制解释整体留给5.4,这是错的,只有"这对理解城市意味着什么"这一层才需要留给5.4,机制事实本身不需要)。
- **外部情境关联的事实陈述**:LNWC富集比、20变量z-score及其组合画像。

### 11.2 Results 不能讲的内容

- **断言乘客/居民具体的行为动机、目的或身份**(例如"residents go to...for leisure""workers who...")。这条边界来自Esra在2026-08-04会议上的当面提醒(生态谬误)和方法论边界章节(3.8)已经写明的限制:smart-card数据不能证实个体动机。**弱化词("we believe"/"can suggest"/"to some extent")不能让越界变得可以接受,只是让越界不那么显眼**,判断标准是断言的对象是不是"人的动机/身份",不是用词强弱。

### 11.3 Discussion(5.4)能讲、且正是其存在意义的内容

- **假设性的行为解读**,但必须**引用锚定**,格式参照BtC论文§5.3(具体数字→现实解读→引用锚定的谨慎表述,一句话完成)。例如:"Rail C1's evening exit-dominant profile...is consistent with accounts of the urban night as a period of concentrated leisure and consumption activity radiating from central districts (Schwanen et al., 2012; Shaw, 2014)...though the smart-card data cannot confirm individual passengers' purposes or destinations." ——这才是"乘客可能在做什么"这类叙事该落地的地方,不是不讲,是换成能站得住的讲法。
- **跨簇、跨模式的综合判断**(候选城市夜间功能),这是需要综合时序+背景+空间多条证据线才能做的工作,提前在Results做等于替5.4把活干完了,5.4就没有新内容可增补。

### 11.4 处理方式:内容"搬家",不是"删除"

如果Results里已经写了越界的乘客行为推断,不要直接删掉损失掉这个解读方向的价值——把它移到5.4,补上引用锚定和"数据不能证实具体乘客"的限定语,原Results段落只保留到事实层面为止。
