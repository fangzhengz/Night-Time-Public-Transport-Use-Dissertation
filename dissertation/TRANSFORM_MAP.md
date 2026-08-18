# Dissertation transform map

This is the change ledger for the locked dissertation working version. Each
batch records the source state, transformation, evidence, downstream scope,
and verification result. A batch is not marked complete until its outputs have
been rerun and checked.

All dissertation transformation batches are recorded in this single document.
No separate per-batch Transform Map is maintained; supporting JSON files are
machine-readable audit evidence only.

## Current revision control dashboard

Updated: 2026-08-13

This section is the single review-facing overview of the revision programme. The
detailed evidence for completed work remains in the individual TM entries below.

### 1. Current revision objectives

| Objective | Current interpretation | Completion criterion |
|---|---|---|
| Preserve the adopted research route | Retain the approved Main RQ, RQ1, RQ2 and Objectives 1–3 verbatim; analyse Rail and Bus separately and synthesise them descriptively | No unapproved RQ, objective, model or analytical branch is introduced |
| Make the dissertation argument-led | Maintain a visible chain from research gap to RQs/objectives, Methods promises, Results delivery, Discussion and Conclusion | Each RQ and objective has an identifiable method, result and concluding answer |
| Lock the empirical evidence base | Use the current Rail 403-station K=5 and Bus 3,383-LSOA K=4 labels, the common 18:00–05:00 window, and the verified contextual samples | No superseded sample, label, time window, cluster name or contextual result remains in the main narrative |
| Preserve the inference boundary | Describe observed public-transport use and external area context; do not infer passenger identity, causality, unmet demand or service deficiency | Claims use mode-specific, area-level and associational language throughout |
| Improve reproducibility and traceability | Name source datasets, versions, units, transformations, samples, thresholds and spatial-linkage rules; record every revision batch here | A reader can identify the source, transformation, analytical unit and sample behind every principal method/result |
| Produce one reviewable working document | Continue editing `Main_body_partV5_evidence_aligned.docx`; retain existing red text and mark every new textual modification red | No unnecessary dissertation versions; each change batch has a Transform Map entry and passes structural/visual QA |

### 2. Remaining revision sequence

The order below adapts the reviewer’s proposed sequence to the verified current
state. Completed items are not rerun merely to reproduce an arbitrary checklist.

| Order | Planned batch or gate | Required work | Decision/exit condition | Status |
|---:|---|---|---|---|
| 1 | TM-005 — remaining front-half Methods alignment | Audit the unrevised Methods prose for grammar, terminology, internal consistency, formula/variable definitions, table references and transitions. Repair the existing page-25 GMM wrapping defect. Keep results and analytical outputs fixed. | No broken sentences, undefined principal terms, contradictory counts/windows or unresolved structural placeholders; visual QA passes | Complete |
| 2 | Sensitivity evidence consolidation | Bring the already completed Bus window/threshold evidence and Rail catchment evidence into a concise Methods/appendix account. Do not mechanically rerun 20/33/50 thresholds. Keep 18:00–05:00 and threshold 33 as the main Bus specification unless the existing evidence fails its stated justification. | Main specification, comparator, affected sample and observed stability/change are stated; no unsupported robustness claim | Deferred by current scope decision |
| 3 | Rail catchment sensitivity gate | Verify whether the existing alternative-radius outputs are current-label, same-metric and directly comparable with the 800 m main specification. If they are not comparable, record the limitation instead of blending old and current results. | Either one controlled current-label sensitivity is reportable, or a documented reason is given for not using it | Deferred with sensitivity work |
| 4 | Posterior uncertainty gate | Optional only. Run/report it only if a pre-declared acceptance question would materially change cluster interpretation. | Explicit value added beyond the existing BIC/seed/bootstrap evidence; otherwise skipped | Skipped by current scope decision |
| 5 | Discussion | Interpret the verified Rail and Bus organising dimensions, LNWC/context associations, limitations and contribution. Mechanisms remain interpretations rather than findings. | Every major claim traces to a Results subsection; no new empirical result or causal/service-gap claim appears | Next |
| 6 | Conclusion | Answer the Main RQ, RQ1, RQ2 and Objectives 1–3 directly; state contribution, limits and implications at the supported level | Concise one-to-one RQ/objective closure with no new evidence | Pending |
| 7 | Literature Review criticality pass | Strengthen synthesis, disagreement, method limitations and the explicit bridge from literature gap to this study | Paragraphs compare evidence rather than list studies; cited gap matches the actual contribution | Pending |
| 8 | Figures and tables | Audit numbering, in-text call-outs, captions, legends, units, samples, colour readability and standalone interpretation | Every figure/table is cited, self-explanatory and consistent with the current outputs | Pending |
| 9 | Language and terminology | Standardise Rail/Bus capitalisation, observed-use terminology, area-context wording, tense and statistical notation | Terminology scan passes; no passenger-level, causal or direct cross-mode equivalence slippage | Pending |
| 10 | Word count and balance | Measure chapter-level and total word count against the handbook limit; rebalance repetition before final polishing | Total is within the permitted limit and chapter allocation supports the argument | Pending |
| 11 | Final rubric and reference audit | Map the completed dissertation to the marking criteria; audit in-text/reference-list correspondence, dataset citations, appendix/research log, ethics and abstract | No material rubric item, unmatched citation, unresolved placeholder or required component remains | Final gate |

### 3. Revision acceptance and evaluation indicators

| Evaluation area | Indicator | Pass rule |
|---|---|---|
| Scope control | Adopted Main RQ/RQ1/RQ2/O1–O3; Rail/Bus separation; no unapproved analysis | Exact questions/objectives retained and every added analysis has a stated acceptance purpose |
| Data consistency | Rail 403; Bus 3,383; LNWC Rail 387/Bus 3,383; continuous context Rail 389/Bus 3,383; 18:00–05:00 | No competing current counts or main-window definitions in prose, tables, captions or references to outputs |
| Method–Results closure | Method promise versus delivered result | Every formal Method promise is delivered, explicitly scoped out or labelled optional; no result appears without a described method |
| Reproducibility | Dataset/version, analytical unit, transformation, threshold, feature definition, spatial linkage and sample | Each principal output has a traceable source-to-result chain and exact current input/output location where applicable |
| Statistical reporting | Test, sample size, effect size/direction, correction family and limitation | Reported statistics use the correct mode/sample and are not interpreted as causal, unique variance or directly comparable across modes when they are not |
| Sensitivity reporting | Fixed elements, changed element, comparator and acceptance interpretation | Sensitivity changes one relevant assumption at a time and reports both stability and meaningful differences; archived incompatible outputs are not merged |
| Narrative quality | Gap→RQ/objective→method→result→discussion→conclusion chain | Each link can be located and the conclusion answers only what the verified evidence supports |
| Citation integrity | In-text/reference correspondence and primary-source metadata | No guessed metadata; every in-text citation has a reference and every retained reference is used; uncertain non-essential items may remain explicitly marked for user completion |
| Change traceability | Red formatting plus Transform Map entry | Existing red formatting is retained; all new/replaced text is red; deletions and affected scope are recorded in the relevant TM entry |
| Document integrity | Paragraph/table/figure preservation, OOXML validity and visual rendering | DOCX opens and parses; expected media remain; LibreOffice page review shows no change-induced clipping, overlap, missing glyphs or broken pagination |
| Final assessment | Handbook/rubric coverage, required components and word count | All mandatory components are present and the final rubric checklist contains no material open item |

### 4. Completed revision summary

| Batch | Completed outcome | Key verification |
|---|---|---|
| TM-001 | Locked the working version and closed the Gap–RQ–O1/O2/O3 framing without rewriting the adopted questions/objectives | Text and structure checks passed |
| TM-002 | Re-aligned current Rail/Bus labels, the Bus 18:00–05:00 input, `post_2300_share`, contextual samples and the 20-variable Rail input; rebuilt affected analytical outputs | Two full reruns; 139 checked outputs with only four generated-date-line differences and no scientific differences |
| TM-003 | Aligned front-half Methods and Results to the current samples, models, thresholds, behavioural descriptors, association tests, effect sizes and inference boundaries | 35 paragraph replacements; Method–Results Promise Audit closed all required promises |
| TM-003A | Reorganised the Results narrative around Rail and Bus organising dimensions, added the Methods bridge and explicit two-stage RQ closure | 11 changed red paragraphs; 60-page LibreOffice visual QA passed |
| TM-004 | Closed verified NUMBAT, BUSTO, BUSTO-guidance, LNWC and POI provenance; clarified the 18+2 contextual-variable structure and made the Rail catchment method self-contained | 8 paragraph replacements, 4 new references, 23 red paragraphs total; 60-page visual QA passed; one optional supporting citation remains explicitly marked |
| TM-005 | Completed the remaining Chapter 3 readability and terminology pass, clarified the area-context role and descriptor inventory, and repaired the GMM rationale wrapping issue | 9 red paragraph replacements; 336 paragraphs, 53 native-equation nodes and 14 inline shapes preserved; 60-page PDF render with page-25–27 inspection passed |
| TM-006 | Integrated the user-added Rail/Bus model-specification table into Chapter 4 and removed repeated prose | 3 red paragraph replacements; user table preserved unchanged; 60-page PDF render with table-page inspection passed |

Current principal document: `Main_body_partV6.docx`  
Frozen pre-V6 archive: `Main_body_partV5_evidence_aligned_work.docx` (retained under its existing filename; do not edit)  
Unified change ledger and revision dashboard: `TRANSFORM_MAP.md`  
Version/scope lock: `VERSION_LOCK_PHASE01.md`

## Figure and table decision register — 2026-08-13

This register records design decisions only. No figure, table or dissertation
prose was changed in this review round. Exact layouts remain subject to a
source-data and rendered-size check before implementation.

| Item | Decision | Priority | Implementation condition |
|---|---|---:|---|
| Table 4.1 — final cluster solution summary | Adopt | High | Extend the existing model-specification table rather than create a competing summary. Report mode, current sample, K/covariance, cluster n/share and a short evidence-bounded descriptor. |
| Table 4.2 — behavioural descriptor test summary | Adopt | High | Use mode-specific rows with n, Kruskal–Wallis H, BH-adjusted p and epsilon-squared. Do not force non-equivalent Rail and Bus descriptors into a false one-to-one comparison. |
| Table 4.3 — LNWC association summary | Adopt | High | Report the current mode-specific eligible samples, chi-squared, Cramer's V and permutation/adjusted significance as applicable. Keep enrichment detail in the heatmaps unless a table is needed for accessibility. |
| Table 4.4 — full contextual effect-size results | Appendix candidate | Low | Mark for the appendix, preferably in separate Rail and Bus blocks with n, H, BH-adjusted p, epsilon-squared and rank. Not part of the immediate editing batch. |
| Rail and Bus temporal profile figures | Adopt with modification | High | Retain cluster/day-type small multiples. Do not overlay all clusters merely to imitate a reference design: current between-cluster differences are often modest and would be obscured. Add only one or two evidence-backed callouts per cluster or a short row-level annotation strip, using the plots to locate the feature and the Results prose to interpret it. Preserve common scales where comparison is intended. |
| Annotation style from reference figures | Adopt selectively | High | Reuse concise labels for timing, direction balance and late-night persistence, but avoid annotating every local peak. Every annotation must trace to a plotted pattern or reported descriptor and must not imply statistical significance by itself. |
| Cross-document colour correspondence | Adopt | High | Create one mode-specific cluster colour registry and use it consistently in maps, table swatches, panel headings and cluster-profile displays. Keep movement/direction colours as a separate semantic channel in temporal plots; do not ask one colour to encode both cluster identity and entry/exit or boarding/alighting. Reinforce colour with labels, panel position or line style. |
| Contextual effect-size and cluster-profile display | Adopt as a design candidate | Medium | Preferred design is one separate composite per mode: a narrow epsilon-squared ranking panel beside a z-score cluster-profile heatmap. Select main-text variables by a declared rule such as the top eight within each mode; retain the full results in the appendix table. Use BH significance markers only for the matching inferential comparison, and explain that z-scores show profile direction rather than effect size. |
| Stability/ARI plus GMM K-selection | Adopt with modification | Medium–High | Integrate fit and stability as aligned panels with separate y-scales: BIC above, bootstrap ARI and weakest-cluster matched Jaccard below, with the selected K highlighted. Use only genuinely comparable metrics and candidate ranges across modes. Do not use a dual axis. Move seed-level and full diagnostic distributions to the appendix. |
| Rail–Bus synthesis figure | Pending | Not priority | Reconsider only after the Discussion structure is fixed and only if the graphic adds a defensible synthesis without implying formal cross-mode equivalence. |
| Full diagnostic/robustness figure set | Pending for appendix | Not priority | The principle of appendix placement is accepted; the exact retained panels will be decided during the final figure/appendix audit to avoid redundant diagnostics. |

### Acceptance checks for the future figure batch

- Temporal distinctions remain visible at final dissertation width without
  relying on colour alone.
- Cluster identifiers, descriptors and colours agree across prose, tables,
  profiles, maps and heatmaps within each mode.
- Rail and Bus retain their native analytical units and are not presented as
  directly comparable tests when definitions differ.
- All rankings, top-variable selections and annotations follow a declared rule
  and remain reproducible from the current outputs.
- Main-text figures convey the decision-relevant pattern; exact statistics and
  full diagnostics are available in tables or the appendix.

## Checklist reconciliation against the current working draft — 2026-08-13

This reconciliation supersedes any checklist status inferred from earlier
versions. It was checked directly against the current
`Main_body_partV5_evidence_aligned.docx`, which presently contains 337
paragraphs, one native Word table and 14 inline shapes.

Status key: `[x]` complete in the current draft; `[~]` partly complete;
`[ ]` not complete; `[—]` superseded or deliberately excluded by an adopted
scope decision. A conditional item is marked complete only when the decision
not to add the analysis is explicit and the Method does not promise it.

### P0 —正文与正式分析版本

- [x] Current principal samples and models are stated as Rail 403/K=5 and Bus
  18:00–05:00, 11 hours × 3 day types × 2 directions, 3,383 LSOAs/K=4.
- [~] The main prose contains no current 3,372 or 36-bin statement. One
  18:00–06:00/minimum-36 occurrence is intentionally retained as a historical
  sensitivity comparator. Appendices and every figure legend have not yet had
  a final publication audit.
- [~] `Figure 4.X/4.Y`, `[insert ...]` and `[verified citation]` are absent.
  One explicit `[Supporting citation to be confirmed.]` remains at the 800 m
  radius statement by user-approved choice.
- [x] Rail LNWC is consistently stated as 387 eligible stations within the
  403-station clustering population; continuous context is separately stated
  as 389/403.
- [x] A native five-column internal version table now records mode, analytical
  unit, sample size, final K and covariance structure.

P0 verdict: the main analytical version is aligned; final appendix/figure-
legend auditing and the one optional citation remain open.

### P1 — Research gap, RQs and objectives

- [x] The adopted Main RQ and Objectives 1–3 remain unchanged.
- [x] Section 2.4 states the three substantive gaps: dedicated night-use
  typologies; limited descriptive Rail–Bus comparison; and limited linkage to
  independent night-work geography and wider socio-spatial context.
- [~] The gaps are said to be addressed “in sequence” and the contribution
  paragraph maps the three objectives, but the document does not yet provide a
  fully explicit G1/G2/G3 → Objective → Method → Results 4.1–4.3 matrix.
- [x] Rail–Bus comparison is assigned to Objective 2 and described as a
  cautious descriptive synthesis rather than a statistically equivalent pooled
  sample.
- [x] The observed-use → external area-context boundary is explicit; passenger
  identity, travel purpose, unmet demand and service deficiency are excluded.

### P1 — Literature Review responsibilities

- [x] Section 2.1 primarily establishes the urban night as a distinct
  time–space system.
- [~] Section 2.2 primarily addresses night-time mobility and transport
  conditions, but overlaps with Section 2.1 in its night-versus-day framing.
- [ ] Repetitive night-versus-day summary material has not yet been fully
  deleted or merged; paragraph 35 remains redundant and weakly phrased.
- [ ] Safety, accessibility and equity material has not yet received the planned
  critical compression/background-only clarification.
- [x] Section 2.3 concentrates on smart-card temporal profiling, clustering and
  area contextualisation.
- [x] Section 2.4 synthesises the literature into three gaps rather than
  repeating a paper-by-paper review.
- [ ] The heading typo `Night-time transpportation and mobility` and several
  grammar problems remain (for example, “Therefore ... therefore” and “This
  complexity also compounded”).

### P1 — Methodology

- [~] The K-selection account identifies BIC as primary and ARI/random-seed and
  bootstrap stability as qualifiers, with separation diagnostics retained as
  supporting evidence. It does not yet state the complete ordered protocol in
  the checklist or the final parsimony/substantive-distinctiveness gate.
- [ ] Section 4.1 reports the selected Rail K=5 and Bus K=4 and their stability
  limits, but does not specifically explain why Rail K=4/6 and Bus K=3/5 were
  rejected.
- [ ] Section 3.5.2 still states the final Rail diagonal and Bus full choices;
  these have not yet been confined to Results 4.1.
- [ ] The assertion that compositional constraint is less consequential for
  Rail because its 220 intervals distribute the constraint more thinly remains
  in paragraph 109.
- [ ] Rail raw-share modelling has not yet been reframed explicitly as a
  practical choice subject to the same compositional limitation.
- [—] No current 403-station Rail CLR/ILR model is promised. Under the adopted
  decision, it will not be added without a predeclared acceptance criterion.
- [x] The Bus threshold is justified as 11 hourly intervals × 3 day types and
  at least one estimated activity per hourly cell in each direction; the TfL
  hourly-aggregation guidance and retained 3,383/3,797 scope are stated.
- [x] The existing 18:00–06:00/minimum-36 versus 18:00–05:00/minimum-33
  comparison is summarised, including the stable K=4 and the redrawn smaller-
  cluster boundary.
- [x] Rail continuous context uses the equal-weight arithmetic mean across
  distinct intersecting LSOAs.
- [~] The text defines the aggregation, but does not yet say plainly enough
  that it is an average of intersecting-area context rather than catchment
  population composition.
- [~] The two exceptional `n_intersecting_lsoa` values (five and seven) and the
  389/403 completeness rule are reported. A general distribution/reporting of
  `n_intersecting_lsoa` and a full MAUP/boundary limitation remain absent.
- [—] Area weighting has not replaced the formal definition. Any additional
  area-weighted sensitivity remains conditional on an explicit criterion.
- [x] Formal LNWC and continuous-variable sections use correspondence,
  contextual association and external contextualisation rather than treating
  them as equivalent-data validation. A generic “analysis and validation” phrase
  remains in the Introduction but is not the formal method label.
- [x] Epsilon-squared is defined as the magnitude of distributional
  differentiation and explicitly not as causal contribution or explained
  cluster formation.
- [x] Mann–Whitney U comparisons are explicitly cluster versus all units outside
  that cluster.
- [x] BH families are stated as 20 omnibus tests per mode, 80 Bus cells and 100
  Rail cells.
- [x] The first BUSTO description distinguishes ticketing-derived/scaled
  boardings from TfL-inferred alightings.
- [x] Rail can separate Friday, Bus Weekday cannot; Friday-night Bus activity
  and direct day-type equivalence are expressly limited.

### P1 — Method-to-Results delivery

- [~] Results contains a one-sentence covariance selection statement, but the
  complete covariance × K grid is not yet assembled into the dissertation
  appendix.
- [ ] No native behavioural-descriptor results table containing mode,
  descriptor, n, H, p/BH-adjusted p and epsilon-squared is present in the DOCX.
- [x] Main Results summarises the descriptors that most strongly organise each
  mode.
- [—] The checklist request to report Rail full-composition permutation
  R-squared=0.261 is superseded by the adopted scope decision. The current
  Method explicitly states that no separate multivariate composition test is a
  formal dissertation result; the audit result remains outside the thesis.
- [x] Bus LNWC and dominant-Rail-LNWC Cramér’s V values are retained and not
  treated as a formal cross-mode test.
- [ ] The cluster–context appendix table with mode, cluster, variable, U,
  BH-adjusted p and direction has not yet been inserted into the dissertation.
- [—] No Bus raw-share comparator is promised in the formal Method; therefore
  no comparator result is required unless that promise is later added.
- [x] The unsupported night-versus-day Results claim has been removed.
- [x] The replacement Results framing states that the structures concern
  night-time station/area use and are not a direct night-versus-day comparison.
- [~] Rail Friday/weekend structure and the Bus Friday limitation are described,
  but Objective 2 still lacks one concise, explicit cross-mode day-type
  synthesis sentence.

### P1 — Tables and variable definitions

- [ ] The socio-economic variable image is still captioned `Table 1`, not
  `Table 3.1`.
- [ ] The socio-economic variable table remains an embedded image rather than a
  native Word table.
- [ ] The behavioural-descriptor image has not been rebuilt as a native Word
  table.
- [ ] The current variable material does not yet provide, for every contextual
  variable, source/year, numerator, denominator, spatial unit, transformation
  and higher-value interpretation.
- [~] POI count/facility intensity and Shannon functional diversity are
  distinguished, and Shannon is not called density; the exact preferred labels
  are not yet standardised everywhere.
- [~] Directional balance is used and exemplified, but its formula, range and
  sign interpretation are not yet fully stated in prose/table form.
- [ ] Only `post_2300_share` has a complete common-window definition. Deep-night
  share, post-midnight persistence and weekend ratio still lack complete
  mode-specific numerator/denominator/window/range definitions.
- [x] Census industry measures are described as residence-based employed-
  resident shares rather than workplace distributions.
- [x] The current text consistently defines 18 Census/deprivation indicators
  plus two POI indicators, producing 20 formal continuous variables.

### P1 — Figures

- [ ] The large Rail/Bus composite figures have not yet been fully separated
  into main-text temporal profiles, maps and appendix-level detailed panels.
- [ ] Full K diagnostics and covariance grids have not yet been moved into a
  completed appendix structure.
- [ ] A simplified two-panel cluster-selection figure marking Rail K=5 and Bus
  K=4 with adjacent-K reasoning is not present.
- [~] Main text contains Rail and Bus temporal/spatial figures, LNWC figures and
  contextual figures, but their role and placement have not undergone the final
  7–9-core-figure triage.
- [ ] Repeated cluster-map/LNWC-reference combinations have not yet been
  rationalised through appendix cross-references.
- [ ] Fixed mode-specific palettes, consistent `Rail C#`/`Bus C#` legends,
  Greater London/Thames/exclusion categories and 100%-scale legibility have not
  yet passed a dedicated final audit.
- [ ] Captions remain incomplete: the document still contains standalone
  `Figures 4.1` and `Figures 4.2`, and full data/window/sample/unit/version/
  limitation captions are absent.
- [ ] Context heatmap captions do not yet document cell values, star thresholds,
  cluster-vs-rest MWU, BH-adjusted p and correction families.
- [ ] LNWC enrichment captions do not yet fully state ER=1, the mode-specific
  eligible benchmark, different Rail/Bus denominators and the prohibition on
  comparing absolute Rail/Bus ER magnitudes.

### P2 — Results and Discussion evidence boundary

- [x] Rail is framed through observed station entries/exits and Bus through
  representative estimated passenger activity rather than exact journeys or
  passenger demand.
- [ ] Bus C3 still uses `destination characteristics`; this must be changed to
  wording such as `alighting-oriented estimated activity` without inferred
  destination or travel purpose.
- [x] LNWC and socio-economic results are explicitly area context.
- [x] Cluster–context associations are not used to infer passenger identity.
- [x] Low activity is not used to claim unmet demand or service deficiency.
- [ ] Candidate night-worker, resident and land-use mechanisms await the
  Discussion and have not yet been written with interpretation labels.
- [~] Cross-mode differences are limited by spatial unit, feature construction,
  sample and stability; temporal resolution, service window and measurement
  certainty still need to be added explicitly.
- [x] `Rail more structured / Bus more continuous` is presented as descriptive
  synthesis, not a formal cross-mode statistical conclusion.

### Final consistency checks

- [~] A Method–Results Promise Audit exists in this Transform Map, but the full
  Gap → RQ/Objective → Method → Result → Figure/Table → Conclusion matrix is not
  yet complete because Discussion and Conclusion are unwritten.
- [x] Current formal Method promises have been checked against current Results;
  known appendix deliveries remain listed as open rather than falsely closed.
- [~] Principal Results claims are associated with figures or reported values,
  but a complete claim-by-claim source table has not yet been produced.
- [~] Current main figures broadly support the core claims, but incomplete
  captions and composite density prevent this item from passing.
- [x] Current main-text samples, K values, time window and 18+2 variable count
  are internally aligned; the historical sensitivity mention is clearly
  identified as such.
- [ ] Cross-references, figure/table numbering and the table of contents have not
  received the final update.
- [ ] The prior 60-page QA predates the current 337-paragraph/one-table state.
  A new final Word/PDF page-by-page QA is therefore required after the current
  edits and figure/table work are complete.

### Corrected immediate priorities from this audit

1. Remove the Rail “220 intervals makes composition less consequential” claim
   and replace it with an explicit raw-share modelling choice/limitation.
2. Complete the ordered K-selection protocol and add adjacent-K rejection
   evidence in Results; move final covariance choices out of Section 3.5.2.
3. Fix Literature Review duplication, heading typo and grammar.
4. Complete variable/descriptor definitions and rebuild the two image tables as
   native numbered Word tables.
5. Replace Bus C3 destination wording and add the remaining measurement-
   difference limitation.
6. Triage figures, complete captions/cross-references and assemble required
   appendix tables before Discussion and Conclusion.

## TM-001 — Version lock and Gap/RQ closure

| Field | Record |
|---|---|
| Status | Complete |
| Source | `Main_body_partV3.docx` |
| Target | `Main_body_partV4_working.docx` and `VERSION_LOCK_PHASE01.md` |
| Transformation | Locked the current Rail/Bus analytical route and revised the Gap–Main RQ–RQ1/RQ2–O1/O2/O3 signposting. The adopted research questions and objectives were retained verbatim. |
| Reason | Close the argument chain before later Methods, Results and Discussion edits. |
| Evidence | Paragraph-level text comparison; main RQ and objectives unchanged; working copy opens successfully. |
| Affected scope | Introduction/research framing only; no analytical outputs changed. |
| Verification | Text and document-structure checks passed. Visual page rendering was unavailable because LibreOffice was not installed, so no page-layout claim is made. |

## TM-002 — Current-label and Bus-window alignment

| Field | Record |
|---|---|
| Status | Complete |
| Source state | Rail labels: current 403-station K=5 file. Bus labels: current 3,383-LSOA K=4 file. The RQ2 context-metrics configuration mixed these current labels with the superseded Bus 18:00–06:00 long table. |
| Transformation | Repointed both primary and weighting-sensitivity configurations to `data_processing/bus_stoparea/outputs_1805_min33/preprocessed/bus_lsoa_night_long.parquet`; locked the expected 11 hourly bins (1080–1680); added fail-fast time-bin and sample-count checks; changed Bus `post_2300_share` to use the available 23:00–05:00 bins; corrected generated interpretation text and stale sample documentation. The 20-variable Rail table now reads the current Rail label file directly rather than inheriting labels through a context-metric intermediate. |
| Reason | Prevent mixing current cluster labels and denominators with an archived data window. |
| Direct evidence | Superseded table: 12 bins, 1080–1740, total activity 6,930,047.30656. Current table: 11 bins, 1080–1680, total activity 6,592,260.64664. Current label counts: Rail 403; Bus retained 3,383. |
| Numeric effect | Across the 3,383 retained Bus LSOAs, correcting the mixed input changed `post_2300_share` for 3,336 units. The mean changed from 0.183352 to 0.134111 (mean absolute change 0.049241); the invalid old calculation produced one share above 1, while the corrected calculation produces none. |
| Affected scope | `rq2_new_clusters_analysis` primary and area-weighted sensitivity context metrics, their reports/figures/data, and the 20-variable Rail input inherited by `rq2_independent_variables`. |
| Final samples | Behaviour metrics: Rail 403, Bus 3,383. LNWC: Rail 387/403 eligible, Bus 3,383/3,383. Formal 20-variable tests: Rail 389/403 complete, Bus 3,383/3,383 complete. |
| Spatial reconciliation | All 387 LNWC-eligible Rail stations are complete for the 20-variable layer. Grange Hill and Roding Valley add two 20-variable cases because their 800m catchments intersect 5 and 7 London LSOAs, although the station points are outside the LNWC extent. The remaining 14 LNWC exclusions have no London-LSOA catchment intersection and are incomplete for all 20 formal variables. |
| Locked LNWC check | Primary equal-weight Rail composition permutation: R-squared 0.260761, p=0.001, n=387, 999 permutations. This is retained as an audit result but remains outside the dissertation reporting scope under the adopted decision. |
| Reproducibility | Two complete reruns rebuilt context metrics, LNWC, 20-variable tables, tests, reports and figures. Of 139 hashed CSV/Markdown/PNG/PDF files, 135 were byte-identical. The only four differences were the generated `Origin Date` lines in the two primary and two sensitivity Markdown reports; no scientific value, table or figure differed. |

## TM-003 — Front-half evidence and Method–Results alignment

| Field | Record |
|---|---|
| Status | Complete for content and structural QA; page-level visual QA unavailable because LibreOffice is not installed |
| Source | `Main_body_partV4_working.docx` |
| Target | `Main_body_partV5_evidence_aligned.docx` |
| Transformation scope | 35 local paragraph replacements across Chapters 3 and 4. Chapters 1–2, the adopted Main RQ and Objectives 1–3 were not rewritten in this batch. V4 was preserved rather than overwritten. |
| Core alignment | Locked Rail at 403 stations, diagonal GMM K=5; Bus at 3,383 retained LSOAs, full GMM K=4; common 18:00–05:00 analytical window. Aligned all cluster headings to the generated current label files. |
| Bus threshold | Replaced the unresolved threshold placeholder with the operational basis: 11 hourly intervals × 3 day types = 33, equivalent to an average of at least one estimated activity per interval and direction. Recorded the existing 18:00–05:00 sensitivity evidence without introducing a new 20/33/50 grid. |
| Behavioural descriptors | Defined `post_2300_share` consistently as 23:00–05:00 divided by 18:00–05:00 for both modes, while retaining mode-native activity measures and separate inference. Confirmed that descriptors were calculated after clustering and did not enter either GMM. |
| Spatial samples | Methods and Results now distinguish LNWC Rail n=387 from continuous-context Rail n=389. All 387 LNWC-eligible stations are in the 20-variable sample. Grange Hill and Roding Valley enter the 20-variable sample through catchments intersecting 5 and 7 London LSOAs but are excluded from LNWC because their station points lie outside its extent. Bus is n=3,383 in both layers. |
| Statistical reporting | Clarified Kruskal–Wallis/epsilon-squared and cluster-vs-rest Mann–Whitney/rank-biserial roles; named BH correction families (20 omnibus tests per mode; 80 Bus and 100 Rail cluster-variable cells); removed wording that treated epsilon-squared as a causal or unique variance contribution. |
| Model-selection boundary | Results now state the BIC-preferred Rail diagonal K=5 and Bus full K=4 specifications and disclose stability limits: Rail seed-refit mean ARI=0.859 and bootstrap mean ARI=0.480; Bus bootstrap mean ARI=0.785 and minimum-cluster Jaccard=0.316. The clusters are described as analytical typologies rather than perfectly separated natural groups. |
| Result corrections | Updated Rail enrichment ratios to current outputs (C2 LNWC1=2.01; C0 LNWC5/6/7=2.13/2.78/3.06), removed the `Figures 4.X and 4.Y` placeholder from the continuous-context result sentence, and aligned Rail/Bus contextual effect sizes and z profiles with the rebuilt 20-variable outputs. |
| Interpretation boundary | Removed the unsupported statement that the results demonstrated night-versus-day differences and passenger behaviour. Reaffirmed observed-use, area-context, exploratory association and descriptive cross-mode wording. |

### TM-003 Method–Results Promise Audit

| Method promise | Results delivery after TM-003 | Decision |
|---|---|---|
| Rail/Bus data, feature construction and GMM selection | Rail 403/K=5/diagonal and Bus 3,383/K=4/full are stated with stability limits | Closed |
| Post-clustering behavioural descriptors | Mode-specific descriptors and the aligned 23:00–05:00 share are reported for the complete fixed-label samples | Closed |
| Bus LNWC categorical association | Cramér's V=0.253, n=3,383 and enrichment interpretation are reported | Closed |
| Rail dominant-LNWC categorical association | Cramér's V=0.405, n=387 and enrichment interpretation are reported | Closed |
| Rail full-composition permutation test | Formal Methods promise removed. The full composition is retained only for descriptive shares and enrichment; the permutation output remains audit evidence outside the dissertation result scope | Closed by scope decision |
| Twenty continuous area variables | Omnibus and cluster-vs-rest layers are reported for Bus n=3,383 and Rail n=389 | Closed |
| Rail–Bus comparison | Methods and Results consistently define this as descriptive synthesis across separate mode-specific analyses | Closed |
| Posterior uncertainty analysis | No formal Methods promise and no Results claim; remains an optional later gate | Not required for current closure |

### TM-003 Verification

| Check | Result |
|---|---|
| Deterministic edit audit | `tm003_edit_audit.json` records all 35 old/new paragraph pairs and source/output SHA-256 hashes |
| Document structure | 331 paragraphs, 0 Word tables and 14 inline shapes before and after; adopted Main RQ preserved verbatim |
| OOXML integrity | DOCX ZIP valid; critical XML parts parsed successfully; package retained the same 28 parts |
| Figure preservation | All 14 embedded media files retained with zero hash differences from V4 |
| Current-data cross-check | Rail labels=403; Bus retained labels=3,383; formal 20-variable n=389/3,383; LNWC n=387/3,383 |
| Residual scan | No 3,372 or 390 sample statements; no old cluster headings; no formal permutation promise; no `Figures 4.X and 4.Y` string; no replacement characters |
| Historical 18:00–06:00 mention | One intentional occurrence remains solely to describe the already-completed controlled sensitivity comparison; it is not presented as the current analytical window |
| Visual QA | Attempted with the required DOCX renderer; failed with `FileNotFoundError [WinError 2]` because LibreOffice/soffice is unavailable. No page-layout claim is made. |

### Deferred to the next batch

The remaining bracketed citation and reproducibility placeholders are deliberately
not filled from inference. They occur in the NUMBAT source citation, BUSTO source
citation and guidance, LNWC citation, threshold/source attribution and POI method
attribution. These require source verification and will form the next unified entry,
`TM-004 — Placeholders and reproducibility closure`.

## TM-003A — Results narrative organisation and Methods bridge

| Field | Record |
|---|---|
| Status | Complete; structural and 60-page visual QA passed |
| Source and target | `Main_body_partV5_evidence_aligned.docx`, edited in place as the single principal working document; no new dissertation version was created |
| Transformation scope | Nine existing paragraphs were replaced and two paragraphs were inserted. All 11 changed locations are red in the principal document. Chapters 1–2, the adopted RQs/objectives, cluster labels, samples, numerical results, figures and contextual tests were not changed. |
| Methods bridge | Replaced the overextended and grammatically incomplete transition in Section 3.8 with a two-stage account: transport-derived types and descriptors first, then external LNWC and continuous-area associations. The replacement explicitly retains station-catchment/LSOA interpretation and excludes passenger-level and causal explanation. |
| Results organisation | Section 4.2 now states the organising dimensions before the cluster catalogue: Rail combines centrality/activity scale, direction and late-night continuation; Bus is framed as a more continuous activity–persistence gradient. Added Section 4.2.3 to synthesise the mode-specific organising dimensions descriptively before moving to area context. |
| RQ closure | Section 4.4 now distinguishes the first stage (identifying and characterising mode-specific observed-use patterns) from the second stage (associating those patterns with LNWC and wider area context). It explicitly excludes passenger identity, causal mechanism, service deficiency and formal cross-mode effect comparison. |
| Use of early Results draft | The early draft informed narrative order only. Its 404/3,372 samples, former labels and cluster sizes, post-01:00 metric, 17-variable layer, LNWC values, full-composition permutation result and exploratory Rail–Bus co-location analysis were not restored. |
| Structural verification | Paragraphs 331→333; Word tables 0→0; inline shapes 14→14. All 14 embedded media files remained byte-identical. Exactly 11 paragraphs contain red runs. Main-document SHA-256 changed from `246de22022fcf06c14300ecd9639e348d31d21a953b56cc04e9277a7d057bf7f` to `822ba97f1b3bbb04236bf12c680b90a21d784f718cd8cee08c4f110580efcaf5`. |
| LibreOffice verification | LibreOffice `26.2.5.2` was located at `C:\Program Files\LibreOffice\` and successfully converted the edited DOCX to a 60-page PDF. The packaged renderer's PDF step works; its direct PNG step lacks Poppler, so `pypdfium2` was used locally for rasterisation. |
| Visual QA | All 60 rendered pages were reviewed in contact sheets, followed by original-resolution inspection of the changed pages (31–32, 36–37, 41, 43, 45 and 53–54). No clipping, overlap, missing glyphs, broken figures or change-induced pagination defect was found. |
| Deferred existing issue | LibreOffice exposed pre-existing letter-by-letter wrapping in part of the GMM rationale paragraph on page 25. This was outside the present Results-alignment scope and is retained for the later language/formatting pass. |
| Next batch | `TM-004 — Placeholders and reproducibility closure`: verify and fill the remaining dataset/method citations and reproducibility placeholders without inferring sources. |

### TM-003 review overlay — red change identification

| Field | Record |
|---|---|
| Purpose | Provide a reviewer-facing copy in which every textual change from the original V3 to the current clean V5 can be located directly in Word. |
| Review file | `Main_body_partV5_evidence_aligned_RED_REVIEW.docx` |
| Baseline | Original `Main_body_partV3.docx` |
| Comparison method | Word-, punctuation- and whitespace-level comparison. Text retained from V3 remains in the document's normal colour; text inserted or substituted in V5 is red. Deleted text is not reinserted. For the single deletion-only heading change, the surviving heading is red so the modification location is still visible. |
| Coverage | 40 changed paragraphs in total: 5 from TM-001 and 35 from TM-003. All 40 contain at least one red run. |
| Clean-copy protection | `Main_body_partV5_evidence_aligned.docx` remains unchanged and is still the clean working version. The red review file is a separate derivative for checking only. |
| Text verification | Review-copy paragraph text is exactly identical to the clean V5 text. The overlay changes font colour only. |
| Structure verification | 331 paragraphs, 0 Word tables and 14 inline shapes retained. All 14 embedded media files are unchanged. Critical OOXML parts parse successfully. |
| Audit evidence | `v5_red_review_audit.json` records the 40 paragraph indices, V3/V5 text pairs, red-run counts and SHA-256 hashes. |
| Visual QA | Rendering was attempted again and failed with `FileNotFoundError [WinError 2]` because LibreOffice/soffice is unavailable. Red-run presence is structurally verified, but no page-level visual-layout claim is made. |

## TM-004 — Placeholders and reproducibility closure

| Field | Record |
|---|---|
| Status | Complete under the user-approved boundary: verified sources were filled; one non-blocking supporting citation remains explicitly marked for later confirmation rather than inferred |
| Source and target | `Main_body_partV5_evidence_aligned.docx`, edited in place as the single principal working document; no additional dissertation version was created |
| Transformation scope | Eight existing Methods paragraphs were replaced, four verified dataset/source entries were added to the reference list, and the incomplete undated Peiret-García reference entry was removed. Chapters 1–2, the adopted RQs/objectives, analytical samples, cluster labels, numerical results, figures and fitted outputs were not changed. |
| NUMBAT closure | Replaced the dataset placeholder with `(Transport for London, 2024)`, named all five representative day types and recorded the five exact source workbooks: `NBT24MON_outputs.xlsx`, `NBT24TWT_outputs.xlsx`, `NBT24FRI_outputs.xlsx`, `NBT24SAT_outputs.xlsx` and `NBT24SUN_outputs.xlsx`. Added a NUMBAT 2024 dataset entry linked to TfL's official crowding-data location. |
| BUSTO closure | Replaced the dataset and guidance placeholders with Transport for London citations. Corrected the provenance detail that the 2024/25 release contains spring 2025 typical-day estimates because autumn 2024 data were unavailable following TfL's cyber incident. Clarified that boardings are derived from ticketing records and scaled, whereas alightings are inferred. The hourly aggregation is now tied directly to TfL's recommendation to sum four consecutive quarter-hours before interpretation or analysis. |
| LNWC closure | Replaced the placeholder and grammatically incomplete description with the verified authorship and evidence base from Mavrogeni et al. (2025): official employment statistics plus mobile-phone footfall data, assigned to seven LSOA night-work types. The existing DOI-backed reference was retained. |
| Context-layer clarification | Rewrote the broken 18-variable source paragraph to distinguish the 18 Census/deprivation indicators from the two POI indicators that form the 20-variable contextual set. Added the June 2026 Ordnance Survey Points of Interest dataset entry and stated explicitly that POI intensity/diversity are post-clustering area-context measures. |
| Rail catchment reproducibility | Replaced the unsupported claim that the hybrid method had already been established by the cited literature with a self-contained operational rationale: 800-metre maximum radius plus Voronoi allocation of overlapping space. The radius is explicitly an analytical convention, not an observed passenger walking route. |
| Citation boundary | The available evidence verified the 2026 GISRUK presentation title for Peiret-García, but not a full publication record or its support for the 800-metre method. No metadata were guessed. The incomplete reference-list entry was removed and one red marker, `[Supporting citation to be confirmed.]`, remains at the radius statement for optional user completion. The method no longer depends on that citation to be intelligible or reproducible. |
| Direct evidence | TfL official open-data description; local `FYP/巴士数据/BUSTO User Guide and Data Dictionary v1.2.pdf` (TfL Public Transport Service Planning, March 2026); the 12 local 2024/25 Total Demand CSVs; the five local NUMBAT workbooks; local `FYP/参考文献/mavrogeni-et-al-2025-creating-the-london-night-worker-geodemographic-classification.pdf`; and the licensed-input record in `rq2_facility_diversity_analysis/data/source/README.md`. |
| Red change identification | All eight replacement paragraphs and all four new reference entries are red. The 11 red paragraphs already present from TM-003A were preserved. Red-paragraph count is 11→23. The deleted incomplete reference is recorded here because deletion cannot be represented by font colour. |
| Structural verification | Paragraphs 333→336; Word tables 0→0; inline shapes 14→14; DOCX package retained 28 parts. Critical XML parts parsed successfully, no old `[insert verified ...]` or `[verified citation]` markers remain, and the only open marker is the single explicitly retained supporting-citation note. |
| Media preservation | All 14 embedded media files remain present; no figure was replaced or edited. |
| LibreOffice and visual QA | LibreOffice 26.2.5.2 converted the edited document to a 60-page PDF. All 60 pages were reviewed in contact sheets, with original-resolution inspection of changed pages 14, 16–17, 19–20, 30, 57 and 59–60. No clipping, overlap, missing glyphs, broken figures or change-induced pagination defect was found. The pre-existing GMM-rationale wrapping issue on page 25 remains deferred. |
| Hashes | Main-document SHA-256 changed from `822ba97f1b3bbb04236bf12c680b90a21d784f718cd8cee08c4f110580efcaf5` to `2e995eb3b52014fec0d7bd9b2e970c38f8e75927bce293a28bd764dbe074de5d`. |
| Next step | Continue the planned front-half content alignment by auditing the remaining Methods prose for internal consistency and readability before moving to sensitivity analysis or Discussion. Citation-only completion can proceed later without restructuring the argument. |

## TM-005 — remaining front-half Methods alignment

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | `Main_body_partV5_evidence_aligned.docx`, edited in place as the single principal working document; no new dissertation version was created |
| Transformation scope | Nine existing Chapter 3 paragraphs were replaced: area-context framing (76); the two feature-construction headings and Bus-composition explanation (100, 109–110); GMM rationale and model-selection prose (132, 139–140, 143); and the post-clustering descriptor inventory (147). The adopted RQs/objectives, all formulas, analytical samples, cluster labels, numerical results, figures and fitted outputs were not changed. |
| Formula and definition control | Native Word equations were inspected before editing and excluded from the replacement set. The document retains all 53 OMML nodes. The surrounding prose now defines the role of BIC, ARI, bootstrap stability, CLR motivation and the mode-specific descriptor inventory without altering the formulas or their results. |
| GMM layout repair | The pre-existing letter-by-letter wrapping in the page-25 GMM rationale was removed by replacing the malformed prose with a shorter, technically bounded explanation of covariance flexibility, probabilistic allocation and analytical-typology interpretation. |
| Red change identification | All nine replacement paragraphs are red; existing red text was retained. |
| Structural verification | Paragraphs 336→336; Word tables 0→0; inline shapes 14→14; native equation nodes 53→53. Critical DOCX XML parts parsed successfully; the package retains 28 parts. |
| Visual QA | LibreOffice 26.2.5.2 rendered the edited document to a 60-page PDF. The Methodology review range was rendered to PNG; pages 25–27 were inspected at high resolution. The repaired GMM text, equations, headings and page transition show no clipping, overlap, missing glyphs or broken pagination. |
| Audit evidence | `tm005_edit_audit.json`; `scripts/build_v5_tm005.py`; rendered review files in `render_tm005/`. |
| Hashes | Main-document SHA-256 changed from `2e995eb3b52014fec0d7bd9b2e970c38f8e75927bce293a28bd764dbe074de5d` to `5a1695c261542385f757d6ccba1294e2b9d434b0db967be955625de1dd1a54cb`. |
| Next step | Sensitivity evidence consolidation: state the fixed main specification, the controlled comparator, the affected sample and the observed stability/change; do not add a new threshold grid or blend incompatible Rail-radius outputs. |

## TM-006 — Table integration and Results compression

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | `Main_body_partV5_evidence_aligned.docx`, edited in place after the user added the Rail/Bus model-specification table |
| Table preservation | The user-added 3×5 Word table was retained without alteration: Mode, analytical unit, clustering sample, final K and covariance structure for Rail and Bus. |
| Transformation scope | Replaced three Results paragraphs only. The Chapter 4 opening now gives a short roadmap; the former repeated model-selection paragraph was split into the title `Table 2. Adopted mode-specific clustering specifications` before the table and a concise post-table BIC/stability interpretation. |
| Narrative decision | The table now carries the repeated bookkeeping information (analytical unit, clustering sample, K and covariance structure). The remaining prose reports only the model scan, BIC preference, ARI/bootstrap evidence and the analytical-typology boundary. |
| Scope protection | No result, sample, label, statistic, formula, figure or user-table value was changed. |
| Structural and visual verification | Paragraphs 337→337; Word tables 1→1; inline shapes 14→14; native equation nodes unchanged. The document rendered to a 60-page PDF; the table page was inspected at high resolution and showed no clipping, overlap or broken pagination. |
| Audit evidence | `tm006_edit_audit.json`; `scripts/build_v5_tm006_table_integration.py`; rendered review files in `render_tm006/`. |
| Hashes | Main-document SHA-256 changed from `8d90273d5cab4540c985006d24440030aa86d7ea6807556616370466b7a5683a` to `599fca59be436b9e550677f5ea6ca0cab9da10dadf8144c179b3926455c54f9f`. |
| Next step | Draft Chapter 5 Discussion from the locked Results evidence. Sensitivity evidence and the Rail catchment sensitivity gate are deferred; they will be reopened only if a defined interpretive claim cannot be supported without them. |

## TM-007 — Chapter 4 figure/table source alignment

| Field | Record |
|---|---|
| Status | Complete, subject to final visual-render check recorded below. |
| Source and target | `Main_body_partV5_evidence_aligned.docx`, edited in place as the sole main working document; the single main-text figure set is `final_figures/`. |
| Reproducible generator | `scripts/build_ch4_final_figures.py`; it reads locked labels and current formal output CSVs only and does not fit, relabel, or retest any model. |
| Locked inputs | Rail 403 stations / diagonal GMM K=5; Bus 3,383 LSOAs / full GMM K=4 / 18:00–05:00 / threshold 33; Rail LNWC n=387; Rail continuous context n=389. |
| New figures | Figures 4.1–4.9: K-selection/stability; mode-specific temporal profiles and maps; separate Rail/Bus LNWC enrichment heatmaps; separate Rail/Bus epsilon-squared plus z-score contextual panels. |
| Table integration | The existing model-specification table was expanded into Table 4.1; Tables 4.2 and 4.3 were added from current behavioural-test and LNWC-statistical-summary CSVs. Table 4.4 remains appendix-pending. |
| Colour and label rule | `final_figures/COLOUR_AND_LABEL_REGISTER.md` is the shared register. Cluster colour is mode-specific and separate from fixed movement line colour/style. |
| Source-risk control | `final_figures/FIGURE_SOURCE_INVENTORY.md` records every Figure/Table source and flags retired 404/3,372 results. Rail Figure 4.6 uses `rail_enrichment.csv` (full equal-station 800m catchment enrichment), not the dominant-LNWC reduction. |
| Text changes | Updated Chapter 4 figure/table references and captions. All replacement/addition text and new table text were coloured red; pre-existing red content was not reset. |
| Interpretation control | Results captions/text state separate mode-specific units, samples and definitions; LNWC is area context; enrichment is benchmark-relative; epsilon-squared is distinct from z-score; no causal, passenger-identity, latent-demand, service-deficiency or formal cross-mode-effect claim was added. |
| Statistical change | None. This batch changes presentation and source alignment only. |
| Deferred | Table 4.4 appendix, Rail–Bus synthesis figure, posterior uncertainty, new CLR/ILR model, threshold comparison figure and expanded diagnostics remain pending by instruction. |
| Visual check | All nine generated figures were inspected in a contact sheet before DOCX integration. LibreOffice 26.2.5.2 was found, but two headless PDF conversion attempts (normal and unique-profile) produced no PDF or diagnostic output in `render_tm007`; therefore no DOCX page-layout/pass claim is made for TM-007. This remains the blocking final-acceptance item. |

### TM-007R — Priority correction following user review

| Field | Record |
|---|---|
| Reason | The user correctly identified that TM-007 had over-compressed the Section 4.1 Results prose and promoted three unsuitable large tables into the main text. |
| Correction | Removed all three TM-007 Word tables and their captions from the Chapter 4 main text. The reproducible CSV tables remain in `final_figures/` as appendix candidates, not deleted evidence. |
| Restored prose | Restored the complete current-data K-selection paragraph after the Section 4.1 heading: Rail diagonal K=5, Bus full K=4, current ARI/bootstrap/Jaccard qualifications and the analytical-typology limitation. Replacement text is red. |
| Figure 4.1 | Regenerated `Figure_4_1_k_selection_and_stability.png` with the original three-part fit/stability structure and an explicit fourth bootstrap-ARI row for Rail and Bus below it. |
| Statistical change | None; repair and presentation revision only. |
| Remaining figure work | Rebuild Figure 4.2/4.3 in the legacy-profile-plus-current-metrics logic; retain only effect-size ranking in the compact contextual figures and restore the complete z-score display as a separate full matrix. |

## TM-008 — Planned figure-led Results synthesis and boundary redistribution

| Field | Record |
|---|---|
| Status | Planned and approved in principle; no dissertation prose or figure placement changed in this decision-record batch. |
| Current working document | Treat `Main_body_partV5_evidence_aligned_work.docx` as the sole editable main draft. Retain `Main_body_partV5_evidence_aligned_backup.docx` as recovery evidence only. |
| Reason | Figures 4.1–4.9 now provide the main visual evidence, but the surrounding Results still reproduces many exact values and repeats negative inference-boundary statements. The next revision must make the figures and tables carry evidence while the prose synthesises patterns, contrasts and bounded interpretation. |
| Candidate Results tables | The CSVs in `final_figures/` are reproducible source summaries, not approved main-text layouts. Table 4.1 contains unformatted full-precision shares and descriptors that repeat cluster IDs; Table 4.2 combines non-identical mode-specific descriptor sets, contains machine-form p-values including `0.0`, and is too wide/dense for direct Word insertion; Table 4.3 is only a two-row summary and repeats a spatial-autocorrelation caveat that is better handled once in Methods/Limitations. None will be inserted unchanged. |
| Table decision | Redesign only where a table improves auditability. A compact cluster lookup may be integrated with the existing model table or caption system; detailed behavioural statistics and full contextual tests remain appendix-table candidates. LNWC association statistics may remain concise prose if a two-row table adds no retrieval value. Exact layout and main/appendix placement require a rendered-width check before insertion. |
| Legacy LNWC reference composites | Move the two existing `cluster map + LNWC reference map` composites out of the Chapter 4 main narrative and retain them temporarily as appendix candidates. Main Results will cross-reference the already retained mode-specific cluster maps and LNWC enrichment heatmaps rather than repeating the spatial panels. |
| Results compression | Remove redundant point-by-point numerical recitation where the same values are already legible in a figure or appendix table. Retain only decision-relevant magnitudes, extrema, contrasts and statistics needed to substantiate the paragraph's claim. Each paragraph should answer what pattern matters and how it advances O1–O3, rather than narrating every cell or bar. |
| Boundary redistribution | Keep measurement definitions once in the Data section and analytical-unit/inference scope once in Methods or at the opening of the relevant Results section. Delete repeated end-of-paragraph statements about what the result cannot identify or prove. Consolidate ecological fallacy, causality, spatial autocorrelation, typical-day uncertainty, MAUP/catchment uncertainty and service-deficiency/unmet-demand boundaries in Discussion/Limitations, except where one local warning is essential to prevent a specific misreading. |
| Positive bounded interpretation | Prefer affirmative, neutral statements of supported pattern: observed directionality, persistence, spatial concentration, enrichment and area-level correspondence. Results may add cautious trend or mechanism-oriented interpretation when it is visibly supported by the current figure/statistic and is signalled as `suggests`, `is consistent with`, `may reflect` or equivalent. Such interpretation must not introduce passenger identity, trip purpose, causality, latent demand, unmet need or service-deficiency claims. More developed mechanisms belong in Discussion. |
| Mode-specific interpretation | Retain Rail as a more structured directional/node-role typology and Bus as a more continuous activity–persistence gradient, explicitly as descriptive synthesis. Bus C3 remains `alighting-oriented estimated activity`; it is not relabelled as a verified destination or travel-purpose type. |
| Methods alignment | Revise Methods only where the new figure/table presentation exposes a missing definition, statistic, selection rule or output destination. Do not rewrite Methods to repeat captions or Results, and do not add a new analytical branch. |
| Planned execution order | (1) finalise the main-versus-appendix figure inventory; (2) move the two legacy LNWC composites to appendix candidates; (3) decide the compact table/appendix-table architecture; (4) create a paragraph-level Results evidence map for Figures 4.1–4.9; (5) rewrite Results for synthesis and positive bounded interpretation; (6) align only affected Methods text and captions; (7) transfer consolidated limitations to Chapter 5; (8) update cross-references and render the full DOCX for visual QA. |
| Acceptance checks | No current statistic or cluster label changes; every retained exact value has a clear evidential purpose; repeated boundary language is materially reduced; each main figure supports one explicit claim; interpretation remains distinguishable from observation; appendix moves preserve auditability; all new/replaced DOCX text remains red; full LibreOffice render shows readable figures, captions and pagination. |

### TM-008 execution checklist — use of the legacy Results interpretation draft

Legacy reference copy: `legacy_reference/结果部分整理_legacy_interpretation_reference.docx`  
Original supplied file: `C:/Users/fangz/Desktop/结果部分整理.docx`  
SHA-256 for both files: `BC2BA856112D35EF023BBA4DF0891BDB9BCD2A87AF37C3FC8578696602EDFC59`

The file is an interpretation aid, not a current evidence source. Its opening
uses the current headline sample counts, but its LNWC values, contextual
statistics and some cluster descriptions derive from earlier analytical
states. It must never be cited as a formal output or used to override the
locked current figures and CSVs.

- [ ] Build a current-evidence record for each Rail C0–C4 and Bus C0–C3 using
  the current temporal profile, map, behavioural descriptors, LNWC enrichment
  and contextual panels before consulting the legacy wording.
- [ ] Extract from the legacy draft only candidate organising ideas: temporal
  timing, direction balance, spatial concentration, late-night persistence,
  activity scale and the Rail-versus-Bus narrative contrast.
- [ ] Retain its useful paragraph logic where appropriate: plotted observation
  → spatial/descriptor corroboration → concise cluster definition → cautious
  interpretation.
- [ ] Verify every retained cluster statement against at least one current
  figure and, where it contains magnitude, rank or association, the matching
  current statistical output.
- [ ] Replace every legacy sample, effect size, z-score, Cramér's V and
  enrichment ratio with the current value or omit it if it is no longer needed.
- [ ] Do not restore the unsupported night-versus-day comparison or treat the
  legacy prose as evidence of significant daytime differences.
- [ ] Reframe passenger or trip stories such as residents arriving, returning
  home, night workers, special passenger groups or journey purpose as either a
  cautious pattern-level interpretation (`suggests`, `is consistent with`,
  `may reflect`) or a Discussion hypothesis.
- [ ] Keep Bus C3 as `alighting-oriented estimated activity`; do not reinstate
  `destination type`, verified destination function or travel-purpose labels.
- [ ] Preserve the descriptive synthesis that Rail is more structured by
  direction/node role whereas Bus is more continuous along an
  activity–persistence gradient, without presenting it as a formal cross-mode
  statistical test.
- [ ] Use the legacy contextual discussion only to identify questions for the
  current Figure 4.6–4.9 evidence; do not reuse its old LNWC or continuous-
  context numbers.
- [ ] Mark in the paragraph-level Results evidence map whether each final
  interpretation is `direct observation`, `statistically supported synthesis`
  or `bounded interpretation`.
- [ ] After rewriting, run a legacy-leakage audit for old values and high-risk
  labels, including Rail Cramér's V `0.377`, legacy enrichment values, generic
  `destination type`, passenger-group claims and former figure numbering.

Checklist exit condition: the legacy draft has improved explanation and
paragraph structure without contributing any unverified number, superseded
label or stronger inference than the current evidence permits.

### TM-008A — Results evidence-led rewrite

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | `Main_body_partV5_evidence_aligned_work.docx`, edited in place as the current main working document. |
| Transformation scope | Replaced 63 existing Chapter 4 Results paragraphs only (paragraphs 196–304). No paragraph was added/deleted; titles, captions, tables, figure placement, samples, labels, fitted outputs and statistical tests were not changed. |
| Evidence basis | `TM008_RESULTS_EVIDENCE_MAP.md`, Figures 4.1–4.9, the current template tables, and the locked current output CSVs. The legacy interpretation reference guided paragraph logic only and contributed no unverified number or superseded label. |
| Narrative change | Results now foregrounds within-mode organising contrasts and evidence-carrying figures rather than repeating every profile, enrichment or contextual cell. Rail is synthesised as a structured directional/node-role typology; Bus as an activity–persistence gradient with overlapping intermediate profiles. |
| Boundary control | Bus C3 was changed from destination language to `alighting-oriented estimated activity`. Context remains post-clustering, area-level correspondence; no passenger identity, travel purpose, causality, unmet-need, service-deficiency or formal cross-mode effect claim was introduced. |
| Red change identification | All 63 replacement paragraphs are red. Existing non-Results text was not globally recoloured. |
| Structural verification | Paragraphs remain 356; Word tables remain 2 (Rail 6×7; Bus 5×8); inline shapes remain 17; DOCX media count remains 17. |
| Visual QA | LibreOffice 26.2.5.2 rendered the document to a 63-page PDF. Chapter 4 pages 34–54 were rasterised and inspected in contact sheets. Figures, template tables, captions and the revised text showed no clipping, overlap or change-induced pagination defect. |
| Hash | `word/document.xml` SHA-256 after the rewrite: `16cac3ab3c0c31bb66a5a44acf2446ae30af7a92128442c6ff80fbd4a93a0a1f`. |
| Next step | Review the red Results rewrite for substantive preference. Only then revise affected Methods/captions if a concrete presentation-definition mismatch remains; Chapter 5 limitation consolidation follows separately. |

### TM-008B — Results refinement after user review

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | `Main_body_partV5_evidence_aligned_work.docx`, edited in place as the active working document. |
| User-directed refinement | Restored the multi-criterion logic for K selection: BIC/model fit, reproducibility/stability and substantive interpretability jointly support Rail K=5 and Bus K=4. |
| 4.2.3 | Expanded the contrasting-organising-dimensions section from one sentence to two connected paragraphs. It now explains the Rail station-level directional/node-role structure, the Bus LSOA-level activity-persistence gradient, and why the same contextual question is read through these different mode-specific structures. |
| 4.3 / 4.4 | Removed/replaced repetitive defensive wording. Area-context introduction now frames the contribution as spatial embedding of observed-use types. The final Results sentence now bridges positively to Discussion on what the mode-specific structures imply for London night-time mobility. |
| Continuous context prose | Replaced numerical listing with figure-led interpretation. Rail discusses central–outer combinations and C3's distinct persistent-use context; Bus discusses the linked residential, facilities and activity-context gradient. Figures continue to carry the full ranking and z-score detail. |
| Scope protection | No sample, cluster label, statistic, figure, caption, table value, method, formula or fitted output changed. Bus C3 remains `alighting-oriented estimated activity`; no destination-function claim was restored. |
| Change identification | 16 existing paragraphs replaced and one supporting paragraph inserted; all 17 new/replaced paragraphs are red. |
| Structural verification | Paragraphs 351→352; Word tables remain 3 (3×5, 6×7, 5×8); inline shapes remain 17; media count remains 17. |
| Visual QA | LibreOffice 26.2.5.2 rendered a 63-page PDF. Chapter 4 pages 34–56 were rasterised and inspected. No clipping, overlap, broken figure/table, missing glyph or change-induced pagination defect was found. |
| Hash | `word/document.xml` SHA-256 after refinement: `da8a61695f74dcda6543917a06dead1987ed1fba309ea8de456b471093238121`. |

### TM-008C — Methods alignment with Results presentation

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | `Main_body_partV5_evidence_aligned_work.docx`, edited in place as the active working document. |
| Transformation scope | Eight existing Methods paragraphs replaced (3.5.3: 138–139, 142–143; 3.6: 146; 3.8.2: 179–181). No formula, section heading, table, caption, figure, sample, label, test or output changed. |
| K-selection alignment | Methods now states the final selection logic explicitly: BIC supplies the primary fit-complexity criterion, while seed/ bootstrap reproducibility, supporting separation diagnostics and substantive profile interpretability qualify the final K choice. |
| Descriptor alignment | Methods now defines night-behaviour z-score panels as descriptive standardised fixed-cluster means relative to the mode-wide mean. They are neither clustering inputs nor additional inferential tests. |
| Context-panel alignment | Methods now explicitly distinguishes epsilon-squared (within-mode Kruskal–Wallis effect-size ranking) from z-scores (directional descriptive display), while retaining Mann–Whitney/rank-biserial procedures and all BH correction counts unchanged. |
| Change identification | All eight replacement paragraphs are red. |
| Structural verification | Paragraphs remain 352; Word tables remain 3 (3×5, 6×7, 5×8); inline shapes remain 17; media count remains 17. |
| Visual QA | LibreOffice 26.2.5.2 produced a 64-page PDF. Methods pages 20–34 were rasterised and inspected; equations, the revised paragraphs, page transitions and the Results transition show no clipping, overlap, missing glyph or pagination defect. |
| Hash | `word/document.xml` SHA-256 after Methods alignment: `6ed51de77a75903df2e43916c8c65ccef85f272b5118790b7840ef265ff3d5df`. |
| Next step | Move to the separately scoped Chapter 5 Discussion and limitations consolidation after user review of the current red Methods text. |
## TM-009 — Argumentative-language calibration (2026-08-13)

**Authority.** User requested a more argumentative and less mechanical dissertation voice, explicitly preserving all results and substantive claims. The request identified the GMM/K-selection explanation as the primary example and asked for calibration against the CASA handbook and local high-scoring work.

**Calibration.** The CASA Dissertation Handbook's writing-up guidance and the current CASA marking scheme were checked. A local 2025 CASA MSc reference dissertation was read only for broad rhetorical organisation, not copied. The local calibration note is `TM009_ARGUMENTATIVE_LANGUAGE_CALIBRATION.md`.

**Applied scope.** `Main_body_partV5_evidence_aligned_work.docx`, Sections 3.5-3.8 and Chapter 4 explanatory/linking paragraphs only. 34 paragraphs were replaced and rendered in red. No heading, formula, figure, table, caption, research question, dataset, sample, variable, statistic, result, cluster label or substantive inference changed.

**Key language corrections.**

- Recast K selection as an analytical judgement between candidate model representations: BIC supplies the starting point, reproducibility/stability qualifies the selection, supporting indices and profile interpretation complete the judgement.
- Recast GMM, post-clustering descriptors, spatial linkage and continuous-context methods around the analytical purpose of each step rather than a procedural sequence.
- Strengthened Results transitions so that temporal typology, spatial context and mode-specific interpretation form a continuous argument without new claims.
- Preserved the existing evidential boundaries: area context remains post-clustering and area-level; Rail/Bus are not formally cross-mode tested; z-scores remain descriptive rather than inferential effect sizes.

**Verification.** DOCX structure remained 352 paragraphs, 3 tables and 17 embedded figures. All 34 replacement paragraphs (plus one punctuation-only sentence cleanup) were confirmed red. LibreOffice rendered the final document successfully to a 64-page PDF; full-document contact sheets and the affected Method/Results pages were visually reviewed with no clipping, overlap or pagination defect. Final DOCX SHA-256: `2fa31851090d982bed066934ed782c1c9f437ccf4602123e6a90241bc0c2da1b`.

## TM-010 — V6 Results narrative refinement and archive transition

| Field | Record |
|---|---|
| Status | Complete |
| Version transition | `Main_body_partV5_evidence_aligned_work.docx` is frozen as the pre-V6 archive without renaming. Its SHA-256 remains `36e2d3fd2ac449909b40be9377c221fa179aa4997d188bdb83bbf7a0720afb3d`. The active working document is now `Main_body_partV6.docx`. |
| Authority | User prioritised complete, natural and argumentative academic expression over mechanical shortening. Repeated defensive caveats and metric-list prose were to be replaced with figure-led interpretation, without losing supported observations or introducing passenger, trip-purpose, causal, latent-demand or service-deficiency claims. |
| Calibration | Applied the existing CASA handbook/reference-dissertation calibration in `TM009_ARGUMENTATIVE_LANGUAGE_CALIBRATION.md`: concise and pertinent writing, a clear line of argument, and analysis/commentary rather than a raw-results record. Common direct academic English was preferred over compressed, unusual or formulaic AI-like phrasing. No wording was copied from reference dissertations. |
| Transformation scope | Twenty-one Chapter 4 paragraphs were replaced: Rail C0–C4 interpretation and synthesis; Bus C0–C3 interpretation and synthesis; one Rail LNWC interpretation; one Rail continuous-context synthesis; and the Figure 4.8/4.9 captions. The Results structure, headings, figure numbering, figures, tables, samples, labels and statistical outputs were otherwise retained. |
| Narrative outcome | Rail cluster descriptions now connect temporal shape, direction and spatial role before presenting a concise definition. Bus descriptions explain the high-activity/persistent to low-activity/early-declining gradient and the overlapping intermediate profiles. Key discriminating values remain where they clarify a definition; repeated lists of log activity, shares and persistence metrics were removed when the appendix tables/figures already carry them. |
| Boundary redistribution | Repetitive Chapter 4 statements framed as what a result cannot identify or prove were removed from the replaced paragraphs. Positive, evidence-bounded interpretation now states what the profiles and contextual correspondence show. General measurement, ecological and causal limitations remain reserved for the appropriate Data/Methods and forthcoming Discussion/Limitations treatment. |
| Appendix correction | In the Bus cluster-characteristics appendix table, `C3 moderate activity with destination characteristics` was replaced with `C3 moderate activity with alighting-oriented estimated activity`, matching the current Results label. |
| Caption correction | Figure 4.8 and Figure 4.9 captions now describe panels `(a)` effect-size ranking and `(b)` z-score profiles rather than referring to `left` and `right`, because the panels paginate vertically in the current Word layout. |
| Change identification | All 21 replacement paragraphs and the corrected appendix table cell use yellow highlighting. Pre-existing red formatting remains unchanged elsewhere; V5 contains no yellow highlighting and was not edited. |
| Word-budget result | Chapter 4 changed from 2,513 to 2,673 words (+160). The increase is intentional and consists of substantive comparison and interpretation. Numeric tokens decreased from 140 to 129, showing that repeated metric recitation was reduced without imposing an artificial word-reduction target. |
| Structural verification | V5 and V6 both retain 354 body paragraphs, 3 native Word tables, 19 drawings and 19 media files. V6 contains exactly 21 yellow-highlighted body paragraphs plus the yellow-highlighted corrected appendix cell. Searches found no remaining `destination characteristics`, legacy Rail Cramér's V `0.377`, old `Figures 5.*` or `Figure X` leakage. |
| Visual QA | LibreOffice rendered V6 to 64 pages. Results through Appendix pages 34–64 were rasterised and inspected. Yellow highlighting is visible; figures, tables and captions show no clipping, overlap, missing glyphs or broken pagination. The two legacy cluster-map/LNWC-reference composites remain in the appendix rather than Chapter 4. |
| Reproducibility | Generator: `scripts/build_v6_results_refinement.py`. V6 SHA-256: `92d9702dccf9505c94213f0ec95f41c10c4f02f810ccb2a517c6d8dc9bd70fe7`; `word/document.xml` SHA-256: `37c8467db9d28ba96769bd49b27d6c4b7ca52561aa52a00041908ad5bdaa5fee`. |
| Next step | User review of the yellow V6 Results changes. After approval, draft Chapter 5 Discussion/Limitations so the released word space and consolidated boundary material are used for interpretation, contribution, limitations and implications rather than reintroduced into each Results paragraph. |

## TM-011 — V6 Methodology verification and expression alignment

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | `Main_body_partV6.docx`, edited in place after TM-010. The frozen V5 archive remained unchanged. |
| Authority | User requested a further Methodology verification and expression pass, retaining content completeness and preferring natural, direct academic language over mechanical compression or formulaic AI-style phrasing. All new changes remain yellow-highlighted. |
| Verification finding | Section 3.4.2 still contained the superseded claim that compositional constraint was less consequential for Rail because it had 220 intervals per direction. The text now states that normalisation produces compositional profiles in both modes; Bus uses CLR, while Rail raw shares remain a pragmatic modelling choice whose compositional limitation is acknowledged. No new Rail CLR/ILR model or sensitivity result was introduced. |
| Structural corrections | The duplicated heading `3.4 Feature Engineering Direction-specific normalisation` was corrected to `3.4 Feature Engineering`; `Table 1` was corrected to `Table 3.1`. The four covariance structures remain in Methods, while the final Rail diagonal and Bus full choices are reported in Results 4.1 rather than repeated as Methods findings. |
| Expression scope | Fourteen Methods paragraphs were replaced: the separate-mode design; Rail/Bus composition; GMM rationale; covariance comparison; K-selection and stability logic; descriptor measurement note; 800 m buffer wording; contextual-stage bridge; and continuous-context test interpretation. Data lineage, thresholds, samples, equations, variable definitions, correction families and test procedures were retained. |
| Argumentative outcome | K-selection is framed as a judgement among candidate representations: BIC identifies competitive solutions, seed/ARI and bootstrap evidence assess reproducibility, and separation/profile interpretation qualify the final choice. Contextual methods state their analytical purpose positively and retain one clear area-level unit boundary instead of repeating lists of prohibited interpretations. |
| Content-preservation control | An initial attempt to replace the epsilon-squared definition paragraph removed three inline OMML variables. That draft was discarded. V6 was rebuilt from the frozen V5 source and the safe Methods edits reapplied with the formula-bearing paragraph excluded. Final V6 matches V5 at 40 `oMath` nodes, 12 `oMathPara` nodes and 102 `m:ctrlPr` nodes. |
| Change identification | Final V6 contains 35 yellow-highlighted body paragraphs: 21 Results paragraphs from TM-010 and 14 Methods paragraphs from TM-011, plus one yellow-highlighted appendix table cell. Pre-existing red content remains elsewhere. |
| Word-budget result | Methodology changed from 4,043 words in frozen V5 to 4,013 words in final V6. The small reduction reflects removal of duplicated/result-like wording; no variable, formula, sample or reproducibility detail was intentionally removed. |
| Structural verification | Final V6 retains 354 body paragraphs, 3 native Word tables, 19 drawings, 19 media files, 40 inline-equation nodes and 12 equation paragraphs. Searches confirm removal of the superseded Rail-composition sentence, the mechanical `GMM cannot identify the optimal number` opening, the old `Table 1` caption and the old Bus C3 destination label. |
| Visual QA | LibreOffice rendered the final V6 to 65 pages. Methods through Appendix pages 20–65 were rasterised and inspected. Yellow highlights, equations, Table 3.1, figures, captions and appendix materials show no clipping, overlap, missing glyphs or broken pagination. |
| Reproducibility | Methods generator: `scripts/refine_v6_methods.py`; Results/V6 generator: `scripts/build_v6_results_refinement.py`. Final V6 SHA-256: `ae1658876dad96cc7141da27a8c8a6a425d3500364ed41c9392f9f692e740396`; `word/document.xml` SHA-256: `b894a23f6e8f796fcffd83e02ebd8eca9b8d9904a62b54ccef02ec759132fc33`. |
| Next step | User review of the yellow Methods and Results text. Then proceed to Chapter 5 Discussion/Limitations and the remaining appendix/cross-reference audit. |

## TM-012 — V6 Discussion and Conclusion completion

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | The latest user-reviewed `Main_body_partV6.docx` was used as the sole baseline and edited in place. Its pre-edit SHA-256 was `b0591d56e4e31f1219d9633a113247cf814d9e3c0922c7cf3060687901113063`. The frozen V5 archive was not edited and the earlier V6 build scripts were not rerun, so subsequent manual wording changes in Methods and Results were preserved. |
| Agreed structure | Chapter 5 now contains six connected sections: mode-specific overall interpretation; Rail node roles and late-night persistence; the Bus activity-persistence gradient; the contribution of LNWC and continuous area context; planning relevance; and integrated interpretive limits/future research. Chapter 6 closes the main RQ and Objectives 1–3 in five concise paragraphs. |
| C3 interpretation | The Discussion develops the observed association between Rail C3 persistence and relatively higher health deprivation, unemployment and social renting into a cautious equity-relevant interpretation. Lower-paid, on-site and less temporally flexible night work is presented as one plausible mechanism alongside leisure, interchange, service and land-use alternatives. No passenger occupation, income or causal effect is asserted. |
| Literature dialogue | Chapter 5 reconnects the results to the existing night-mobility, smart-card, temporal-accessibility and equity literature already present in the dissertation. The locally available full text of Peiret-García, Kimani and Suel's `Beyond the Commute` manuscript was checked directly. Its working-class/deprivation and non-standard-time finding is treated as a related all-day precedent, explicitly not a replication of C3. One transparent `no date`, unpublished-manuscript reference was added; no publication year, venue or identifier was invented. |
| Centre–outer reflection | Residence-based indicators are described as having spatially uneven interpretive reach: potentially closer to local social context around outer residential locations and weaker as passenger proxies around central employment, entertainment and interchange nodes with non-local users. This is recorded as the dissertation's own methodological reflection derived from the data structure and results. No meeting, supervisor or conference discussion is cited. |
| Limitations logic | Measurement, ecological, spatial-scale and cross-mode-comparability limits are integrated into the argument and used to motivate specific next analyses. The Results chapter was not repopulated with repetitive negative caveats. A short concluding boundary paragraph remains because it defines what the completed evidence supports. |
| Conclusion rule | Chapter 6 contains no author-year citations, no new evidence and no new interpretive claim. It restates the investigation, how it was completed, the main findings, their significance and the evidence boundary, following the CASA handbook instruction not to add new material or references in the Conclusion. |
| Change identification | All 30 non-empty Discussion paragraphs (including six section headings), all five Conclusion paragraphs and the added BtC reference are yellow-highlighted. Pre-existing red and yellow material elsewhere was retained. |
| Word result | Discussion: 2,568 words. Conclusion: 516 words. The added length is used for synthesis, comparison, mechanism alternatives, contribution, implications and methodological reflection rather than numerical repetition. |
| Structural verification | Body paragraphs increased from 354 to 388. The automated audit confirmed that every new Discussion and Conclusion paragraph is yellow-highlighted, the Conclusion contains no citation-like author-year strings, the BtC reference occurs once, and no `Howard`, `meeting`, `supervisor` or `conference` wording appears in Chapter 5. |
| Visual QA | LibreOffice 26.2 rendered the revised V6 successfully to a 77-page PDF. All 77 pages were rasterised and inspected through page contact sheets, including the new Chapters 5–6 and the shifted reference/appendix pages. No clipping, overlap, missing glyph, broken figure/table or change-induced pagination defect was found. |
| Reproducibility | Writer: `scripts/write_v6_discussion_conclusion.py`; structural audit: `scripts/audit_v6_discussion.py`; final V6 SHA-256: `6f89c85710ba8ffbdea4dc46f00e8783839a2b0cb1e4e9ebeb2d4727bb36d58e`. |
| Next step | User substantive review of the yellow Discussion and Conclusion. After approval, run the remaining citation/cross-reference, terminology, appendix and final rubric audits without reopening the analytical model unless a concrete inconsistency is found. |

## TM-013 — Argument-led Discussion restructuring and concise Conclusion

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | The latest `Main_body_partV6.docx` after TM-012 was edited in place. Pre-edit SHA-256: `6f89c85710ba8ffbdea4dc46f00e8783839a2b0cb1e4e9ebeb2d4727bb36d58e`. No earlier V6 builder was rerun, and Chapters 1–4, existing figures/tables and manual edits were preserved. |
| Authority | User and external review identified that the previous Chapter 5 followed the Results chapter's Rail-then-Bus order, repeated results and premise-level claims, and duplicated contribution statements across 5.1, 5.5 and Chapter 6. The approved revision required an argument-led cross-mode structure, clearer use of the temporal curves, fuller consideration of Bus scale effects and attention to the 12,000-word CASA limit. |
| New Chapter 5 structure | `5.1 Answering the research question`; `5.2 Why Rail and Bus reveal different night-time structures`; `5.3 Night-specific transport functions and extended-hour activity`; `5.4 Interpreting area context across central and outer London`; `5.5 Implications for night-time transport and equity`; `5.6 Interpretive limits and future research`. The chapter is now organised by explanatory claim rather than transport-mode workflow. |
| Direct RQ closure | 5.1 gives a positive two-part answer: differentiated Rail node roles and a Bus area-level activity-persistence gradient, followed by how both correspond with night-work and wider urban context. The previous `not a single map ... instead` construction and extended re-justification of the night as a separate analytical period were removed. |
| Rail-Bus explanation | 5.2 distinguishes substantive system structure from observation scale. It discusses Rail discrete nodes and entry/exit direction; Bus aggregation of multiple StopAreas to LSOAs; hourly smoothing; estimated alightings; and the possibility that dense, many-stop/local Bus travel yields less specialised OD roles. The last mechanism is explicitly framed as an OD-testable proposition because BUSTO lacks complete journey chains and distance. Analytical scale is presented as contributing to, not determining, the contrast. |
| Night-specific functions | 5.3 uses the temporal curves as evidence for central evening dispersal (Rail C1), continuing interchange (C2), extended-hour persistence (C3), persistent Bus areas (Bus C1) and earlier-declining areas (Bus C0). These are described as transport functions expressed in observed curves, not directly identified land-use zones or passenger purposes. |
| Equity interpretation | The full C3 argument now appears once within the night-function section: extended-hour persistence occurs beyond the most facility-intensive central settings and coincides with higher health deprivation, unemployment and social renting. Less flexible/on-site night work is one plausible mechanism; leisure, interchange and service context remain alternatives. BtC is used as a related all-day precedent rather than a replication. Bus contributes a complementary area-level persistence gradient, not an equivalent deprivation cluster. |
| Area-context interpretation | The former abstract `uneven proxy reach` wording was replaced with a plain title and argument about central and outer London. LNWC and continuous variables have distinct interpretive roles; residence-side indicators may align more closely with outer residential settings and less closely with users of central employment, entertainment and interchange nodes. |
| Planning and limits | 5.5 begins directly with diagnostic planning and equity implications. Repeated three-stage contribution prose was removed. 5.6 retains dataset, typical-day, spatial linkage and cross-mode boundaries but shortens the final recap and connects each boundary to a concrete next analysis. |
| Conclusion | Chapter 6 was rebuilt as four continuous paragraphs: research gap/approach; one integrated answer; methodological, empirical and practical contributions; and concise boundary/future work. It contains no citations, new evidence or objective-by-objective results list. |
| Word-limit control | Before revision, paragraph-only Chapters 1–6 totalled approximately 12,616 words. After revision they total approximately 11,438 words; the conservative count including native Word tables is approximately 11,444. Chapter 5 is approximately 1,586 words and Chapter 6 approximately 326 words, leaving about 550 words below the 12,000-word threshold for later small corrections. |
| Change identification | All 24 non-empty Chapter 5 paragraphs (including six headings) and all four Chapter 6 paragraphs are yellow-highlighted. Pre-existing red/yellow formatting elsewhere remains unchanged. |
| Structural verification | Body paragraphs changed from 388 to 381. Automated checks confirmed all new Chapter 5/6 paragraphs are yellow, Chapter 6 contains no author-year citation pattern, the BtC reference remains once, and no meeting/supervisor attribution appears. |
| Visual QA | LibreOffice 26.2 rendered the final V6 to 73 pages. All 73 pages were rasterised and inspected through contact sheets. The restructured Discussion, Conclusion, shifted references and appendix show no clipping, overlap, broken table/figure, missing glyph or change-induced pagination defect. |
| Reproducibility | Writer: `scripts/restructure_v6_discussion.py`; section audit: `scripts/audit_v6_discussion.py`; word audit: `scripts/count_v6_thesis_words.py`; final V6 SHA-256: `5fc0c95d3499c523eb66130fb8cfe9f398ebf91726b0b7eaee9b95d4a6cc42f5`. |
| Next step | User substantive review of the revised yellow Chapter 5 and Chapter 6. The remaining safe scope is citation/cross-reference, terminology, appendix and final rubric audit; the roughly 550-word margin should be protected unless a concrete argument gap is identified. |

## TM-014 — Guided Chapter 5–6 analytical revision

| Field | Record |
|---|---|
| Status | Complete |
| Source and target | `Main_body_partV6.docx` was edited in place from the TM-013 version. Pre-edit SHA-256: `5fc0c95d3499c523eb66130fb8cfe9f398ebf91726b0b7eaee9b95d4a6cc42f5`. No additional V6 copy was created and Chapters 1–4, figures, tables, equations, references and appendix content were preserved. |
| Revision authority | Applied the user-approved Chapter 5–6 guidance after rereading the current research question/objectives, research gap, research design, actual Chapter 4 results and existing Chapter 5–6. `main.pdf` was used only to calibrate argument-led section function and progression; none of its wording or substantive claims was transferred. |
| Chapter 5 structure | Replaced the TM-013 structure with: `5.1 Synthesis of the principal findings`; `5.2 Explaining the mode-specific structure of night-time transport`; `5.3 Night-time mobility as a differentiated urban rhythm`; `5.4 Night-work and socio-spatial context within the urban night`; `5.5 Implications for night-time transport planning and equity`; `5.6 Limitations and future research`. |
| 5.1 transformation | Gives a direct positive answer through three findings: an internally differentiated dedicated-night geography; differentiated Rail node roles versus a continuous Bus area activity-persistence gradient; and systematic but incomplete correspondence with LNWC and wider context. Cluster detail and extended defence of the night as a separate period were excluded. The section closes with the analytical questions that organise the chapter. |
| 5.2 transformation | Explains Rail first through discrete nodes, entry/exit direction, network hierarchy and activity duration; then explains Bus through dense distributed service, LSOA pooling, hourly resolution and estimated alightings. The possible effect of more local/many-stop Bus travel is retained as an OD- and distance-testable proposition. The synthesis attributes the contrast to the interaction of network geography, journey scale and analytical construction, not to formal cross-mode equivalence. |
| 5.3 transformation | Recasts the temporal curves as differentiated urban rhythms of dispersal, connection, continuation and contraction. Centrality is treated as important but incomplete; Rail interchange and persistent roles plus Bus intermediate positions demonstrate additional organisation. Duration/persistence is identified as the dedicated-night contribution beyond all-day station typologies. |
| 5.4 transformation | Interprets LNWC correspondence as systematic but incomplete and combines the continuous indicators into contextual bundles rather than a variable list. The Rail C3 persistence/deprivation association is developed as an equity-relevant extension beyond an entertainment-centred night, with work-related interpretation presented cautiously alongside mixed urban functions. The dissertation's own central-versus-outer proxy-reach reflection is included once and is not attributed to any meeting. |
| 5.5 transformation | Converts the typology into distinct planning questions concerning operating span and onward connectivity at persistent Rail stations, transfer coordination at interchange stations, the role of persistent Bus areas as later services contract, and the ambiguity of early-declining outer Bus activity. The section defines locations and times for further investigation without claiming unmet demand or service deficiency. |
| 5.6 transformation | Concentrates temporal smoothing, modal measurement/unit differences, spatial contextualisation, classification uncertainty and missing service/passenger evidence in one section. Each boundary leads to a specific future design. Existing stability evidence is reported accurately: Rail mean seed ARI `0.859`, Rail mean bootstrap ARI `0.480`, Bus mean bootstrap ARI `0.785`, and Bus mean minimum-cluster Jaccard `0.316`. |
| Conclusion transformation | Rewritten as five continuous paragraphs: direct RQ answer; separate mode findings; systematic but incomplete context; methodological, empirical and planning contributions; and a concise evidence boundary/future-work close. It contains no author-year citations, new analysis or new substantive claim. The former objective-by-objective and result-list structure was not restored. |
| Language and boundary control | Uses claim–evidence–literature–explanation–implication progression. Repeated negative disclaimers were removed from the analytical sections; one concise area-versus-passenger distinction remains in 5.4 and detailed boundaries are concentrated in 5.6. No new dataset, statistic, cluster, causal mechanism, passenger identity, trip purpose, service-adequacy conclusion or reference was invented. |
| Change identification | All 26 non-empty Chapter 5 paragraphs, including six headings, and all five Chapter 6 paragraphs are yellow-highlighted. Existing red/yellow changes elsewhere remain intact. |
| Word-budget result | Chapter 5 is approximately `1,897` words and Chapter 6 approximately `477` words. Chapters 1–6 total approximately `11,900` words; including native Word tables the conservative count is approximately `11,906`, leaving about `94` words below the 12,000-word threshold. |
| Structural verification | Final DOCX retains 384 body paragraphs, 3 native Word tables, 19 drawings, 19 media files, 40 inline-equation nodes and 12 equation paragraphs. Conclusion citation-pattern check returned none; the BtC reference remains once; no meeting/supervisor attribution appears. |
| Visual QA | LibreOffice 26.2 rendered the revised V6 to 75 pages. Chapter 5–6 pages 56–65, the shifted reference pages and appendix pages were rasterised and inspected. Yellow highlighting is visible and no clipping, overlap, missing glyph, broken figure/table, orphaned heading or change-induced pagination defect was found. QA output: `qa_v6_guided_20260813/Main_body_partV6.pdf`. |
| Reproducibility | Writer: `scripts/revise_v6_discussion_guided.py`; section audit: `scripts/audit_v6_discussion.py`; word audit: `scripts/count_v6_thesis_words.py`; structure audit: `scripts/audit_v6_structure.py`. Final DOCX SHA-256: `573476e6b0cf81de51f25de5f0e016dc46025e6d544321a3eabfbe84057b95d9`; `word/document.xml` SHA-256: `8a9abb51779a3e05d12d7b47763fddf7292a684a1224efbd994b89017163ec83`. |
| Next step | User substantive review of the yellow Chapter 5–6 text. Because the remaining word margin is small, subsequent changes should preferably replace existing wording rather than add new material. |

## TM-015 — Project storyline alignment and cross-window recovery baseline

| Field | Record |
|---|---|
| Status | Complete |
| Scope | Documentation only. No manuscript, analysis, figure, table, label or statistic was changed. |
| Authority | The user requested a persistent Markdown record that allows a new Codex window or another AI system to recover the project's purpose, hidden storyline, agreed interpretive sequence, evidence roles, local reading set and claim boundaries without relying on conversational memory. |
| New baseline | Added `D:\SDS2025_workspace\CASA_FYP\FYP\DISSERTATION_STORYLINE_ALIGNMENT.md` as the project-level narrative and recovery baseline. |
| Central alignment | Locked the sequence: identify night-time transport rhythms → examine correspondence with night-work and neighbourhood context → interpret the combined evidence as candidate urban functions → derive bounded implications for night-time travel and planning. |
| Evidence mapping | Recorded the current 403-station Rail K=5/diagonal and 3,383-LSOA Bus K=4/full specifications; behavioural-descriptor effect sizes; LNWC samples and Cramér's V; the formal 20-variable role; candidate Rail functions; the Bus activity-persistence interpretation; and the distinction between credibility checks and substantive evidence. |
| Boundary control | Recorded the inference ladder from observed aggregate use to planning questions and prohibited unsupported jumps to passenger identity, causality, exact land use, unmet demand, accessibility outcomes or service deficiency. |
| Recovery sources | Indexed current authoritative outputs, user-authored early reasoning drafts, Results drafts, Project21, four meeting records, structural exemplars and legacy technical files. Historical sources are explicitly marked as idea/rationale recovery material rather than current numerical or academic authority. |
| Discovery improvement | Added a prominent pointer at the top of `PROJECT_CONTEXT.md`, whose older analytical samples and decisions are superseded, so future assistants encounter the current storyline baseline before using the legacy coding context. |
| Next step | Use the baseline to build a paragraph-level Chapter 5 argument map, then revise 5.1–5.5 and Chapter 6 without changing the adopted RQ/Objectives or importing unauthorised side analyses. |

## TM-016 — Linked Results–Discussion narrative recovery

| Field | Record |
|---|---|
| Status | Complete — 2026-08-14. |
| Scope and authority | Implements the story-alignment baseline after the user approved a linked revision of Results 4.2.1–4.3.2 and Chapters 5–6. The adopted RQ/Objectives, current analytical specification, labels, figures, tables and formal outputs remain fixed. No side analysis is added. |
| Central change | Results will move from cluster-legitimacy phrasing (difference from adjacent cluster, therefore a valid type) to evidence-bounded observed-pattern phrasing (night-time transport pattern, supported by temporal/directional/spatial evidence). Discussion will then interpret those already-described patterns thematically: rhythms; night-work/neighbourhood correspondence; candidate functions and scale; diagnostic planning questions; limits. |
| Evidence lock | Exact results remain traceable to `final_figures/Table_4_1_cluster_solution.csv`, `Table_4_2_behavioural_descriptor_tests.csv`, `Table_4_3_lnwc_association.csv`, `rq2_independent_variables/outputs/report/RESULTS.md`, and `rq2_new_clusters_analysis/outputs/report/CONTEXT_METRICS.md`. Historical drafts may supply narrative voice only, never current values. |

### Paragraph-level Results–Discussion argument map

| Current paragraphs | Action | Current role/problem | Target role and evidence |
|---|---|---|---|
| 208–210 Rail C1 | Rewrite | Concludes that differences define a valid type | Describe observed central evening departure-oriented station activity; support with temporal profile, direction balance, map and current descriptors. |
| 211–213 Rail C0 | Rewrite | Defined chiefly as contrast to C1 | Describe outer arrival-oriented evening receipt pattern; retain peripheral/directional evidence, with comparison secondary. |
| 214–216 Rail C4 | Rewrite | Primarily an in-between contrast | Describe broad inner–middle mixed/arrival-oriented pattern, retaining its less sharply specialised role. |
| 217–219 Rail C3 | Retain and tighten | Already foregrounds late persistence but ends as taxonomic distinction | Describe extended-duration activity and Friday/Saturday persistence; leave contextual interpretation to 4.3/5.3. |
| 220–222 Rail C2 | Rewrite | Defined by contrast to C1/C3 | Describe observed balanced interchange/connective role; use high activity and near-balanced direction as support. |
| 223–225 Rail overall | Merge/tighten | Repeats cluster inventory | One short bridge from Rail patterns to contextual correspondence. |
| 232–248 Bus overview/C1–C0 | Rewrite and compress | Gradient is identified, but middle groups are chiefly relative positions | Describe an area-level activity-persistence regime: central/inner high-persistent endpoint, outer early-declining endpoint, and overlapping intermediate observed profiles. Retain estimated-alighting qualifier where direction is mentioned. |
| 249–251 contrasting dimensions | Retain and move detail | Useful modal bridge, but scale mechanism is repeated in Discussion | Keep concise Results-level unit distinction; reserve extended scale interpretation for 5.4. |
| 256–276 current 4.3.1 | Retain and refine | Formal LNWC association/enrichment is present, but cluster settings can be narrated more consistently | Results reports the mode-specific association and cluster-level night-work settings, with enrichment as support and no passenger/workplace inference. |
| 304 Chapter 5 Chinese bridge | Delete | Temporary working prose; introduces unsupported accessibility wording | Begin 5.1 directly. |
| 306–307 current 5.1 | Retain/rewrite | Direct answer is useful; asks how structures are produced | State direct answer and the progression from rhythms to context, candidate function and planning question; remove causal-production wording. |
| 309–312 current 5.2 | Split/move | Rail-then-Bus explanation repeats Results and foregrounds mechanism | Place observed rhythms in thematic 5.2; move unit, temporal aggregation and scale reflection to 5.4. |
| 314–316 current 5.3 | Split/merge | Useful rhythm/function material overlaps with 5.2 | Use direction/node role, persistence and centre–outer participation as three cross-mode 5.2 themes; use candidate-function synthesis in 5.4. |
| 278–295 current 4.3.2 | Rewrite and expand selectively | Effect-size and profile logic is present, but C4 and several cluster-level portraits are underdeveloped | Results carries the two-layer context evidence: mode-level epsilon-squared ranking plus flexible, cluster-level 20-variable background portraits. Do not turn it into an unstructured variable list. |
| 318–321 current 5.4 | Move and rewrite | Correct context material, but follows rather than structures the target arc | Become 5.3: interpret what the Results-level LNWC and context correspondence changes in the urban-night reading; do not repeat rankings, z-scores or full portraits. Retain the area-not-passenger and uneven-proxy-reach boundary once. |
| 323–324 current 5.5 | Retain/tighten | Already diagnostic but duplicates C3 framing | Keep as 5.5, add the transport-derived-signature methodological contribution, and formulate service questions rather than service conclusions. |
| 326–330 current 5.6 | Retain | Concentrated limits/future work | Preserve with only overlap removal; exact stability values remain formal-output verified. |
| 332–336 Chapter 6 | Rewrite after Chapter 5 | Repeats some Results and calls context an explanation | Give one integrated answer, separate mode findings, contextual correspondence, contribution and concise boundary; no new evidence/citations. |

| Target Chapter 5 sequence | 5.1 principal answer and progression; 5.2 thematic cross-mode night-time rhythms (direction/node role; persistence/day type; spatial participation); 5.3 night-work and neighbourhood correspondence; 5.4 candidate functions across modes and scales; 5.5 diagnostic planning/equity implications; 5.6 limitations and future research. |
| Language rule | Use the full 20-variable set flexibly for cluster-level portraits, while effect-size rankings answer a distinct mode-level question. State inference limits proportionately and concentrate detailed boundaries in 5.6; do not append defensive disclaimers mechanically. |
| Implemented Results changes | Rewrote 4.2.1 and 4.2.2 as observed-pattern accounts: Rail is described through central departure-oriented activity, outer arrival orientation, inner–middle mixed activity, late persistence and balanced interchange; Bus through an area-level activity–persistence regime. Cluster contrasts remain supporting evidence rather than the main rhetorical conclusion. Section 4.3.1 retains the formal LNWC association/settings; 4.3.2 now explicitly separates mode-level epsilon-squared differentiation from flexible, cluster-level 20-variable background portraits, including C0's relatively less economically pressured, family-oriented outer-suburban context and the less sharply differentiated C4 context. |
| Implemented Discussion/Conclusion changes | Rebuilt 5.1–5.5 around the approved sequence. Section 5.2 is organised by direction/node role, persistence/day type and spatial participation, pairing Rail and Bus descriptively within each theme; it expressly avoids formal cross-mode significance claims. Section 5.3 interprets Results-level context without reproducing rankings or portraits; 5.4 frames candidate functions and scale; 5.5 turns the typology into diagnostic planning questions without asserting service inadequacy. Chapter 6 gives the integrated answer and contribution without new evidence or citations. Existing 5.6 limitations text was retained. |
| Boundary control | No passenger-purpose, identity, occupation, income, causal, land-use-certification, unmet-need or service-deficiency claim was added. The former passenger-purpose formulation for central departure activity was not used. C3 is framed as extended-duration activity in a deprivation-related area context, with less flexible/on-site night work one possibility alongside leisure, interchange and local-service alternatives. |
| Change identification | The current TM-016 wording is blue font (`0000FF`) for readability; 70 changed text runs are blue. Pre-existing red text and yellow-highlighted prior revisions were retained. One Chinese temporary Chapter 5 bridge was removed from the primary manuscript. |
| Archive | Reconstructed `Main_body_partV6_pre_TM016_review_notes_reconstructed.docx` with the eight prior Chinese temporary review notes restored at their original locations. It preserves the notes for review but is not a byte-identical pre-TM-016 English-text snapshot: it contains the current revised English prose. |
| Structural and visual verification | Primary manuscript: 384 body paragraphs, 3 native Word tables, 19 drawings, 19 media files, 40 inline-equation nodes and 12 equation paragraphs. No Chinese temporary notes remain in the primary body. LibreOffice rendered the revised manuscript to 72 pages; all pages were rasterised and checked, with no clipping, overlap, missing glyphs, broken figures/tables or pagination defect. Blue text remains legible, and prior yellow/red revision marking is intact. |
| Reproducibility | Writer: `scripts/apply_tm016_linked_narrative_revision.py`; blue-font conversion: `scripts/convert_tm016_blue_highlight_to_font.py`; archive-note reconstruction: `scripts/rebuild_pre_tm016_review_notes_archive.py`; visual rendering/rasterisation: `scripts/render_docx_tm016.py`, `scripts/rasterize_tm016_pdf.py`. Final DOCX SHA-256: `377ced813a11b3429b49e7e1f9e6d239a459ade94e83ccc9aec59af60d30da3b`. |
| Deferred scope | The reported Bus–Rail co-location output remains a separate, controlled next-scope candidate (TM-017) rather than being introduced into this linked writing revision. |

## TM-017 — Evidence-led Results, Discussion and Conclusion reconstruction

| Field | Record |
|---|---|
| Status | Complete — 2026-08-14. |
| Scope and authority | Reconstructed Results 4.2.1, 4.2.2, 4.3.1 and 4.3.2; Discussion 5.1–5.6; and Chapter 6 in the primary `Main_body_partV6.docx`. No additional manuscript version was created. TM-016's six-part Discussion architecture and its Results/Discussion division of labour were retained. Chapters 2–3, the adopted RQ/Objectives, clustering specifications and formal labels were not changed. |
| Evidence lock | Rail remains 403 stations, diagonal GMM K=5; Bus remains 3,383 fitted LSOAs, full GMM K=4, threshold 33 and 18:00–05:00. Rail LNWC uses n=387 and the full equal-station catchment composition from `rq2_new_clusters_analysis/outputs/data/rail_enrichment.csv`; headline ratios remain C1–LNWC1=3.98 and C0–LNWC7=3.06. The separate `outputs_800m` enrichment variant was audited and excluded from the manuscript. |
| Results reconstruction | Rewrote the specified Results paragraphs as observable urban geographies and temporal rhythms. Rail is narrated through central departure, outer arrival, inner–middle participation, late persistence and balanced connection; Bus through a graded activity–persistence geography. Section 4.3 retains exact LNWC association/enrichment evidence and distinguishes mode-level effect-size rankings from cluster-level 20-variable portraits. |
| Required evidence gaps closed | Added the younger-age dimension for central Rail C1 (`age_20_34_share` z=+1.00); separated Rail's two socio-economic stories (C3 deprivation/persistence versus C0 family/higher-car/lower-deprivation context); contrasted these with Bus C1's bundled centrality–housing–facility–deprivation gradient; and treated no-car prevalence separately because it peaks around central Rail C1 while the strongest deprivation bundle surrounds C3. |
| Discussion reconstruction | Rebuilt every Discussion paragraph from the locked evidence and the approved hidden storyline: rhythms → external context → candidate urban functions → planning/equity implications → limits. Section 5.2 is organised by direction, duration/day type and scale; 5.3 interprets night-work and neighbourhood correspondence; 5.4 combines candidate functions, analytical scale and the new Bus–Rail relationship; 5.5 translates the typology into targeted planning questions; 5.6 concentrates temporal, modal, spatial, classification and service-evidence boundaries. |
| Literature integration | Restored literature dialogue using only references already present in V6. Chapter 5 contains 25 author–year citation groups: 5.1=2, 5.2=6, 5.3=5, 5.4=5, 5.5=3 and 5.6=4. A final reference-list audit corrected two draft citations to the existing single-author form `Cats (2024)`. Chapter 6 contains no citation pattern or new reference. |
| Bus–Rail correspondence | Introduced the current-label Test A2 headline in 5.4: within 400 m of a Rail station, 54.3% of fitted Bus LSOAs are stronger-persistence C1 versus the 33.5% baseline (1.6×), with enrichment retained in inner, middle and outer centrality rings. Appendix A3 carries the method, all distance-band shares, ring-stratified results, Test B (n=1,757; Cramer's V=0.158; 9,999-permutation p=0.0001; 1,200 m V=0.154), a Test A2 figure and a 403-station overlay. C3 display text is aligned to V6 as `moderate activity with alighting-oriented estimated activity`; no label or numerical result was changed. |
| Claim boundary | Bus–Rail evidence is described as spatial correspondence and overlapping night-active geography. It does not establish passenger transfers, feeder behaviour or corridor effects. Rail C3 is interpreted as consistent with possible constrained/on-site night work alongside leisure, local-service and network explanations; no passenger occupation, income, causal deprivation effect, service gap or accessibility outcome is asserted. |
| Conclusion reconstruction | Rewritten as four continuous paragraphs: research answer; integrated Rail/Bus/context synthesis; methodological, empirical and planning contributions; concise boundary and future validation. It contains no objective-by-objective list, new material or references. |
| Language regression check | Removed all occurrences of the targeted self-referential phrases (`rather than the purpose of`, `is supporting evidence rather than`, `these observations show/locate/provide`), plus `C# captures` and `The profile shows`. Detailed caveats are concentrated in 5.6 and the appendix; interpretive caution in 5.2–5.5 is integrated with evidence and literature. |
| Word-limit result | Paragraph-based main-text count before References is 11,228 words. Adding all words in the three native main-text tables gives a conservative count of 11,426, remaining below the 12,000-word maximum. Appendix tables are excluded from this conservative main-text count. |
| Change identification | All newly reconstructed prose and Appendix A3 content use dark-green font (`006600`), producing 80 green runs. Existing red text, yellow highlights and TM-016 blue text were preserved. The two pagination-only adjustments changed no wording: `Bus clusters and LNWC` now begins with Figure 4.7, and the 4.3.2 introduction is kept together. |
| Structural verification | Final DOCX contains 397 body paragraphs, 5 native Word tables and 21 inline shapes. Appendix A3 appears once. The final citation-name audit has zero `Cats and Ferranti, 2024` strings; Conclusion has zero author–year citation patterns; the targeted self-referential phrase count is zero. |
| Visual QA | LibreOffice 26.2 rendered the final manuscript to 76 pages. All pages were rasterised with PDFium and inspected through numbered contact sheets; the revised Results, Discussion, Conclusion and Appendix A3 pages were additionally inspected at full-page resolution. No clipping, overlap, missing glyph, broken figure/table, table overflow or orphaned heading remains. Final QA PDF: `qa_tm017_final/Main_body_partV6.pdf`. |
| Reproducibility | Primary writer: `scripts/rewrite_tm017_evidence_led.py`; appendix figures: `scripts/build_tm017_bus_rail_appendix_figures.py`; citation alignment: `scripts/fix_tm017_citation_names.py`; pagination: `scripts/fix_tm017_pagination.py`; final audit: `scripts/audit_tm017_final.py`; rasterisation: `scripts/rasterize_tm017_pdf.py`. Text audit: `final_figures/TM017_TEXT_QA.md`. Final DOCX SHA-256: `6a273cc974c88455674f21b7bca3cd972d71c59bd5c8bacfa46dbf98699d2c56`. |
| Next step | User substantive review of the dark-green TM-017 text. Future edits should preserve the 11,426-word conservative budget, the citation density, the Results/Discussion functional split and the inference ladder recorded here. |

## TM-018 — V7 Discussion evidence–literature matrix and RQ callback plan

| Field | Record |
|---|---|
| Status | Planning evidence complete; manuscript drafting not yet started. |
| Current manuscript authority | `main_body_V7_backup2 .docx`, last modified 2026-08-15 17:59:14, size 3,639,784 bytes. The file was open during review, so a hash could not be obtained without interrupting the user's editing session. |
| User decision superseding earlier records | Retain the current V7 Main RQ, RQ1 and RQ2 framing as the formal narrative anchor. Do not restore the earlier Main RQ + Objectives 1–3 formulation. |
| Unified Rail contextual sample | LNWC and the 20 continuous contextual variables use the same catchment eligibility rule and the same 389/403 Rail-station sample. Current categorical LNWC summary: Rail Cramér's V=0.408, n=389; Bus V=0.253, n=3,383. Older 387/389 split-sample records are superseded for the V7 narrative. |
| Scope | Build the evidence and literature basis for Chapters 5–6 only. No new empirical analysis, no service-mismatch test, and no manuscript wording change in this entry. |
| Local literature verification | Twelve core items were found in Zotero and checked against locally indexed PDF full text. Zotero writes were not performed. Item and attachment keys are recorded below. |

### RQ callback decision

| Location | Function | Decision |
|---|---|---|
| Results 4.4 | Empirical closure | Retain the current concise synthesis, but in the later writing pass make the relationship explicit with one RQ1 sentence and one RQ2 sentence. Do not add literature, mechanisms or planning implications here. |
| Discussion 5.1 opening | Interpretive answer | State the thesis-level answer to the Main RQ: night-time use is heterogeneous, mode-specific and embedded in differentiated night-work and socio-spatial contexts. Do not repeat the full cluster inventory. |
| Chapter 6 | Final closure | Answer RQ1 and RQ2 directly in separate consecutive paragraphs, followed by contribution and one concise future direction. No new results or citations. |
| Repetition rule | Division of labour | Results answers **what was found**; Discussion answers **what it means and how it changes the literature**; Conclusion states **the final answer and contribution**. |

### Discussion evidence–literature matrix

| ID / target | Discussion claim | Current V7 internal evidence | Prior-chapter anchor | Locally verified Zotero literature and relationship | Drafting boundary |
|---|---|---|---|---|---|
| D01 / 5.1 | The 18:00–05:00 period is internally differentiated rather than a homogeneous off-peak block. | Figs 4.2.1.1 and 4.2.2.1; Rail timing/direction/day-type differences; Bus persistence gradient; 4.4 paras 313–318. | 2.1 paras 23–25; 2.2 paras 32–34; 2.4 paras 49–51. | Schwanen et al. (2012), `QNYLLKSE` / PDF `HXMWGLL3`: **supports** a rhythmic, spatiotemporal reading of the night. Van Liempt et al. (2015), `I4Y6JSDZ` / `9S3854YQ`: **supports** treating the urban night as a distinct space-time. V7 **extends** these arguments with transport-use evidence. | Do not infer the activities or people responsible for each rhythm. |
| D02 / 5.1 | Late-night persistence is an organising dimension in its own right, not simply a by-product of the highest activity volume or centrality. | Rail C3, paras 221–224, remains later on Friday/Saturday; C1 has highest volume but more limited post-23:00 share, paras 208–211. | 2.1 para 25; 2.2 paras 32–34. | Schwanen et al. (2012): **supports** attention to changing rhythms through the night. Briand et al. (2016), `BT49VPYL` / `5UB66ET5`: **methodological support**, showing temporal clustering can identify subtle nightlife activity. V7 **extends** this to a distinct station-level persistence geography. | C3 is not equivalent to night workers, nightlife users or one land use. |
| D03 / 5.1 | Weekday–weekend variation changes how station roles are expressed during the night. | C0 Friday/Saturday directional shift, paras 212–215; C3 stronger Friday/Saturday persistence, paras 221–224. | 2.1 para 25; 2.3 paras 39–43. | Cheng et al. (2024), `M728A4SY` / `3NK63IUZ`: **supports** examining intra-day and intra-week variation at London stations. V7 **extends** this into a dedicated night window and links it to direction and persistence. | Use representative day-type language; do not generalise to every Friday or event night. |
| D04 / 5.2 | Rail reveals differentiated node roles through the combination of direction, scale, centrality and duration. | C1 central/departure, C0 outer/arrival, C2 balanced hub, C3 persistence and C4 inner–middle continuation, paras 208–233 and Figs 4.2.1.1–4.2.1.3. | 2.3 paras 40–42; 2.4 paras 49–51. | Gan et al. (2020), `49YA8VDY` / `2H5J2NVJ`: **supports** linking station ridership rhythms to node/place and urban-function differences. Cheng et al. (2024): **supports** station classification using intra-week entry/exit profiles. V7 **extends** both through a night-specific London typology. | Functions remain evidence-bounded interpretations, not verified land uses or trip purposes. |
| D05 / 5.2 | Bus is better interpreted as an activity–persistence continuum with two clear endpoints and overlapping intermediate positions. | Bus paras 235–263; C1/C0 endpoints; C2/C3 spatial and temporal overlap; Figs 4.2.2.1–4.2.2.3. | 2.3 paras 40–44; 2.4 para 50. | Briand et al. (2016): **supports** extracting interpretable temporal profiles. Cheng et al. (2024): fuzzy memberships **qualify** hard cluster boundaries by showing that transport profiles can occupy mixed positions. V7 adds a night-specific Bus-area case in which overlap is substantively meaningful. | Do not describe C2/C3 overlap as clustering failure or as proof of natural categories. |
| D06 / 5.2 | Rail and Bus expose different organising logics: discrete node roles versus graded area-level participation. | Rail/Bus comparison in paras 196–198, 231–263 and 4.4 paras 313–315. | Explicit cross-mode gap in 2.4 para 50. | Gan et al. (2020) and Cheng et al. (2024) provide the station-profile baseline; Briand et al. (2016) provides temporal-mixture positioning. V7 **extends** this literature through a night-specific, mode-separated comparison. | Comparison is descriptive; spatial unit, resolution and direction construction differ. |
| D07 / 5.3 Story A | Central night-time activity environments combine intensive transport activity with younger, private-rented, amenity-rich and low-car area contexts. | Rail C1 LNWC 1 enrichment and context paras 275–278, 297–299; Bus C1 paras 307–310. | 2.3 paras 42–43; 2.4 para 51. | Mavrogeni et al. (2025), `ECQGKQZM` / `LG96SGKI`: **contextualises** central and peripheral London night-work geographies using an independent classification. Gan et al. (2020): **supports** reading temporal profiles alongside station environments. V7 adds night-specific Rail/Bus evidence. | Describe catchment/LSOA environments, not young renters or night workers as passengers. |
| D08 / 5.3 Story B | Night-time mobility re-expresses London's centre–periphery geography through an outer, earlier-declining and more family/car-oriented context. | Rail C0 paras 212–215, 280, 300; Bus C0 paras 257–259, 288–289, 309. | 2.1 para 25; 2.3 paras 42–43. | Gan et al. (2020): residential-oriented station rhythms **support** the broader node/place interpretation. Mavrogeni et al. (2025): **contextualises** peripheral night-work types. V7 **extends** these into outer night-time receiving and early-decline rhythms. | Do not identify passengers as local residents or attribute low use to one cause. |
| D09 / 5.3 Story C | Extended activity is not synonymous with the most central, amenity-intensive nightlife context. | Rail C3 late persistence, paras 221–224; LNWC 2/3 association, para 283; elevated health deprivation, social renting, unemployment, age 20–34 and accommodation/food employment, para 302. | 2.1 paras 24–25; 2.2 paras 29–34; 2.3 para 43. | Shaw (2014), `D2PACS5I` / `VB7S82QJ`: **qualifies** a narrow night-time-economy reading by treating the urban night as more than consumption venues. McArthur et al. (2019), `3VJGK3P9` / `3CZWH7UV`, and Palm et al. (2023), `YI7FCEZB` / `MHZF7BRW`: night-work and shift-commuting evidence **supports the relevance** of constrained and differentiated night mobility. V7 **complicates** a centre/nightlife-only account. | Present night work as one plausible contextual interpretation alongside leisure, interchange and local services; never assign C3 passengers an occupation. |
| D10 / 5.3 | No-car prevalence is not a one-dimensional proxy for disadvantage in London. | No-car peaks around central Rail C1, whereas the strongest deprivation bundle surrounds C3, paras 299, 302–303. | 2.2 paras 30–31; 2.3 paras 42–43. | McArthur et al. (2019) and Smeds et al. (2020), `GNM5FFSC` / `BYASWYDU`: **qualify** single-variable accounts by foregrounding socio-spatial and temporal difference. Palm et al. (2023): **supports** the importance of transport resources in shift mobility while not making car ownership a universal deprivation measure. | Interpret variables as a bundle; do not turn no-car or deprivation into a causal explanation of activity. |
| D11 / 5.3 | Bus context forms a more bundled centre-to-periphery gradient than the differentiated Rail context. | Bus C1/C0 contextual opposites and intermediate C2/C3, paras 288–310; Rail has separate C1, C0 and C3 stories, paras 297–303. | 2.3 paras 42–44; 2.4 para 50. | Mavrogeni et al. (2025): **contextual baseline** for London's night-work geography. Gan et al. (2020): **supports** environment-profile linkage. V7 **adds a mode-specific qualification**: contextual differentiation changes with transport mode and analytical scale. | Avoid ranking one mode as socially more important; LSOA aggregation bundles several stops and land uses. |
| D12 / 5.3 synthesis | Sequential clustering followed by external contextualisation supports candidate urban-night functions without allowing context to define the clusters. | Research sequence in 1.2 paras 15–16; Methods post-clustering design; combined 4.2 and 4.3 evidence; 4.4 para 318. | 2.3 paras 41–44; 2.4 paras 49–51. | Gan et al. (2020): **methodological positioning** for linking profiles and urban environments. Mavrogeni et al. (2025): supplies the independently constructed night-work geography. V7 **extends** this sequence to night-specific Rail and Bus types. | Use “candidate function”, “consistent with” and “suggests”; no validation claim. |
| D13 / 5.4 | Night-specific planning and accessibility analysis should recognise temporal differentiation within the night rather than use one aggregate off-peak category. | Distinct timing, persistence and day-type evidence across 4.2; C3 versus C0/C1; Bus C1 versus C0. | 2.2 paras 30–34; 2.4 para 50. | Ryan et al. (2023), `CWEC49SQ` / `35C5S7ST`: **supports** treating accessibility as time-dependent and group-differentiated. McArthur et al. (2019): **supports** the relevance of socio-spatial and temporal equity to London's night transport. V7 **provides a diagnostic empirical layer**, not an accessibility outcome. | Say “can inform” or “provides a basis”; do not claim service mismatch or inadequate provision. |
| D14 / 5.4 | Mode-specific interpretation is necessary because one analytical vocabulary does not describe Rail and Bus equally well. | Rail differentiated node roles versus Bus continuum; separate models, units and descriptor structures. | Cross-mode research gap in 2.4 para 50; mode-separated design in 1.2 para 15. | Briand et al. (2016), Gan et al. (2020) and Cheng et al. (2024): **methodological baseline** for temporal profiling. V7 **extends and qualifies** it by showing that interpretability depends on mode and analytical unit. | Do not present K=5 versus K=4 as a formal test that Rail is inherently more complex. |
| D15 / 5.4 | Equity relevance is strongest as a targeted diagnostic where extended activity and disadvantage coincide, not as a city-wide finding of transport injustice. | Rail C3 temporal/context combination; Bus bundled gradient; no service-side evidence in Results. | 2.2 paras 30–31; 2.3 para 43. | McArthur et al. (2019), Smeds et al. (2020), Palm et al. (2023), and Plyushteva & Boussauw (2020), `2HNTFT8T` / `UIJ7PNNW`: **support the relevance** of temporal conditions, difference and inclusion to night mobility. V7 identifies where these questions merit examination. | No claim of unequal outcomes, underserved areas, causation or passenger identity. |
| D16 / 5.5 | The principal contrasts are informative, but representative-day data, scale differences and hard cluster labels bound how finely the typologies should be interpreted. | Typical-day construction in Methods; Rail/Bus resolution and unit differences; Bus C2/C3 overlap; model-stability evidence in 4.1. | 2.3 paras 39–41; 2.4 para 50. | Cheng et al. (2024): fuzzy membership **qualifies** hard typologies and supports treating mixed stations/areas carefully. Manley et al. (2018), Zotero item `4HMFWLIG`, provides the existing Literature Review basis for temporal regularity; full-text recheck remains optional before drafting 5.5. | Concentrate this discussion in 5.5; do not repeat the same caveat after every substantive paragraph. |

### Zotero verification register

| Subsection | Verified local items | Intended role |
|---|---|---|
| 5.1 | Schwanen et al. 2012 (`QNYLLKSE`); Van Liempt et al. 2015 (`I4Y6JSDZ`); Shaw 2014 (`D2PACS5I`) | Distinct space-time, rhythmic inequality and a broader urban-night framing. |
| 5.2 | Briand et al. 2016 (`BT49VPYL`); Gan et al. 2020 (`49YA8VDY`); Cheng et al. 2024 (`M728A4SY`) | Temporal clustering, node/place interpretation, intra-week variation and mixed memberships. |
| 5.3 | Mavrogeni et al. 2025 (`ECQGKQZM`); McArthur et al. 2019 (`3VJGK3P9`); Smeds et al. 2020 (`GNM5FFSC`); Palm et al. 2023 (`YI7FCEZB`) | Independent night-work geography, differentiated mobility, temporal equity and shift commuting. |
| 5.4 | Ryan et al. 2023 (`CWEC49SQ`); Plyushteva & Boussauw 2020 (`2HNTFT8T`); McArthur/Smeds/Palm items above | Time-dependent accessibility, inclusive night mobility and diagnostic planning/equity relevance. |
| 5.5 | Cheng et al. 2024 (`M728A4SY`); Manley et al. 2018 (`4HMFWLIG`, metadata verified; optional full-text recheck before prose) | Mixed membership, temporal regularity and limits of hard typologies. |

### Drafting gates after matrix review

1. Confirm that D01–D16 represent the intended Discussion claims and that D09/D15 remain within the desired interpretive boundary.
2. Revise Results 4.4 only enough to make RQ1/RQ2 closure explicit; do not add literature or mechanisms.
3. Draft 5.1, audit it against D01–D03, and obtain user review before moving to 5.2.
4. Draft 5.2 against D04–D06, then 5.3 against D07–D12; use the matrix to prevent 5.3 from becoming Results 2.0.
5. Draft 5.4 and 5.5 only after the empirical interpretation is stable; write Chapter 6 last.

## TM-019 — Discussion and Conclusion structural consolidation (V2)

| Field | Record |
|---|---|
| User instruction | Treat the principal defect as content-level repetition and loss of emphasis caused by sections being drafted independently. Preserve the source document and generate a separate V2 file. |
| Source preservation | `讨论总结部分整理.docx` was read only and retained at its original size (27,701 bytes) and last-modified time (2026-08-15 19:14:25). It remained open during final checks, so no source hash was forced. |
| Output | `讨论总结部分整理V2.docx`; SHA-256 `A7EBF3E06C6E6439EF6C85DEB5A6413D9E292F72B98A964DF98511589DF430BC`. |
| Paragraph ownership | 5.1 now owns the dedicated-night argument; 5.2 owns the Rail node-role versus Bus persistence-continuum explanation; 5.3 owns the three socio-spatial stories and contextual synthesis; 5.4 owns planning/research implications; 5.5 owns limitations and future research; Chapter 6 alone provides final RQ1/RQ2 closure. |
| Principal transformations | Removed repeated full cluster inventories and repeated transitions; retained C3 only where it serves three distinct roles (temporal organising dimension, socio-spatial qualification, targeted planning diagnostic); merged the no-car interpretation into one multidimensional paragraph; separated passenger/trip-purpose limits from service/accessibility limits; reordered the Conclusion so empirical and methodological contributions precede future work. |
| Length and structure | Source: 42 non-empty paragraphs and approximately 4,168 words. V2: 40 non-empty paragraphs and approximately 2,757 words. The reduction is approximately 33.9%, with interpretive depth restored after an over-compressed intermediate draft. |
| Repetition audit | No paragraph pairs exceeded the similarity threshold. Theme counts changed from source to V2: central/outer `63 -> 43`; persistence/duration `46 -> 27`; context-boundary language `31 -> 19`; mode-difference references `23 -> 20` (retained where required for section and RQ closure). |
| Evidence and citations | No new empirical analysis or literature was introduced. The prose uses only the D01–D16 evidence–literature register already verified in TM-018. Chapter 6 contains no citations or new results. |
| Visible change convention | Reconstructed body prose uses dark green `006600`; chapter and subsection headings retain standard heading styling. The source document contains no pre-existing colour/highlight runs that required preservation. |
| Structural QA | V2 contains no tables, images, placeholders, internal claim/evidence tokens or Codex markers. Heading levels were normalised to Heading 1 for chapters and Heading 2 for subsections. |
| Visual QA | LibreOffice 26.2 rendered V2 to an eight-page PDF. Because Poppler was unavailable to the packaged raster step, the emitted PDF was rasterised locally with PDFium. The contact sheet and all eight original-resolution page images were inspected; no clipping, overlap, missing glyph, broken heading, or orphaned subsection was found. |
| Next decision | User review should focus on whether the revised hierarchy now gives sufficient prominence to: (1) persistence as a night-specific dimension; (2) the mode-specific organising logics; and (3) the C3 qualification to a centre/nightlife-only interpretation. After approval, integrate the accepted prose into the authoritative V7 manuscript rather than creating another discussion-only version. |

## TM-020 — Discussion and Conclusion argumentative refinement (V3)

| Field | Record |
|---|---|
| Status | Complete — 2026-08-15. |
| User instruction | Preserve V2 and create an independent V3. Improve connective expression, remove Results repetition, make 5.3 more concrete and literature-responsive, reduce the length and citation-padding risk in 5.4–5.5, and strengthen Chapter 6. Use the two supplied dissertations only as examples of argumentative organisation and expression. |
| Source and output | Source: `讨论总结部分整理V2.docx` (read-only during this revision). Output: `讨论总结部分整理V3.docx`; SHA-256 `A5B5503801CF9D599FDC487318C938A18205CDE0525FD9F3418F9205638A1AB6`. |
| Reference-paper use | `main.pdf` informed the disciplined separation of Results and Discussion, the use of a thesis-level interpretive claim, and the progression from RQ answer to qualification and contribution. `24114779_MSc_Dissertation.pdf` informed the value of concrete spatial-function narration. Its stronger passenger-purpose, inequality and service claims were not adopted. No wording, results or substantive conclusions were copied from either sample. |
| 5.1 transformation | Replaced the opening Results inventory with one interpretive proposition: the night contains concurrent rhythms rather than one off-peak condition. Duration and day type each perform a distinct argumentative role, followed by a bridge into modal organisation. |
| 5.2 transformation | Consolidated Rail as differentiated directional node roles and Bus as graded area participation. Removed the extra volume and intermediate-cluster restatements. The final paragraph now treats network form and analytical unit as an explicit qualification and transition into context. |
| 5.3 transformation | Rebuilt the section around three concrete settings and a synthesis. Centrality is operationalised through the observed co-location of activity intensity, facilities, area composition, car access and LNWC context rather than invoked as an abstract cause. Gan et al. and Mavrogeni et al. are used to establish the profile–environment and night-work dialogue; Rail C3 then qualifies a centre/nightlife-only account through Shaw and night/shift-mobility literature. Vehicle ownership is retained once as a bundled-context example. |
| 5.4 transformation | Reduced four paragraphs to three. The section now owns only: time-sensitive diagnosis, mode-specific planning questions, and the transferable research sequence. It no longer repeats the full temporal, modal and contextual findings or presents a literature list detached from a claim. |
| 5.5 transformation | Reduced five paragraphs to four organised limitations: temporal representation; spatial/modal comparability; area context and missing journey purpose; hard cluster boundaries. Each limitation is paired directly with a future test, avoiding a second independent future-research inventory. |
| Chapter 6 transformation | Replaced the methodological opening with the central substantive conclusion. RQ1 and RQ2 are answered in consecutive paragraphs and then integrated into empirical, conceptual and methodological contributions. No citations or new empirical results were added. |
| Paragraph map | 5.1: merge/rewrite V2 P002–P006; 5.2: merge/rewrite P008–P013; 5.3: rewrite P015–P022 around central, outer and C3 stories; 5.4: merge P024–P028 into three purpose-led paragraphs; 5.5: merge P030–P034 into four limitation–test pairs; Chapter 6: rewrite P036–P039 as conclusion, RQ1, RQ2 and contribution. |
| Length and repetition | V2 contained 40 non-empty paragraphs and approximately 2,757 words. V3 contains 32 non-empty paragraphs and approximately 2,302 words. No paragraph pair exceeded the audit similarity threshold. Theme mentions declined from V2 to V3: central/outer `43 -> 36`, persistence `27 -> 21`, mode-difference `20 -> 15`, off-peak `7 -> 6`, and diagnostic phrasing `5 -> 1`. The reduction was achieved through content consolidation rather than telegraphic rewriting. |
| Evidence boundary | Rail and Bus remain separate and are synthesised descriptively. The contextual layer concerns catchments/LSOAs and is not used to assign passenger identity, trip purpose or causal mechanism. Detailed limitations are concentrated in 5.5; only interpretation-specific qualifications remain in 5.2–5.4. |
| Visible-change convention | All V3 body paragraphs use dark-blue font `1F4E79`; chapter and subsection headings retain their standard styles. This distinguishes V3 rewriting from V2's dark-green body text without tracked-change markup. |
| Structural and visual QA | Final V3: 32 non-empty paragraphs, 0 tables, 0 inline shapes and 0 detected placeholder/internal citation tokens. LibreOffice 26.2 rendered the file to seven pages; all pages were rasterised with PDFium and inspected at original resolution. Heading blocks are kept together. No clipping, overlap, missing glyph, broken heading or isolated one-word continuation remains. |
| Reproducibility | Writer: `scripts/revise_discussion_summary_v3.py`; text audit: `scripts/audit_discussion_summary_doc.py`; PDF discovery/extraction: `scripts/audit_reference_discussions.py`, `scripts/extract_pdf_page_range.py`; rasterisation: `scripts/rasterize_pdf_pages.py`; final QA directory: `FYP/dissertation_working/qa_discussion_v3_final3`. |
| Next decision | Review whether the stronger 5.3 literature dialogue and the shorter 5.4–5.5 match the intended dissertation voice. Once approved, integrate V3 into the authoritative full manuscript and perform a final Chapter 4–5 transition and reference-list consistency audit. |
