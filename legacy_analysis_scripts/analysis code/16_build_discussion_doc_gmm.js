const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, PageNumber, Footer
} = require("docx");

const IMG = "D:\\SDS2025_workspace\\CASA_FYP\\FYP\\outputs\\";
const OUT = "D:\\SDS2025_workspace\\CASA_FYP\\FYP\\night_transport_RQ1_discussion.docx";

const PURPLE = "500778", ACC = "8E6BB8", GREY = "666666", BODYC = "222222";
const QFILL = "FBF3DE", QBORDER = "C89B3C", TINT = "F4F0F8", REDC = "9A3D3D";

const P = (kids, opts = {}) => new Paragraph({ spacing: { after: opts.after ?? 120, before: opts.before ?? 0, line: 276 }, alignment: opts.align, children: Array.isArray(kids) ? kids : [new TextRun({ text: kids, size: opts.size ?? 21, color: opts.color ?? BODYC, bold: opts.bold, italics: opts.italics })] });
const run = (t, o = {}) => new TextRun({ text: t, size: o.size ?? 21, color: o.color ?? BODYC, bold: o.bold, italics: o.italics });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 130 }, children: [new TextRun({ text: t, bold: true, size: 30, color: PURPLE, font: "Arial" })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 170, after: 80 }, children: [new TextRun({ text: t, bold: true, size: 23, color: PURPLE, font: "Arial" })] });
const bullet = (kids) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 70, line: 270 }, children: Array.isArray(kids) ? kids : [run(kids)] });

function picture(path, wpx, arW, arH, caption) {
  const h = Math.round(wpx * arH / arW);
  const kids = [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 30 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: wpx, height: h }, altText: { title: caption || "f", description: caption || "f", name: "f" } })] })];
  if (caption) kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 140 }, children: [new TextRun({ text: caption, italics: true, size: 17, color: GREY })] }));
  return kids;
}
function discuss(text) {
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], rows: [new TableRow({ children: [new TableCell({
    width: { size: 9360, type: WidthType.DXA }, shading: { fill: QFILL, type: ShadingType.CLEAR },
    borders: { top: { style: BorderStyle.SINGLE, size: 8, color: QBORDER }, bottom: { style: BorderStyle.SINGLE, size: 8, color: QBORDER }, left: { style: BorderStyle.SINGLE, size: 18, color: QBORDER }, right: { style: BorderStyle.SINGLE, size: 8, color: QBORDER } },
    margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: [new Paragraph({ spacing: { after: 50 }, children: [new TextRun({ text: "◆  For discussion", bold: true, size: 19, color: "7A5A12" })] }), new Paragraph({ children: [new TextRun({ text: text, size: 20, color: BODYC })] })],
  })] })] });
}
function table(head, rows, cw) {
  const cell = (t, o = {}) => new TableCell({ width: { size: o.w, type: WidthType.DXA }, shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR } : undefined, margins: { top: 55, bottom: 55, left: 100, right: 100 }, borders: { top: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" }, bottom: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" }, left: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" }, right: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" } }, children: [new Paragraph({ children: [new TextRun({ text: t, size: o.size ?? 19, bold: o.bold, color: o.color ?? BODYC })] })] });
  const hr = new TableRow({ tableHeader: true, children: head.map((t, i) => cell(t, { w: cw[i], bold: true, color: "FFFFFF", fill: PURPLE })) });
  const br = rows.map((r, ri) => new TableRow({ children: r.map((t, i) => cell(t, { w: cw[i], bold: i === 0, color: BODYC, fill: ri % 2 === 0 ? TINT : undefined })) }));
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: cw, rows: [hr, ...br] });
}

const c = [];
// Title
c.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Night-time Public Transport & Spatial Equity in London", bold: true, size: 34, color: PURPLE, font: "Arial" })] }));
c.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "RQ1 clustering — methods, results & open questions (updated, GMM)", size: 24, color: ACC, bold: true })] }));
c.push(new Paragraph({ spacing: { after: 30 }, children: [new TextRun({ text: "Fangzheng  |  UCL CASA × TfL  |  discussion brief, rev. for 2026-06-24 meeting", size: 19, color: GREY, italics: true })] }));
c.push(new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: PURPLE, space: 4 } }, spacing: { after: 160 }, children: [] }));
c.push(P([run("Discussion brief, not a status report. ", { bold: true }), run("Updated to reflect the move to GMM (the earlier KMeans-based write-up is superseded). It records the method decisions, the current — now less clear-cut — results, and the open questions, of which the most important is a structural mismatch between the clusters the model produces and the night-use types the analysis needs.")]));

// 1 Window
c.push(H1("1. Analysis window: 18:00–06:00 → 20:00–06:00"));
c.push(P([run("Clustering starts at "), run("20:00", { bold: true }), run(". 18:00–20:00 is still the PM commute tail — a generic signal that dominates and masks night-specific patterns; 20:00 better matches the night-time economy; and the same start is used across modes and day-types.")]));
c.push(discuss("Is 20:00 the right cut-off, or should the night window be defined differently (e.g. 22:00/23:00, or aligned to Night Tube hours)?"));

// 2 Weekday/weekend definition
c.push(H1("2. Weekday / weekend definition — and a rail–bus mismatch"));
c.push(P([run("Originally weekend = Fri+Sat+Sun. But "), run("Sunday has no Night Tube, so its pattern behaves like a weekday", { bold: true }), run(". I therefore moved to weekend = Fri+Sat, with Sunday in weekday. Empirically this tightened the weekday clustering (Sunday reinforces rather than dilutes it) and left weekend no worse.")]));
c.push(P([run("Data-forced mismatch: ", { bold: true, color: REDC }), run("BUSTO only has day-types Weekday / Saturday / Sunday and "), run("cannot isolate Friday", { bold: true }), run(" (Friday sits inside ‘Weekday’). So bus cannot mirror the rail Fri–Sat split — a cross-mode comparability problem. A bus version under the new definition was generated but its ‘weekend’ collapses to Saturday-only.")]));
c.push(discuss("How should weekday/weekend be defined given (a) no Sunday Night Tube and (b) bus data that cannot separate Friday? Is the rail Fri–Sat / bus Sat-only asymmetry acceptable, or do we need a common compromise?"));

// 3 Algorithm
c.push(H1("3. Clustering algorithm — now GMM (diagonal)"));
c.push(P([run("Early high-dimensional attempts with "), run("GMM full covariance were unstable", { bold: true }), run(" (near-singular covariances, parameters ≫ 270 stations). After feature engineering reduced the space, I returned to "), run("GMM with diagonal covariance as the primary model", { bold: true }), run("; KMeans and Ward are kept as cross-model checks.")]));
c.push(P([run("On full covariance: ", { bold: true }), run("now numerically feasible (converges for K=2–6), but BIC does not consistently favour it — at rail weekday K=4, diagonal BIC (414) is far better than full (2024). So diagonal is retained.")]));
c.push(P([run("Caveat introduced by the switch: ", { italics: true, color: REDC }), run("compared with KMeans, GMM gives lower silhouettes and more imbalanced clusters, and the K choice became less clear (Section 7–8).", { italics: true })]));
c.push(discuss("Which algorithm should we commit to — GMM (soft assignment, posteriors, BIC) or KMeans/Ward (simpler, higher silhouette here)? Given the results shifted on switching, this choice is consequential."));

// 4 Feature engineering
c.push(H1("4. Feature engineering (an AI-proposed approach)"));
c.push(P([run("To be transparent about provenance: the original analysis clustered on the raw, normalised entry/exit share curves only, and performed poorly — near-duplicate clusters, silhouette ≈ 0.07, K unresolvable. ", {}), run("On AI's suggestion I then adopted the behavioural feature-engineering approach below; the specific feature set was AI-proposed.", { bold: true })]));
c.push(P("Each station's curve is summarised into a few contrast-type scalars:"));
c.push(bullet([run("A_net — net directionality", { bold: true }), run(": (entry−exit)/total → origin vs destination.")]));
c.push(bullet([run("F_flip — direction flip", { bold: true }), run(": early- vs late-night directionality → ‘leave then return’ vs ‘arrive then leave’.")]));
c.push(bullet([run("t_median / persist_00 / hump_22 / dawn", { bold: true }), run(": timing, post-midnight persistence, 22–23h nightlife bump, 04:30–06:00 rebound.")]));
c.push(P([run("Key difference from the original approach: ", { bold: true }), run("the original already kept entry and exit as separate normalised blocks, so it retained directional timing (the entry/exit crossover) — but each block summed to 1, so it discarded the entry-vs-exit volume balance (A_net). It also worked in ~80 highly-correlated dimensions dominated by the shared night-decline envelope. The engineered set's genuinely new directional axis is A_net; F_flip mainly concentrates timing information the original already contained, and reducing to ~6 interpretable axes lets the contrast features cancel the shared envelope.")]));
c.push(P([run("A limitation of both versions: ", { bold: true, color: REDC }), run("every feature is a share or ratio (scale-free), so station total night-time flow is not used — a tiny station and a major hub cluster together if their shapes match. Shape-normalisation is standard in profile-clustering, but for night-time equity, where service and demand are thin, absolute flow arguably matters more; it could be brought back as a separate layer (cluster × volume tier) rather than inside the clustering.")]));
c.push(P([run("Outcome: the clustering improved — weekday silhouette ~0.07 → ~0.3, and the Heathrow stations separate cleanly (extreme F_flip + dawn). ", {}), run("But the cluster division is still not clean (Section 6). So the feasibility of this AI-proposed feature set, and the soundness of the method, are themselves open for discussion — including the risk that hand-picked features ‘carve out’ the structure we expected to see.", { bold: true })]));
c.push(discuss("Is this AI-proposed feature set methodologically defensible, or does it over-inject prior assumptions? Which features would you add/drop? Should a more hands-off baseline (raw-share + PCA) be reported alongside as a check, and does compositional (log-ratio) treatment of the shares matter?"));

// 5 Visualization gap
c.push(H1("5. A visualisation gap — the profile plot hides A_net"));
c.push(P([run("The entry/exit profile plots normalise each direction to sum 1, so they show timing, shape, the crossover (F_flip) and the 22–23h hump — but "), run("not A_net", { bold: true }), run(". Two clusters with similar shapes but opposite entry/exit volume balance look identical in the plot even though the model separates them. This is why some clusters ‘look the same’ in the profiles yet are kept apart.")]));
c.push(discuss("Should the profiles be re-plotted as shares of total activity (making A_net visible), and/or accompanied by a per-cluster feature signature, so the figure matches what the model actually uses?"));

// 6 Typology mismatch (CORE)
c.push(H1("6. The core problem — clusters ≠ night-use types"));
c.push(P([run("This is the most important issue. ", { bold: true }), run("Variance/likelihood clustering spends its K budget on the large homogeneous ‘smooth-decline’ mass, splitting it into near-duplicate clusters that should be ONE type, while the genuinely distinct small types only appear at high K (or not at all).")]));
c.push(P([run("Example (rail weekday, GMM): at K=3 two clusters differ only by A_net −0.36 vs −0.56 and t_median 0.30 vs 0.35 — in any write-up these are the same night-use type. The visibly distinct nightlife/destination type (a 22–23h entry hump, n≈18) only emerges at K=5; Heathrow (n≈3) only at weekend K=5.")]));
c.push(...picture(IMG + "lu_rail_2000_featv2_FS\\candidates\\weekday_k3_profiles.png", 430, 1335, 912, "K=3: clusters look alike (differences are in A_net/timing, hidden above)."));
c.push(...picture(IMG + "lu_rail_2000_featv2_FS\\candidates\\weekday_k5_profiles.png", 330, 1335, 1513, "K=5: only now does a distinct nightlife type (C3, hump) appear."));
c.push(P([run("So the clusters the model returns do not map cleanly onto interpretable types: the mass is over-split, the distinct pockets are buried.", { bold: true })]));
c.push(discuss("How should we handle this? Options to weigh: (a) low-K main types + separate special-type detection (HDBSCAN density clusters, or flag via GMM low max-posterior/high entropy, or feature rules for airport/nightlife); (b) peel known special types first, then cluster the remainder at low K; (c) reframe as a continuum plus a named special-case catalogue. [Strategy to be decided in this meeting.]"));

// 7 K under GMM
c.push(H1("7. Choosing K — now ambiguous under GMM"));
c.push(P("With GMM the internal indices disagree about K (a symptom of the continuous structure plus small distinct pockets). Best-K by each metric, on the adopted definitions:"));
c.push(table(["group", "best by silhouette", "best by DB", "best by stability", "tension"],
  [["Rail wd", "K=2 / 5", "K=4", "K=2 / 5", "4 vs 2/5"],
   ["Rail we", "K=2", "K=4", "K=2", "2 vs 4"],
   ["Bus wd", "K=2", "K=5", "K=2", "2 vs 5"],
   ["Bus we", "K=2", "K=4", "K=4", "2 vs 4"]],
  [1500, 2100, 1500, 2100, 2160]));
c.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
c.push(...picture(IMG + "lu_rail_2000_featv2_FS\\weekday_kdiag_v2.png", 470, 1584, 1191, "Rail weekday (GMM): silhouette, CH, DB and bootstrap stability vs K."));
c.push(discuss("When indices disagree like this, how should K be chosen — by DB + interpretability, by stability, or by abandoning a single global K in favour of the two-tier approach in Section 6?"));

// 8 Bus unit + blanks
c.push(H1("8. Bus — spatial unit and blank areas"));
c.push(P([run("Bus is clustered at LSOA (area) level, rail at station (point) level. Bus clusters look more balanced and stable, "), run("but this is a sign of weaker structure, not stronger", { bold: true }), run(": aggregation averages out distinctive signals (MAUP), so bus is a smooth continuum with no sharp special types — hence balanced but low-silhouette clusters. Rail’s imbalance, by contrast, reflects real special types (airport, nightlife) being carved out.")]));
c.push(P([run("Separately, the n ≥ 50 night-demand filter drops ~40% of LSOAs before clustering: ~22% have some night bus below threshold, ~18% none at all — concentrated in the outer ring (an equity signal in itself).")]));
c.push(...picture(IMG + "busto_lsoa_2000_gmm\\weekday\\weekday_bus_cluster_map.png", 360, 1744, 1390, "Weekday bus: clustered / low-service / no-service LSOAs."));
c.push(discuss("Is LSOA the right unit for bus (vs stop level)? And how should the dropped 40% be handled — explicit low/no-service categories, a lower threshold, or a different unit?"));

// 9 Current results
c.push(H1("9. Current tentative results (provisional)"));
c.push(P([run("These are GMM, on the adopted definitions, and are provisional pending the Section 6 decision.", { italics: true })]));
c.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [4680, 4680], rows: [new TableRow({ children: [
  new TableCell({ width: { size: 4680, type: WidthType.DXA }, borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } }, margins: { top: 40, bottom: 40, left: 40, right: 40 }, children: picture(IMG + "lu_rail_2000_featv2_FS\\candidates\\weekday_k4_map.png", 290, 1485, 921, "Rail weekday K=4 (FS)") }),
  new TableCell({ width: { size: 4680, type: WidthType.DXA }, borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } }, margins: { top: 40, bottom: 40, left: 40, right: 40 }, children: picture(IMG + "busto_lsoa_2000_featv2\\candidates\\weekday_k3_map.png", 290, 1485, 1186, "Bus weekday K=3") }),
]})]}));

// 10 Questions
c.push(H1("10. Questions for the meeting"));
[
  "Typology mismatch (priority) — how to capture a few main types AND the distinct small types (Section 6)?",
  "Algorithm — GMM or KMeans/Ward as primary, given results shifted on switching?",
  "K — how to choose when silhouette/DB/stability disagree (Section 7)?",
  "Weekday/weekend — rail Fri–Sat vs bus Sat-only mismatch; is it acceptable?",
  "Window — is 20:00–06:00 right?",
  "Features — are the engineered features sound; PCA/compositional baseline needed?",
  "Flow/volume — all features are scale-free; should absolute night flow enter the analysis (esp. for equity), and how?",
  "Bus — LSOA vs stop level; how to handle the 40% blank LSOAs?",
].forEach((q, i) => c.push(new Paragraph({ numbering: { reference: "n", level: 0 }, spacing: { after: 80, line: 270 }, children: [run(q)] })));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 21, color: BODYC } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, color: PURPLE, font: "Arial" }, paragraph: { spacing: { before: 300, after: 130 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, color: PURPLE, font: "Arial" }, paragraph: { spacing: { before: 170, after: 80 }, outlineLevel: 1 } }] },
  numbering: { config: [
    { reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] },
    { reference: "n", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 280 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "RQ1 discussion brief (GMM) · page ", size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY })] })] }) },
    children: c }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("Saved", OUT); });
