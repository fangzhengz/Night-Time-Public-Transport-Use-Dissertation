# -*- coding: utf-8 -*-
"""Execute the hub-first isolated test's downstream source with rebound paths."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import config as C

REFERENCE_SRC = C.FYP / "rq1_bus_hub_first_isolated_test" / "src"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load reference module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rebound_reference_config():
    ref = _load_module("stoparea_reference_config", REFERENCE_SRC / "config.py")
    ref.ROOT = C.ROOT
    ref.OUT = C.OUT
    ref.FEAT = C.FEAT
    ref.DIAG = C.DIAG
    ref.FIG = C.FIG
    ref.LAB = C.LAB
    ref.REPORT = C.REPORT
    ref.BUS_LONG = C.BUS_LONG
    ref.LSOA_GEOJSON = C.LSOA_GEOJSON
    for directory in (ref.OUT, ref.FEAT, ref.DIAG, ref.FIG, ref.LAB, ref.REPORT):
        directory.mkdir(parents=True, exist_ok=True)
    return ref


def run_reference(script_name: str, replacements: dict[str, str] | None = None) -> None:
    ref_config = rebound_reference_config()
    sys.modules["config"] = ref_config
    path = REFERENCE_SRC / script_name
    if not replacements:
        module = _load_module(f"stoparea_reference_{path.stem}", path)
        module.main()
        return

    source = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        source = source.replace(old, new)
    namespace = {"__name__": "__main__", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), namespace)
