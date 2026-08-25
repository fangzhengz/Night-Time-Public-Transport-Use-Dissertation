# Reproducibility levels

## Level 1: frozen-evidence verification

Available to every clone. It checks the submitted PDF hash, analysis sample sizes, cluster counts, model choices, LNWC statistics, the 20-variable test coverage, and the absence of retired specifications from active result tables.

```bash
python scripts/validate_repository.py
python -m unittest discover -s tests -v
```

## Level 2: aggregate reporting rebuild

Available to every clone using committed aggregate tables.

```bash
python analysis/05_reporting/make_behavioural_figures.py
```

This reconstructs the formal behavioural panels from the current signature matrices in `results/recomputed_figures/`. It does not require passenger-level or provider-restricted data and does not overwrite the figures embedded in the submitted dissertation.

## Level 3: full raw-data rebuild

Requires authorised local copies of NUMBAT, BUSTO, NaPTAN, boundaries, LNWC, deprivation, Census and OS POI inputs. The full run writes intermediates inside the clone, promotes adopted tables and diagnostics to `results/`, places rebuilt figures in `results/recomputed_figures/`, and does not overwrite the source workspace, submitted PDF or paper-matched figures.

By default, raw inputs are read from the repository-relative
`authorised_data/` directory described in
[`authorised_data/README.md`](../authorised_data/README.md). No drive letter is
embedded in the code. A different location can be selected with
`--source-root`; that resolved path is passed to every adopted stage.

```bash
python scripts/run_pipeline.py --dry-run
python scripts/run_pipeline.py --full
python scripts/validate_repository.py
```

For an external authorised-data directory:

```bash
python scripts/run_pipeline.py --dry-run --source-root "/path/to/authorised_data"
python scripts/run_pipeline.py --full --source-root "/path/to/authorised_data"
```

The complete rerun is intentionally separated from GitHub distribution because reproducibility does not imply permission to republish restricted source data.
