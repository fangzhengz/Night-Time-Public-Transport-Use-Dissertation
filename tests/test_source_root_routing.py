from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


class SourceRootRoutingTests(unittest.TestCase):
    def test_pipeline_default_is_repository_relative(self) -> None:
        pipeline = load_module("pipeline_for_source_test", "scripts/run_pipeline.py")
        self.assertEqual(pipeline.DEFAULT_SOURCE_ROOT, ROOT / "authorised_data")
        environment = pipeline.build_stage_environment(ROOT / "portable_inputs")
        self.assertEqual(
            Path(environment["CASA_FYP_SOURCE_ROOT"]),
            (ROOT / "portable_inputs").resolve(),
        )

    def test_active_raw_inputs_follow_environment_override(self) -> None:
        source_root = (ROOT / "_portable_source_test").resolve()
        with (
            patch.dict(os.environ, {"CASA_FYP_SOURCE_ROOT": str(source_root)}),
            patch("pathlib.Path.mkdir"),
        ):
            modules_and_paths = [
                (
                    "bus_raw_for_source_test",
                    "analysis/01_data_preparation/bus/src/preprocess_busto.py",
                    ["DEFAULT_INPUT_DIR"],
                ),
                (
                    "bus_prep_for_source_test",
                    "analysis/01_data_preparation/bus/src/build_stoparea_data.py",
                    ["NAPTAN_DIR", "BUS_STOPS_CSV", "LSOA_GEOJSON"],
                ),
                (
                    "rail_prep_for_source_test",
                    "analysis/01_data_preparation/rail/src/01_preprocess_rail_allmodes.py",
                    ["RAIL_DATA_DIR"],
                ),
                (
                    "rail_coords_for_source_test",
                    "analysis/01_data_preparation/rail/src/01c_match_naptan_coords.py",
                    ["NAPTAN_PATH", "UNDERGROUND_STATIONS_CSV"],
                ),
                (
                    "bus_config_for_source_test",
                    "analysis/02_mode_specific_clustering/bus/src/config.py",
                    ["LSOA_GEOJSON", "LSOA_LAD_LOOKUP"],
                ),
                (
                    "lnwc_config_for_source_test",
                    "analysis/03_lnwc_context/src/config.py",
                    ["LNWC", "LNWC_PORTRAITS", "LSOA_BOUNDARIES", "IMD_LSOA21"],
                ),
            ]
            for module_name, relative_path, attributes in modules_and_paths:
                module = load_module(module_name, relative_path)
                self.assertEqual(module.SOURCE_ROOT, source_root)
                for attribute in attributes:
                    self.assertTrue(
                        Path(getattr(module, attribute)).is_relative_to(source_root),
                        f"{relative_path}:{attribute} does not use the authorised source root",
                    )

    def test_adopted_input_interface_uses_ascii_directory_names(self) -> None:
        checked_files = [
            "authorised_data/README.md",
            "scripts/run_pipeline.py",
            "analysis/01_data_preparation/bus/src/preprocess_busto.py",
            "analysis/01_data_preparation/bus/src/build_stoparea_data.py",
            "analysis/01_data_preparation/rail/src/01_preprocess_rail_allmodes.py",
            "analysis/01_data_preparation/rail/src/01c_match_naptan_coords.py",
        ]
        superseded_directory_names = [
            "\u5df4\u58eb\u6570\u636e",
            "\u5730\u94c1\u8fdb\u51fa\u7ad9\u6570\u636e",
            "\u5730\u94c1\u8f66\u7ad9\u7a7a\u95f4\u6570\u636e",
        ]
        for relative_path in checked_files:
            source = (ROOT / relative_path).read_text(encoding="utf-8-sig")
            for directory_name in superseded_directory_names:
                self.assertNotIn(
                    directory_name,
                    source,
                    f"Superseded directory name remains in {relative_path}",
                )

        pipeline = load_module("pipeline_for_ascii_test", "scripts/run_pipeline.py")
        for required_input in pipeline.REQUIRED_INPUTS:
            self.assertTrue(
                all(part.isascii() for part in Path(required_input).parts),
                f"Non-ASCII path component in required input: {required_input}",
            )
        self.assertIn("bus_data/Bus_Stops.csv", pipeline.REQUIRED_INPUTS)
        self.assertIn("rail_data", pipeline.REQUIRED_INPUTS)
        self.assertIn(
            "rail_station_spatial_data/Underground_Stations.csv", pipeline.REQUIRED_INPUTS
        )

    def test_remaining_raw_routes_are_source_rooted(self) -> None:
        expected_snippets = {
            "analysis/02_mode_specific_clustering/rail/src/06_profiles_and_maps_allmodes.py": [
                'LSOA_GEOJSON = SOURCE_ROOT / "map"',
            ],
            "analysis/04_urban_context/src/config.py": [
                'SOURCE_ROOT / "IMDdata_2025"',
                'LSOA_BOUNDARIES = SOURCE_ROOT / "map"',
                'OS_POI = SOURCE_ROOT / "data" / "raw" / "os_poi"',
            ],
            "analysis/05_reporting/build_final_figures.py": [
                'BOUNDARY = SOURCE_ROOT / "map"',
            ],
        }
        for relative_path, snippets in expected_snippets.items():
            source = (ROOT / relative_path).read_text(encoding="utf-8-sig")
            for snippet in snippets:
                self.assertIn(snippet, source, f"Missing source-root route in {relative_path}")


if __name__ == "__main__":
    unittest.main()
