# Adopted method decisions

This page states the active specification only.

- One night window is used throughout: 18:00–05:00.
- Rail uses 403 physical stations and a diagonal-covariance K=5 GMM.
- Bus uses 3,383 retained LSOAs, CLR-transformed temporal compositions and a full-covariance K=4 GMM.
- The Bus reliability floor is at least 33 estimated boardings and at least 33 estimated alightings across the analysis week.
- Rail contextual values use 800m circular catchments clipped by nearest-station Voronoi cells.
- A Rail station's continuous context is the equal-weight mean across distinct intersecting LSOAs; LNWC composition uses the corresponding seven-part catchment composition.
- Fourteen Rail stations without eligible LNWC-covered catchment context are excluded only from contextual analysis, not from clustering.
- Rail and Bus are analysed separately. Cross-mode synthesis is descriptive.
- Context is used to characterise areas surrounding fixed clusters, not to infer passenger identity, travel purpose, causality or service deficiency.
