import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const srcDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(srcDir, "..");
const dataDir = path.join(root, "outputs", "data");
const outDir = path.join(root, "outputs", "workbook");
await fs.mkdir(outDir, { recursive: true });

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += c;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  return rows.map((r, ri) => r.map((value) => {
    if (ri === 0 || value === "") return value === "" ? null : value;
    const number = Number(value);
    return Number.isFinite(number) ? number : value;
  }));
}

async function readCsv(name) {
  return parseCsv(await fs.readFile(path.join(dataDir, name), "utf8"));
}

const workbook = Workbook.create();
workbook.comments.setSelf({ displayName: "User" });
const purple = "#500778";
const lavender = "#E8DDF0";
const green = "#2F6B4F";

const readMe = workbook.worksheets.add("Read Me");
readMe.showGridLines = false;
readMe.getRange("A1:H1").merge();
readMe.getRange("A1").values = [["Bus 15-minute vs 1-hour fair stability validation"]];
readMe.getRange("A1:H1").format = {
  fill: purple,
  font: { bold: true, color: "#FFFFFF", size: 16 },
  rowHeight: 30,
};
readMe.getRange("A3:B13").values = [
  ["Design item", "Specification"],
  ["Source", "Both matrices rebuilt from the same validated 15-minute LSOA long table."],
  ["Units", "Same 4,100 non-empty LSOAs."],
  ["Only treatment", "Temporal bin width: 15 minutes versus 1 hour."],
  ["K", "3, 4 and 5."],
  ["Covariance", "Matched diag and tied GMMs."],
  ["Seeds", "Same six seeds for both resolutions."],
  ["Bootstrap", "Same ten resamples for both resolutions."],
  ["Common-space test", "Both label sets evaluated on the same 1-hour feature matrix."],
  ["External interpretation", "Volume, late-night timing, direction, weekend ratio and LNWC."],
  ["Boundary", "Interpretability cannot compensate for unstable assignments."],
];
readMe.getRange("A3:B3").format = { fill: lavender, font: { bold: true } };
readMe.getRange("A3:B13").format.wrapText = true;
readMe.getRange("A3:B13").format.borders = { preset: "outside", style: "thin", color: "#B8A5C6" };
readMe.getRange("A:A").format.columnWidth = 28;
readMe.getRange("B:B").format.columnWidth = 72;

const sheetSpecs = [
  ["Model Comparison", "model_comparison.csv"],
  ["Cross Resolution", "cross_resolution_agreement.csv"],
  ["Interpretability", "interpretability_metrics.csv"],
  ["Cluster Signatures", "cluster_signatures.csv"],
  ["15m K4 Unit Stability", "unit_stability_15min_diag_k4.csv"],
  ["1h K4 Unit Stability", "unit_stability_1h_diag_k4.csv"],
  ["Contingencies", "cross_resolution_contingency_long.csv"],
  ["Data Audit", "data_audit.csv"],
  ["Input Manifest", "input_manifest.csv"],
];

for (const [sheetName, fileName] of sheetSpecs) {
  const rows = await readCsv(fileName);
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;
  const columns = Math.max(...rows.map((row) => row.length));
  const padded = rows.map((row) => [...row, ...Array(columns - row.length).fill(null)]);
  sheet.getRangeByIndexes(0, 0, padded.length, columns).values = padded;
  sheet.getRangeByIndexes(0, 0, 1, columns).format = {
    fill: sheetName === "Model Comparison" ? green : purple,
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: "#AAB7C4" },
  };
  if (padded.length > 1) {
    sheet.getRangeByIndexes(1, 0, padded.length - 1, columns).format.borders = {
      insideHorizontal: { style: "thin", color: "#E5E7EB" },
    };
  }
  sheet.freezePanes.freezeRows(1);
  sheet.getUsedRange().format.autofitColumns();
  sheet.getUsedRange().format.autofitRows();
  for (let column = 0; column < columns; column++) {
    const range = sheet.getRangeByIndexes(0, column, padded.length, 1);
    if (range.format.columnWidth > 28) range.format.columnWidth = 28;
  }
}

const inspect = await workbook.inspect({
  kind: "table",
  range: "Read Me!A1:H14",
  include: "values,formulas",
  tableMaxRows: 15,
  tableMaxCols: 8,
});
await fs.writeFile(path.join(outDir, "bus_resolution_validation.inspect.ndjson"), inspect.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
await fs.writeFile(path.join(outDir, "bus_resolution_validation.errors.ndjson"), errors.ndjson);
const preview = await workbook.render({ sheetName: "Read Me", range: "A1:H14", scale: 1.5 });
await fs.writeFile(path.join(outDir, "bus_resolution_validation_preview.png"), new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outDir, "bus_resolution_stability_validation.xlsx"));
console.log("Workbook written:", path.join(outDir, "bus_resolution_stability_validation.xlsx"));
