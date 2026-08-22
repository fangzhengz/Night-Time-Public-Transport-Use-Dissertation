# -*- coding: utf-8 -*-
"""Run the exact isolated-test plotting code with corrected presentation labels."""
from _reference_runner import run_reference


if __name__ == "__main__":
    run_reference(
        "04_figures.py",
        {
            "hub-first isolated": "StopArea-only isolated",
            "hub-first-only": "StopArea-only",
        },
    )
