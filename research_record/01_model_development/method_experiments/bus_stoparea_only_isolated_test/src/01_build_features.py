# -*- coding: utf-8 -*-
"""Run the exact hub-first isolated feature code on StopArea-only input."""
from _reference_runner import run_reference


if __name__ == "__main__":
    run_reference(
        "01_build_features.py",
        {"hub-first input": "StopArea-only input"},
    )
