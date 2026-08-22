# RQ2 LNWC baseline reproducibility check

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-07-02
- Verification Status: VERIFIED
- Version Label: rq2_lnwc_baseline_reproducibility_v1

## Method

The current `src/run_analysis.py` pipeline was run twice without changing code,
configuration, or inputs. SHA-256 hashes were compared for four core analytical
outputs.

| Output | Match | SHA-256 |
|---|---:|---|
| `bus_enrichment.csv` | Yes | `E0741A3A97621D68564687B6B6C3F6718B2D270C5C450D3CE1C12B8948B0C541` |
| `rail_enrichment.csv` | Yes | `ACEB2559C6DF74C45D72EB0CBB467E38C140EA6185085E2EBF37554E95A66734` |
| `rail_analysis_station.csv` | Yes | `F7BFAD901B7846E19137F7409398332467684E320C30B2CAAB769C9F3B4DB7A4` |
| `statistical_summary.csv` | Yes | `88FA14F5D82CF507A5F6DB57B678CF74C1BFEF047AAAEDE4BCB31D6967732D7E` |

## Verdict

The checked deterministic core outputs are reproducible in the current
environment. This verifies execution consistency, not the substantive validity
of the provisional K choices, catchment definition, or inferential assumptions.
