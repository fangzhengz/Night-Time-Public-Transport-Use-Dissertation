import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const srcDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(srcDir, "..");
const dataDir = path.join(root, "outputs", "direct_metrics", "data");
const outDir = path.join(root, "outputs", "direct_metrics", "workbook");
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
const titleFill = "#500778";
const headerFill = "#E8DDF0";

const definitions = workbook.worksheets.add("Read Me");
definitions.showGridLines = false;
definitions.getRange("A1:H1").merge();
definitions.getRange("A1").values = [["RQ2 direct transport metrics × LNWC — provisional"]];
definitions.getRange("A1:H1").format = {
  fill: titleFill,
  font: { bold: true, color: "#FFFFFF", size: 16 },
  rowHeight: 30,
};
definitions.getRange("A3:B10").values = [
  ["Item", "Definition"],
  ["Bus unit", "LSOA with one supplied LNWC category."],
  ["Rail unit", "Station with seven fractional LNWC catchment shares."],
  ["Volume", "log(1 + representative-night total activity)."],
  ["Direction balance", "(entry or boarding − exit or alighting) / total."],
  ["Timing", "Bus post-midnight share; rail Night Tube extension share."],
  ["Centrality control", "Straight-line distance to Charing Cross; exploratory sensitivity only."],
  ["Boundary", "Area-level association; no passenger occupation or causal inference."],
];
definitions.getRange("A3:B3").format = { fill: headerFill, font: { bold: true } };
definitions.getRange("A3:B10").format.wrapText = true;
definitions.getRange("A3:B10").format.borders = { preset: "outside", style: "thin", color: "#B8A5C6" };
definitions.getRange("A:A").format.columnWidth = 28;
definitions.getRange("B:B").format.columnWidth = 68;

const sheets = [
  ["Bus by LNWC", "bus_metrics_by_lnwc.csv"],
  ["Bus Omnibus", "bus_kruskal_wallis.csv"],
  ["Bus Pairwise", "bus_dunn_pairwise.csv"],
  ["Rail Fractional", "rail_metrics_by_lnwc_fractional.csv"],
  ["Adjusted Tests", "centrality_adjusted_tests_all.csv"],
  ["Bus Units", "bus_direct_metrics_lsoa.csv"],
  ["Rail Stations", "rail_direct_metrics_station.csv"],
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
    borders: { preset: "outside", style: "thin", color: "#B8A5C6" },
  };
  if (padded.length > 1) {
    sheet.getRangeByIndexes(1, 0, padded.length - 1, cols).format.borders = {
      insideHorizontal: { style: "thin", color: "#ECE7EF" },
    };
  }
  sheet.freezePanes.freezeRows(1);
  sheet.getUsedRange().format.autofitColumns();
  sheet.getUsedRange().format.autofitRows();
  for (let c = 0; c < cols; c++) {
    const range = sheet.getRangeByIndexes(0, c, padded.length, 1);
    if (range.format.columnWidth > 30) range.format.columnWidth = 30;
  }
}

const inspect = await workbook.inspect({
  kind: "table",
  range: "Read Me!A1:H11",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 8,
});
await fs.writeFile(path.join(outDir, "rq2_direct_metrics_results.inspect.ndjson"), inspect.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
await fs.writeFile(path.join(outDir, "rq2_direct_metrics_results.errors.ndjson"), errors.ndjson);
const preview = await workbook.render({ sheetName: "Read Me", range: "A1:H11", scale: 1.5 });
await fs.writeFile(path.join(outDir, "rq2_direct_metrics_preview.png"), new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outDir, "rq2_direct_metrics_results.xlsx"));
console.log("Workbook written:", path.join(outDir, "rq2_direct_metrics_results.xlsx"));
