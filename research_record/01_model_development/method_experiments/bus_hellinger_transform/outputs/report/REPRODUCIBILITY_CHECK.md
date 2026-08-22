## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: validate
- Verification Status: VERIFIED
- Version Label: bus_hellinger_selected_reproducibility_v1

# Selected Hellinger solution reproducibility

|   selected_k | covariance   |   same_seed_n_init |   label_ari | labels_exactly_equal   |   bic_absolute_difference | verdict      |
|-------------:|:-------------|-------------------:|------------:|:-----------------------|--------------------------:|:-------------|
|            3 | full         |                 20 |           1 | True                   |                         0 | REPRODUCIBLE |

The selected solution was refitted from the saved Hellinger feature matrix with
the same seed, covariance family, K, n_init, regularisation, and iteration cap.
