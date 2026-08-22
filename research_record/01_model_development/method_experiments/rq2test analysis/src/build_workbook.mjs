import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const dataDir = path.join(root, "outputs", "data");
const reportDir = path.join(root, "outputs", "report");
const workbookDir = path.join(root, "outputs", "workbook");
await fs.mkdir(workbookDir, { recursive: true });

const summary = JSON.parse(
  await fs.readFile(path.join(reportDir, "results_summary.json"), "utf8"),
);

const workbook = Workbook.create();
const summarySheet = workbook.worksheets.add("Summary");
summarySheet.showGridLines = false;

const titleFill = "#500778";
const headerFill = "#D9E2F3";
const subFill = "#EDE7F6";
const accent = "#C89B3C";

summarySheet.getRange("A1:H1").merge();
summarySheet.getRange("A1").values = [["RQ2 LNWC baseline test — provisional"]];
summarySheet.getRange("A1:H1").format = {
  fill: titleFill,
  font: { bold: true, color: "#FFFFFF", size: 16 },
  rowHeight: 30,
  verticalAlignment: "center",
};

summarySheet.getRange("A3:B8").values = [
  ["Parameter", "Value"],
  ["Rail K", summary.parameters.rail_k],
  ["Bus K", summary.parameters.bus_k],
  ["Rail catchment (m)", summary.parameters.rail_catchment_metres],
  ["Permutations", summary.parameters.permutations],
  ["Random seed", summary.parameters.random_seed],
];
summarySheet.getRange("A3:B3").format = {
  fill: headerFill,
  font: { bold: true },
  borders: { preset: "doubleBottom", style: "thin", color: "#7F8C8D" },
};

summarySheet.getRange("D3:F9").values = [
  ["Coverage metric", "Value", "Interpretation"],
  ["Bus matched rows", summary.coverage.bus.matched_lnwc_rows, "Direct LSOA join"],
  ["Bus match rate", summary.coverage.bus.match_rate, "Share of provisional bus units"],
  [
    "Rail stations",
    summary.coverage.rail.stations_eligible_for_lnwc_analysis,
    "Station point inside LNWC extent with seven-part composition",
  ],
  [
    "Rail stations outside extent",
    summary.coverage.rail.stations_outside_lnwc_extent,
    "Retained in audit; excluded from association estimates",
  ],
  [
    "Mean rail coverage",
    summary.coverage.rail.mean_lnwc_coverage_ratio,
    "Catchment area represented by LNWC LSOAs",
  ],
  [
    "Minimum rail coverage",
    summary.coverage.rail.minimum_lnwc_coverage_ratio,
    "Lowest station catchment coverage",
  ],
];
summarySheet.getRange("D3:F3").format = {
  fill: headerFill,
  font: { bold: true },
  borders: { preset: "doubleBottom", style: "thin", color: "#7F8C8D" },
};
summarySheet.getRange("E5").format.numberFormat = "0.0%";
summarySheet.getRange("E6").format.numberFormat = "0";
summarySheet.getRange("E7").format.numberFormat = "0";
summarySheet.getRange("E8:E9").format.numberFormat = "0.0%";

summarySheet.getRange("A11:H11").merge();
summarySheet.getRange("A11").values = [["Interpretation boundary"]];
summarySheet.getRange("A11:H11").format = {
  fill: subFill,
  font: { bold: true, color: titleFill },
};
summarySheet.getRange("A12:H14").merge();
summarySheet.getRange("A12").values = [[
  "These outputs describe associations between provisional RQ1 transport-use clusters and area-level LNWC context. They do not identify individual passengers or their occupations. Chi-square results are exploratory because neighbouring LSOAs are spatially dependent.",
]];
summarySheet.getRange("A12:H14").format = {
  wrapText: true,
  verticalAlignment: "top",
  fill: "#FAFAFA",
  borders: { preset: "outside", style: "thin", color: "#D0D0D0" },
};

summarySheet.getRange("A17:D21").values = [
  ["Exploratory statistic", "Effect size", "p-value", "Caution"],
  [
    "Bus cluster × LNWC",
    summary.statistics.bus.cramers_v,
    summary.statistics.bus.p_value,
    "Spatial autocorrelation not modelled",
  ],
  [
    "Rail cluster × dominant LNWC",
    summary.statistics.rail_dominant.cramers_v,
    summary.statistics.rail_dominant.p_value,
    "Dominant type discards mixture",
  ],
  [
    "Rail seven-part composition",
    summary.statistics.rail_composition_permutation.r_squared,
    summary.statistics.rail_composition_permutation.permutation_p,
    "Euclidean exploratory permutation",
  ],
  ["Status", "ANALYZED", null, "Not a final RQ2 result"],
];
summarySheet.getRange("A17:D17").format = {
  fill: headerFill,
  font: { bold: true },
  borders: { preset: "doubleBottom", style: "thin", color: "#7F8C8D" },
};
summarySheet.getRange("B18:B20").format.numberFormat = "0.000";
summarySheet.getRange("C18:C20").format.numberFormat = "0.000E+00";
summarySheet.getRange("A21:D21").format = {
  fill: "#FFF2CC",
  font: { bold: true, color: "#7F6000" },
};

const tableSpecs = [
  ["Data Audit", "data_audit.csv"],
  ["LNWC Lookup", "lnwc_group_lookup.csv"],
  ["Bus Counts", "bus_crosstab_counts.csv"],
  ["Bus Row Pct", "bus_crosstab_row_pct.csv"],
  ["Bus Enrichment", "bus_enrichment.csv"],
  ["Bus Residuals", "bus_standardized_residuals.csv"],
  ["Rail Equal Comp", "rail_lnwc_composition_equal_weight.csv"],
  ["Rail Activity Comp", "rail_lnwc_composition_activity_weighted.csv"],
  ["Rail Enrichment", "rail_enrichment.csv"],
  ["Rail Cluster Summary", "rail_cluster_summary.csv"],
  ["Statistics", "statistical_summary.csv"],
  ["Rail Stations", "rail_analysis_station.csv"],
  ["Bus LSOAs", "bus_analysis_lsoa.csv"],
];

for (const [sheetName, fileName] of tableSpecs) {
  const csvText = await fs.readFile(path.join(dataDir, fileName), "utf8");
  const temporaryWorkbook = await Workbook.fromCSV(csvText, { sheetName });
  const temporarySheet = temporaryWorkbook.worksheets.getItem(sheetName);
  const values = temporarySheet.getUsedRange(true).values;
  const sheet = workbook.worksheets.add(sheetName);
  const target = sheet.getRangeByIndexes(0, 0, values.length, values[0].length);
  target.values = values;
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  sheet.getRangeByIndexes(0, 0, 1, values[0].length).format = {
    fill: titleFill,
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    borders: { preset: "doubleBottom", style: "thin", color: "#C8B6D8" },
  };
  target.format.autofitColumns();
  target.format.autofitRows();
  target.format.rowHeight = 18;
  sheet.getRangeByIndexes(0, 0, 1, values[0].length).format.rowHeight = 30;

  if (sheetName.includes("Enrichment") && values.length > 1 && values[0].length > 1) {
    const numeric = sheet.getRangeByIndexes(1, 1, values.length - 1, values[0].length - 1);
    numeric.format.numberFormat = "0.00";
    numeric.conditionalFormats.add("colorScale", {
      colors: ["#4575B4", "#FFFFBF", "#D73027"],
      thresholds: [
        { type: "min" },
        { type: "number", value: 1 },
        { type: "max" },
      ],
    });
  }
  if (sheetName.includes("Comp") || sheetName.includes("Pct")) {
    if (values.length > 1 && values[0].length > 1) {
      sheet
        .getRangeByIndexes(1, 1, values.length - 1, values[0].length - 1)
        .format.numberFormat = "0.0%";
    }
  }
}

summarySheet.freezePanes.freezeRows(1);
summarySheet.getRange("A1:H21").format.font.name = "Aptos";
summarySheet.getRange("A1:H21").format.autofitColumns();
summarySheet.getRange("A1:H21").format.autofitRows();
summarySheet.getRange("A:A").format.columnWidth = 27;
summarySheet.getRange("B:B").format.columnWidth = 18;
summarySheet.getRange("D:D").format.columnWidth = 28;
summarySheet.getRange("F:F").format.columnWidth = 42;
summarySheet.getRange("H:H").format.columnWidth = 4;

const inspection = await workbook.inspect({
  kind: "table",
  range: "Summary!A1:H21",
  include: "values,formulas",
  tableMaxRows: 25,
  tableMaxCols: 10,
});
console.log(inspection.ndjson);

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(formulaErrors.ndjson);

for (const [sheetName, range, fileName] of [
  ["Summary", "A1:H21", "workbook_preview_summary.png"],
  ["Bus Enrichment", "A1:H6", "workbook_preview_bus_enrichment.png"],
  ["Rail Enrichment", "A1:H8", "workbook_preview_rail_enrichment.png"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1.5, format: "png" });
  await fs.writeFile(
    path.join(workbookDir, fileName),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(workbookDir, "rq2_lnwc_baseline_results.xlsx");
await output.save(outputPath);
console.log(`Workbook written: ${outputPath}`);
