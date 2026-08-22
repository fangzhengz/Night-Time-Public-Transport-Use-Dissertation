import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "..");
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
  return rows.map((r, ri) => r.map((v) => {
    if (ri === 0 || v === "") return v === "" ? null : v;
    const n = Number(v);
    return Number.isFinite(n) ? n : v;
  }));
}

async function readCsv(name) {
  return parseCsv(await fs.readFile(path.join(dataDir, name), "utf8"));
}

const workbook = Workbook.create();
workbook.comments.setSelf({ displayName: "User" });

const titleFill = "#234F79";
const headerFill = "#DCE6F1";
const sheets = [
  ["Rail Summary", "rail_cluster_metric_summary.csv"],
  ["Bus Summary", "bus_cluster_metric_summary.csv"],
  ["Rail Units", "rail_unit_metrics.csv"],
  ["Bus Units", "bus_unit_metrics.csv"],
  ["Audit", "data_audit.csv"],
];

for (const [sheetName, fileName] of sheets) {
  const rows = await readCsv(fileName);
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;
  const cols = Math.max(...rows.map((r) => r.length));
  const padded = rows.map((r) => [...r, ...Array(cols - r.length).fill(null)]);
  sheet.getRangeByIndexes(0, 0, padded.length, cols).values = padded;
  sheet.getRangeByIndexes(0, 0, 1, cols).format = {
    fill: titleFill,
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: "#AAB7C4" },
  };
  if (padded.length > 1) {
    sheet.getRangeByIndexes(1, 0, padded.length - 1, cols).format.borders = {
      insideHorizontal: { style: "thin", color: "#E5E7EB" },
    };
  }
  sheet.freezePanes.freezeRows(1);
  sheet.getUsedRange().format.autofitColumns();
  sheet.getUsedRange().format.autofitRows();
  for (let c = 0; c < cols; c++) {
    const range = sheet.getRangeByIndexes(0, c, padded.length, 1);
    if (range.format.columnWidth > 28) range.format.columnWidth = 28;
  }
}

const summary = workbook.worksheets.add("Read Me");
summary.showGridLines = false;
summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["RQ1 context metrics — fixed-cluster interpretation layer"]];
summary.getRange("A1:H1").format = {
  fill: titleFill,
  font: { bold: true, color: "#FFFFFF", size: 16 },
  rowHeight: 30,
};
summary.getRange("A3:B9").values = [
  ["Item", "Definition"],
  ["Scope", "Adds volume, direction balance and timing ratios after clustering."],
  ["Rail volume", "Representative nights across MON, TWT, FRI, SAT and SUN."],
  ["Bus volume", "Representative Weekday, Saturday and Sunday nights."],
  ["Volume bands", "Mode-specific tertiles; not comparable across modes."],
  ["Rail timing", "Common 18:00–01:00 window separated from 01:00–05:00 Night Tube extension."],
  ["Boundary", "Observed use only; no passenger identity, purpose or unmet-demand inference."],
];
summary.getRange("A3:B3").format = { fill: headerFill, font: { bold: true } };
summary.getRange("A3:B9").format.wrapText = true;
summary.getRange("A3:B9").format.borders = { preset: "outside", style: "thin", color: "#AAB7C4" };
summary.getRange("A:B").format.columnWidth = 28;
summary.getRange("B:B").format.columnWidth = 65;

const inspect = await workbook.inspect({
  kind: "table",
  range: "Read Me!A1:H10",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 8,
});
await fs.writeFile(path.join(outDir, "rq1_context_metrics_results.inspect.ndjson"), inspect.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
await fs.writeFile(path.join(outDir, "rq1_context_metrics_results.errors.ndjson"), errors.ndjson);
const preview = await workbook.render({ sheetName: "Read Me", range: "A1:H10", scale: 1.5 });
await fs.writeFile(path.join(outDir, "rq1_context_metrics_preview.png"), new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outDir, "rq1_context_metrics_results.xlsx"));
console.log("Workbook written:", path.join(outDir, "rq1_context_metrics_results.xlsx"));
