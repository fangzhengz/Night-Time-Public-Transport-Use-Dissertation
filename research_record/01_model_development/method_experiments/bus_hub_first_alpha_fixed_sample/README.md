# Fixed-sample alpha sensitivity

Once hub-first processing had fixed the spatial units, a narrower question remained: were the resulting labels mainly a consequence of the smoothing strength? Holding all 3,593 LSOAs and every GMM setting fixed allowed alpha=0 and alpha=5 to be compared without mixing smoothing with coverage or geography. This is the focused counterpart to the wider alpha-grid screen.

This side-by-side experiment compares alpha=0 and alpha=5 on exactly the same
3,593 hub-first LSOAs retained by `rq1_bus_hub_first_reclustering`.

It rebuilds the raw full-week, per-direction 72-column shares with alpha=0,
reruns the complete covariance x K BIC grid, and then compares full-covariance
labels and 20-resample stability with the alpha=5 run.

Run:

```powershell
python -u src\run_alpha_sensitivity.py --bootstrap 20
```

Main output: `outputs/report/ALPHA_SENSITIVITY_RESULTS.md`.
