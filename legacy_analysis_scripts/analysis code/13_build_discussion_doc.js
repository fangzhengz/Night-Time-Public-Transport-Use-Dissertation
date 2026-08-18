const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, PageNumber, Header, Footer
} = require("docx");

const IMG = "D:\\SDS2025_workspace\\CASA_FYP\\FYP\\outputs\\";
const OUT = "D:\\SDS2025_workspace\\CASA_FYP\\FYP\\night_transport_RQ1_discussion.docx";

const PURPLE = "500778", ACC = "8E6BB8", GREY = "666666", BODYC = "222222";
const QFILL = "FBF3DE", QBORDER = "C89B3C", TINT = "F4F0F8";

// ---- helpers ----
const P = (txt, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, before: opts.before ?? 0, line: 276 },
  alignment: opts.align,
  children: Array.isArray(txt) ? txt : [new TextRun({ text: txt, size: opts.size ?? 21, color: opts.color ?? BODYC, bold: opts.bold, italics: opts.italics })],
});
const run = (t, o = {}) => new TextRun({ text: t, size: o.size ?? 21, color: o.color ?? BODYC, bold: o.bold, italics: o.italics });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 140 }, children: [new TextRun({ text: t, bold: true, size: 30, color: PURPLE, font: "Arial" })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 180, after: 90 }, children: [new TextRun({ text: t, bold: true, size: 24, color: PURPLE, font: "Arial" })] });
const bullet = (children) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 70, line: 270 }, children: Array.isArray(children) ? children : [run(children)] });

function img(file, wpx) {
  const meta = { // px dims for AR
    "old": [1440, 1600], "k4p": [1335, 1212], "k4m": [1485, 921],
    "busm": [1485, 1186], "svc": [1744, 1390], "af": [1200, 960],
  };
  return file;
}
function picture(path, wpx, arW, arH, caption) {
  const h = Math.round(wpx * arH / arW);
  const kids = [new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 80, after: 40 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: wpx, height: h },
      altText: { title: caption || "figure", description: caption || "figure", name: "fig" } })],
  })];
  if (caption) kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 140 },
    children: [new TextRun({ text: caption, italics: true, size: 17, color: GREY })] }));
  return kids;
}

function discuss(text) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: 9360, type: WidthType.DXA },
      shading: { fill: QFILL, type: ShadingType.CLEAR },
      borders: { top: { style: BorderStyle.SINGLE, size: 8, color: QBORDER }, bottom: { style: BorderStyle.SINGLE, size: 8, color: QBORDER }, left: { style: BorderStyle.SINGLE, size: 18, color: QBORDER }, right: { style: BorderStyle.SINGLE, size: 8, color: QBORDER } },
      margins: { top: 100, bottom: 100, left: 160, right: 160 },
      children: [
        new Paragraph({ spacing: { after: 50 }, children: [new TextRun({ text: "◆  For discussion", bold: true, size: 19, color: "7A5A12" })] }),
        new Paragraph({ children: [new TextRun({ text: text, size: 20, color: BODYC })] }),
      ],
    })] })],
  });
}

function evidenceTable() {
  const head = ["", "Tent. K", "Silhouette", "Stability (ARI)", "Note"];
  const rows = [
    ["Rail · weekday", "4", "0.33", "0.83", "4 distinct roles; K=3 dissolves nightlife"],
    ["Rail · weekend", "3 + airport", "0.23", "0.47", "weaker structure; Heathrow flagged separately"],
    ["Bus · weekday", "3", "0.20", "0.84", "even, stable; higher K only peels outliers"],
    ["Bus · weekend", "3", "0.22", "0.96", "very robust; mostly timing-driven"],
  ];
  const cw = [1700, 1100, 1300, 1500, 3760];
  const cell = (t, opts = {}) => new TableCell({
    width: { size: opts.w, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    borders: { top: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" }, bottom: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" }, left: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" }, right: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" } },
    children: [new Paragraph({ children: [new TextRun({ text: t, size: opts.size ?? 19, bold: opts.bold, color: opts.color ?? BODYC })] })],
  });
  const headRow = new TableRow({ tableHeader: true, children: head.map((t, i) => cell(t, { w: cw[i], bold: true, color: "FFFFFF", fill: PURPLE })) });
  const bodyRows = rows.map((r, ri) => new TableRow({ children: r.map((t, i) => cell(t, { w: cw[i], bold: i === 1, color: i === 1 ? PURPLE : BODYC, fill: ri % 2 === 0 ? TINT : undefined })) }));
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: cw, rows: [headRow, ...bodyRows] });
}

const children = [];

// ===== Title block =====
children.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Night-time Public Transport & Spatial Equity in London", bold: true, size: 34, color: PURPLE, font: "Arial" })] }));
children.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "RQ1 — Clustering: methods, results & open questions for discussion", size: 24, color: ACC, bold: true })] }));
children.push(new Paragraph({ spacing: { after: 30 }, children: [new TextRun({ text: "Fangzheng  |  UCL CASA × TfL  |  discussion brief", size: 19, color: GREY, italics: true })] }));
children.push(new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: PURPLE, space: 4 } }, spacing: { after: 160 }, children: [] }));

// ===== Purpose =====
children.push(P([run("This brief is for discussion, not a status report. ", { bold: true }),
  run("It walks through the main method decisions taken in RQ1 (the clustering of night-time demand profiles), the results they produce, and the open questions where I would value your steer. Each section ends with a highlighted discussion prompt.")]));

// ===== 1. Window =====
children.push(H1("1. Analysis window: 18:00–06:00 → 20:00–06:00"));
children.push(P([run("The preprocessing keeps the full 18:00–06:00 night period, but the clustering now starts at "), run("20:00", { bold: true }), run(". The reasoning:")]));
children.push(bullet([run("18:00–20:00 is still the PM commute tail", { bold: true }), run(" — a strong, generic commute signal that dominates the clustering and masks night-specific patterns.")]));
children.push(bullet([run("20:00 better matches the night-time economy", { bold: true }), run(" — leisure and night-work travel, rather than the end of the working day.")]));
children.push(bullet([run("Comparability", { bold: true }), run(" — the same 20:00 start is used for rail and bus, weekday and weekend.")]));
children.push(P([run("Note: ", { bold: true, color: GREY }), run("the specific rationale above is my analytical reasoning; if there is a stronger data- or literature-based justification you would prefer, we should record it.", { italics: true, color: GREY })], { size: 19 }));
children.push(discuss("Is 20:00 the right cut-off, or should the night window be defined differently (e.g. 22:00 / 23:00, or aligned to Night Tube operating hours)? Does excluding 18:00–20:00 risk losing any genuinely night-relevant travel?"));

// ===== 2. Clustering algorithm =====
children.push(H1("2. Clustering algorithm — the GMM-full problem"));
children.push(P([run("Early attempts used "), run("GMM with full covariance", { bold: true }), run(" on the high-dimensional raw feature matrix (≈80 quarter-hour share columns). This was unstable: with only 270 stations, the number of covariance parameters greatly exceeds the sample, producing near-singular covariances and erratic solutions.")]));
children.push(P([run("Response so far: "), run("switched to GMM with diagonal covariance", { bold: true }), run(" for stability. However, on the raw features K remained ambiguous regardless of covariance type.")]));
children.push(P([run("Current state: "), run("the problem appears largely resolved", { bold: true, color: PURPLE }), run(" once the feature space is reduced (Section 3). In the low-dimensional engineered space, GMM (diagonal and full), KMeans and Ward broadly agree — cross-model silhouette on rail weekday sits at GMM ≈ 0.26–0.32, KMeans ≈ 0.33–0.34, Ward ≈ 0.32.")]));
children.push(discuss("Which algorithm would you recommend we commit to going forward — model-based GMM (soft assignment, posterior probabilities, BIC) or KMeans/Ward (simpler, here marginally higher silhouette)? Is reporting one primary method plus one cross-model robustness check an acceptable framing?"));

// ===== 3. Feature engineering =====
children.push(H1("3. Feature engineering (the main change)"));

children.push(H2("3.1  Why the early version failed"));
children.push(P([run("The first version clustered on "), run("raw, normalised entry/exit shares only", { bold: true }), run(". Every station's night curve carries the same decline shape (high at 20:00, fading toward zero) — a shared ‘envelope’. In the raw features this common shape is the largest source of variance, so distance is dominated by overall level and the signals that distinguish station roles (direction, timing, persistence) are buried.")]));
children.push(...picture(IMG + "lu_rail_2000_diag\\weekday\\weekday_profiles.png", 360, 1440, 1600, "Old features (raw shares): weekday clusters C0/C1/C3 are nearly identical."));
children.push(P([run("Symptoms: ", { bold: true }), run("near-duplicate clusters (C0/C1/C3 ≈ 75% of stations), centroid cosine distance < 0.018, silhouette ≈ 0.07, and a hard-coded K=5/6 that no index actually supported. After consulting on approach, I moved to behavioural feature engineering.")]));

children.push(H2("3.2  Feature list"));
children.push(bullet([run("A_net — net directionality", { bold: true }), run(": (entry − exit) / total → origin vs destination.")]));
children.push(bullet([run("F_flip — direction flip", { bold: true }), run(": early- vs late-night directionality → ‘leave then return’ vs ‘arrive then leave’.")]));
children.push(bullet([run("t_median — timing", { bold: true }), run(": when activity peaks (early evening vs deep night).")]));
children.push(bullet([run("persist_00 — late persistence", { bold: true }), run(": share of activity after midnight.")]));
children.push(bullet([run("hump_22 — nightlife bump", { bold: true }), run(": secondary 22–23h peak.")]));
children.push(bullet([run("dawn — dawn rebound", { bold: true }), run(": 04:30–06:00 share (early-shift workers / airport).")]));

children.push(H2("3.3  The two core axes"));
children.push(P([run("A_net = (Σentry − Σexit) / (Σentry + Σexit), range [−1, +1].", { bold: true })]));
children.push(P("Greater than 0 = entry-dominant = origin (people leaving); less than 0 = exit-dominant = destination (people arriving). Dividing by total makes it scale-free and cancels the shared decline envelope, isolating direction."));
children.push(P([run("F_flip = A_early − A_late  (early = 20–23h, late = 23–01h).", { bold: true })]));
children.push(P("Greater than 0 = early-out then late-in (‘leave then return’, residential); less than 0 = early-in then late-out (‘arrive then leave’, nightlife/destination). It is the signed, continuous version of the entry/exit crossover seen in the profiles."));

children.push(H2("3.4  Selection logic"));
children.push(bullet("Prefer contrast features (A_net, F_flip): subtracting entry from exit removes the shared envelope, leaving only the discriminative signal."));
children.push(bullet("Prune dead / redundant axes: 'dawn' is empty for the weekday window; 'early_conc' ≈ −t_median (correlation .85–.91) and was dropped; for bus, persist_00 overlapped dawn/t_median and was pruned."));
children.push(bullet("Standardise (z-score) so each axis weighs equally; inspect the correlation matrix before clustering."));

children.push(H2("3.5  Effect"));
children.push(P([run("Weekday rail silhouette rose from ≈ 0.07 (raw) to ≈ 0.33 (engineered) — a 4–5× improvement.", { bold: true }), run(" Clusters now have distinct, nameable shapes; the three models broadly agree; and, as an unsupervised validation, the three Heathrow stations separate cleanly on extreme F_flip + dawn (a genuine airport / 24h type).")]));
children.push(...picture(IMG + "lu_rail_2000_featv2\\candidates\\weekday_k4_profiles.png", 430, 1335, 1212, "Engineered features, rail weekday K=4: four clearly different profiles."));
children.push(discuss("Are these engineered features methodologically sound, or do they inject too much prior assumption? Which would you add or drop? Should a more 'hands-off' baseline (raw shares + PCA) be reported alongside, and does a compositional (log-ratio) treatment of the shares matter here?"));

// ===== 4. K selection =====
children.push(H1("4. Choosing the number of clusters (K)"));
children.push(P("Internal indices are flat across K, which points to a partly continuous structure rather than well-separated groups. Silhouette alone cannot discriminate K=3/4/5 for rail (all ≈ 0.33). I therefore lean on bootstrap stability (ARI across resamples) and interpretability."));
children.push(evidenceTable());
children.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
children.push(discuss("When indices are flat, is it defensible to choose K by stability + interpretability rather than an index peak? Are the tentative Ks (rail weekday 4; rail weekend 3 + airport; bus 3) reasonable, or would you expect a different number of night-time types?"));

// ===== 5. Bus spatial unit =====
children.push(H1("5. Is LSOA-level bus clustering appropriate?"));
children.push(P("Rail is clustered at the station (point) level; bus is aggregated to LSOA (area) level. This asymmetry matters:"));
children.push(bullet([run("Rail — discrete stations: ", { bold: true }), run("each station is one functional entity, giving sharp, distinctive signatures (airport / CBD / nightlife / residential). Supports up to 4 types plus special cases.")]));
children.push(bullet([run("Bus — LSOA aggregates: ", { bold: true }), run("each LSOA contains many stops on mixed routes, so distinctive signals are averaged out (modifiable areal unit problem). Profiles are more homogeneous, supporting ≈ 3 types and staying low-K.")]));
children.push(P([run("This is itself a finding", { bold: true }), run(" — rail carries London’s specialised night roles, while bus is a more uniform spatial baseline — but it is partly an artefact of the chosen unit.")]));
children.push(discuss("Is LSOA the right unit for bus, or should we cluster at stop level (finer but noisier) or another aggregation? Is the lower number of bus types an acceptable substantive result, or a unit artefact we should address?"));

// ===== 6. Bus blank areas =====
children.push(H1("6. Bus ‘blank’ areas (the n ≥ 50 filter)"));
children.push(P([run("Before clustering, LSOAs with total night-window bus demand below 50 are removed. Of London’s 4,994 LSOAs (weekday): "), run("60% are clustered", { bold: true }), run(", "), run("22% are low-service", { bold: true }), run(" (0 < demand < 50), and "), run("18% have no recorded night bus at all", { bold: true }), run(". The low/no-service areas concentrate in the outer ring.")]));
children.push(...picture(IMG + "busto_lsoa_2000_gmm\\weekday\\weekday_bus_cluster_map.png", 430, 1744, 1390, "Weekday bus: clustered / low-service / no-service LSOAs."));
children.push(P([run("This is arguably an equity result in its own right (where there is little or no night bus), and an input to RQ3.", { italics: true })]));
children.push(discuss("How should the dropped 40% be handled? Options: keep them as explicit 'low-service' and 'no-service' categories (an equity finding), lower the n ≥ 50 threshold, or change the spatial unit. Is the threshold itself defensible, and should it differ between weekday and weekend?"));

// ===== 7. Current results =====
children.push(H1("7. Where the results stand right now (tentative)"));
children.push(P([run("Rail, weekday (K=4): ", { bold: true }), run("nightlife/destination (central) · residential-return early (outer) · balanced/through · residential-return later; plus Heathrow as a flagged airport type at weekend.")]));
children.push(P([run("Bus, weekday (K=3): ", { bold: true }), run("destination-early · balanced · late/dawn-persistent (arrival + a strong 05:00 boarding surge).")]));
children.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [4680, 4680], rows: [new TableRow({ children: [
  new TableCell({ width: { size: 4680, type: WidthType.DXA }, borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } }, margins: { top: 40, bottom: 40, left: 40, right: 40 }, children: picture(IMG + "lu_rail_2000_featv2\\candidates\\weekday_k4_map.png", 290, 1485, 921, "Rail weekday K=4") }),
  new TableCell({ width: { size: 4680, type: WidthType.DXA }, borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } }, margins: { top: 40, bottom: 40, left: 40, right: 40 }, children: picture(IMG + "busto_lsoa_2000_featv2\\candidates\\weekday_k3_map.png", 290, 1485, 1186, "Bus weekday K=3") }),
]})]}));

// ===== 8. Questions =====
children.push(H1("8. Consolidated questions for the meeting"));
[
  "Window — is 20:00–06:00 the right night window?",
  "Method — which clustering algorithm should we standardise on?",
  "Features — is the behavioural feature engineering sound; what to add or drop?",
  "K — are the tentative Ks (rail 4 / bus 3) reasonable when indices are flat?",
  "Spatial unit — is LSOA-level bus clustering appropriate, or should we go stop-level?",
  "Blank areas — how should the 40% of LSOAs dropped by the n ≥ 50 filter be handled?",
].forEach((q, i) => children.push(new Paragraph({ numbering: { reference: "n", level: 0 }, spacing: { after: 80, line: 270 }, children: [run(q)] })));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 21, color: BODYC } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, color: PURPLE, font: "Arial" }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: PURPLE, font: "Arial" }, paragraph: { spacing: { before: 180, after: 90 }, outlineLevel: 1 } },
    ] },
  numbering: { config: [
    { reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] },
    { reference: "n", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 280 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "RQ1 discussion brief · page ", size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("Saved", OUT); });
