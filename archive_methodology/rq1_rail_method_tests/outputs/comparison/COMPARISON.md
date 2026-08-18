# Rail: day-type vs full-week closure, native vs padded window

Sidecar result, 2026-08-01. Not an adopted result.

## Anchor

`fullweek_unpadded` reproduces the adopted matrix exactly (max abs diff 0.0 in 01) and reproduces its labels at K=5 (`ari_vs_canon_k5` = 1.000) and its stability numbers (seed ARI 0.894 at K=5, 0.703 at K=7, 0.624 at K=6). The 2x2 therefore measures against the real pipeline.

## BIC behaviour

| variant           |   bic_best_K |   runner_up_K |   margin_over_runner_up |   spread_of_best_5 |
|:------------------|-------------:|--------------:|------------------------:|-------------------:|
| fullweek_unpadded |            5 |             8 |                   256.3 |             1721.5 |
| daytype_unpadded  |            9 |             8 |                   253.2 |             2559.6 |
| fullweek_padded   |            5 |             6 |                   595.2 |             2649.5 |
| daytype_padded    |            9 |            10 |                  2199.2 |             2926.3 |

`spread_of_best_5` is the BIC gap between the best and fifth-best K. A small spread means BIC has stopped discriminating and K cannot be read off it -- Clara's standing caveat that BIC must not auto-pick K.

## Full diagnostics

| variant           | closure   | window   |   K |           BIC |   silhouette |   activity_eta2 |   zero_bin_eta2 |   timing_mean_eta2 |   night_tube_extension_share_eta2 |   weekend_common_ratio_eta2 |   min_cluster_n |   seed_ari_mean |   bootstrap_ari_mean |   ari_vs_canon_k5 |
|:------------------|:----------|:---------|----:|--------------:|-------------:|----------------:|----------------:|-------------------:|----------------------------------:|----------------------------:|----------------:|----------------:|---------------------:|------------------:|
| fullweek_unpadded | fullweek  | native   |   4 | -1442874.0107 |       0.1450 |          0.1441 |          0.0189 |             0.1935 |                            0.0791 |                      0.2081 |              15 |          0.9078 |               0.5504 |            0.4170 |
| fullweek_unpadded | fullweek  | native   |   5 | -1446368.8978 |       0.1018 |          0.2351 |          0.1260 |             0.2998 |                            0.1678 |                      0.2164 |              12 |          0.8940 |               0.5001 |            1.0000 |
| fullweek_unpadded | fullweek  | native   |   6 | -1445565.2792 |       0.1039 |          0.2554 |          0.1440 |             0.3429 |                            0.1696 |                      0.3061 |              12 |          0.6242 |               0.4834 |            0.6565 |
| fullweek_unpadded | fullweek  | native   |   7 | -1445623.3968 |       0.1130 |          0.3240 |          0.1508 |             0.3094 |                            0.2019 |                      0.5413 |              11 |          0.7026 |               0.4610 |            0.5811 |
| fullweek_unpadded | fullweek  | native   |   9 | -1444647.3960 |       0.1070 |          0.3204 |          0.2057 |             0.4264 |                            0.2868 |                      0.5657 |              14 |        nan      |             nan      |            0.3665 |
| daytype_unpadded  | daytype   | native   |   4 | -1114504.3183 |       0.0294 |          0.1611 |          0.4410 |             0.3560 |                            0.5651 |                      0.1491 |              46 |          0.8927 |               0.7183 |            0.2120 |
| daytype_unpadded  | daytype   | native   |   5 | -1122087.0394 |       0.0351 |          0.2093 |          0.4287 |             0.4402 |                            0.5936 |                      0.1886 |              35 |          0.8828 |               0.6115 |            0.2940 |
| daytype_unpadded  | daytype   | native   |   6 | -1128201.1103 |       0.0264 |          0.2870 |          0.5362 |             0.4493 |                            0.7028 |                      0.1589 |              29 |          0.7256 |               0.5503 |            0.2687 |
| daytype_unpadded  | daytype   | native   |   7 | -1129298.3987 |       0.0299 |          0.2445 |          0.4725 |             0.5118 |                            0.6413 |                      0.1854 |              18 |          0.5832 |               0.5764 |            0.2850 |
| daytype_unpadded  | daytype   | native   |   9 | -1131858.0326 |       0.0437 |          0.3657 |          0.6093 |             0.6374 |                            0.7340 |                      0.2254 |              23 |        nan      |             nan      |            0.2173 |
| fullweek_padded   | fullweek  | padded   |   4 | -1901412.8612 |       0.1404 |          0.1473 |          0.0184 |             0.1942 |                            0.0828 |                      0.2048 |              15 |          0.9127 |               0.5406 |            0.4164 |
| fullweek_padded   | fullweek  | padded   |   5 | -1903182.3562 |       0.1095 |          0.2367 |          0.1326 |             0.3057 |                            0.1651 |                      0.2920 |              19 |          0.6968 |               0.5613 |            0.6806 |
| fullweek_padded   | fullweek  | padded   |   6 | -1902587.1754 |       0.0983 |          0.2613 |          0.1401 |             0.3358 |                            0.1817 |                      0.2870 |              13 |          0.6648 |               0.4569 |            0.6367 |
| fullweek_padded   | fullweek  | padded   |   7 | -1900532.8092 |       0.1133 |          0.2874 |          0.2043 |             0.3151 |                            0.2191 |                      0.5434 |              14 |          0.5707 |               0.5203 |            0.6774 |
| fullweek_padded   | fullweek  | padded   |   9 | -1898577.2709 |       0.0975 |          0.3239 |          0.1774 |             0.4305 |                            0.2877 |                      0.5061 |              16 |        nan      |             nan      |            0.3960 |
| daytype_padded    | daytype   | padded   |   4 | -1559717.6133 |       0.0175 |          0.0829 |          0.4181 |             0.3834 |                            0.5844 |                      0.1111 |              60 |          0.7888 |               0.6624 |            0.2118 |
| daytype_padded    | daytype   | padded   |   5 | -1567649.2467 |       0.0410 |          0.2008 |          0.4301 |             0.4377 |                            0.6093 |                      0.1661 |              32 |          0.9411 |               0.5808 |            0.3220 |
| daytype_padded    | daytype   | padded   |   6 | -1573520.3842 |       0.0141 |          0.2592 |          0.5454 |             0.4221 |                            0.7741 |                      0.1864 |              32 |          0.5649 |               0.4227 |            0.2051 |
| daytype_padded    | daytype   | padded   |   7 | -1573749.0135 |       0.0255 |          0.3060 |          0.5337 |             0.5189 |                            0.6611 |                      0.1834 |              26 |          0.5464 |               0.4641 |            0.1962 |
| daytype_padded    | daytype   | padded   |   9 | -1576446.6528 |       0.0431 |          0.3502 |          0.6133 |             0.6304 |                            0.7372 |                      0.2250 |              23 |        nan      |             nan      |            0.2085 |

## Closure effect at K=5, window held at native

|                                 |   fullweek |   daytype |   delta |
|:--------------------------------|-----------:|----------:|--------:|
| silhouette                      |     0.1018 |    0.0351 | -0.0667 |
| activity_eta2                   |     0.2351 |    0.2093 | -0.0259 |
| zero_bin_eta2                   |     0.1260 |    0.4287 |  0.3028 |
| timing_mean_eta2                |     0.2998 |    0.4402 |  0.1404 |
| night_tube_extension_share_eta2 |     0.1678 |    0.5936 |  0.4258 |
| weekend_common_ratio_eta2       |     0.2164 |    0.1886 | -0.0278 |
| min_cluster_n                   |    12.0000 |   35.0000 | 23.0000 |
| seed_ari_mean                   |     0.8940 |    0.8828 | -0.0112 |
| bootstrap_ari_mean              |     0.5001 |    0.6115 |  0.1115 |
| ari_vs_canon_k5                 |     1.0000 |    0.2940 | -0.7060 |

## Closure effect at K=5, window held at padded

|                                 |   fullweek |   daytype |   delta |
|:--------------------------------|-----------:|----------:|--------:|
| silhouette                      |     0.1095 |    0.0410 | -0.0685 |
| activity_eta2                   |     0.2367 |    0.2008 | -0.0358 |
| zero_bin_eta2                   |     0.1326 |    0.4301 |  0.2975 |
| timing_mean_eta2                |     0.3057 |    0.4377 |  0.1320 |
| night_tube_extension_share_eta2 |     0.1651 |    0.6093 |  0.4442 |
| weekend_common_ratio_eta2       |     0.2920 |    0.1661 | -0.1259 |
| min_cluster_n                   |    19.0000 |   32.0000 | 13.0000 |
| seed_ari_mean                   |     0.6968 |    0.9411 |  0.2444 |
| bootstrap_ari_mean              |     0.5613 |    0.5808 |  0.0194 |
| ari_vs_canon_k5                 |     0.6806 |    0.3220 | -0.3586 |

## Closure effect at K=9, window held at native

|                                 |   fullweek |   daytype |    delta |
|:--------------------------------|-----------:|----------:|---------:|
| silhouette                      |     0.1070 |    0.0437 |  -0.0632 |
| activity_eta2                   |     0.3204 |    0.3657 |   0.0453 |
| zero_bin_eta2                   |     0.2057 |    0.6093 |   0.4036 |
| timing_mean_eta2                |     0.4264 |    0.6374 |   0.2110 |
| night_tube_extension_share_eta2 |     0.2868 |    0.7340 |   0.4472 |
| weekend_common_ratio_eta2       |     0.5657 |    0.2254 |  -0.3403 |
| min_cluster_n                   |    14.0000 |   23.0000 |   9.0000 |
| seed_ari_mean                   |   nan      |  nan      | nan      |
| bootstrap_ari_mean              |   nan      |  nan      | nan      |
| ari_vs_canon_k5                 |     0.3665 |    0.2173 |  -0.1493 |

## Closure effect at K=9, window held at padded

|                                 |   fullweek |   daytype |    delta |
|:--------------------------------|-----------:|----------:|---------:|
| silhouette                      |     0.0975 |    0.0431 |  -0.0544 |
| activity_eta2                   |     0.3239 |    0.3502 |   0.0263 |
| zero_bin_eta2                   |     0.1774 |    0.6133 |   0.4359 |
| timing_mean_eta2                |     0.4305 |    0.6304 |   0.2000 |
| night_tube_extension_share_eta2 |     0.2877 |    0.7372 |   0.4495 |
| weekend_common_ratio_eta2       |     0.5061 |    0.2250 |  -0.2811 |
| min_cluster_n                   |    16.0000 |   23.0000 |   7.0000 |
| seed_ari_mean                   |   nan      |  nan      | nan      |
| bootstrap_ari_mean              |   nan      |  nan      | nan      |
| ari_vs_canon_k5                 |     0.3960 |    0.2085 |  -0.1876 |

## Padding effect at K=5, closure held at fullweek

|                                 |   native |   padded |   delta |
|:--------------------------------|---------:|---------:|--------:|
| silhouette                      |   0.1018 |   0.1095 |  0.0077 |
| activity_eta2                   |   0.2351 |   0.2367 |  0.0015 |
| zero_bin_eta2                   |   0.1260 |   0.1326 |  0.0066 |
| timing_mean_eta2                |   0.2998 |   0.3057 |  0.0059 |
| night_tube_extension_share_eta2 |   0.1678 |   0.1651 | -0.0027 |
| weekend_common_ratio_eta2       |   0.2164 |   0.2920 |  0.0756 |
| min_cluster_n                   |  12.0000 |  19.0000 |  7.0000 |
| seed_ari_mean                   |   0.8940 |   0.6968 | -0.1972 |
| bootstrap_ari_mean              |   0.5001 |   0.5613 |  0.0613 |
| ari_vs_canon_k5                 |   1.0000 |   0.6806 | -0.3194 |

## Padding effect at K=5, closure held at daytype

|                                 |   native |   padded |   delta |
|:--------------------------------|---------:|---------:|--------:|
| silhouette                      |   0.0351 |   0.0410 |  0.0059 |
| activity_eta2                   |   0.2093 |   0.2008 | -0.0084 |
| zero_bin_eta2                   |   0.4287 |   0.4301 |  0.0013 |
| timing_mean_eta2                |   0.4402 |   0.4377 | -0.0025 |
| night_tube_extension_share_eta2 |   0.5936 |   0.6093 |  0.0157 |
| weekend_common_ratio_eta2       |   0.1886 |   0.1661 | -0.0225 |
| min_cluster_n                   |  35.0000 |  32.0000 | -3.0000 |
| seed_ari_mean                   |   0.8828 |   0.9411 |  0.0583 |
| bootstrap_ari_mean              |   0.6115 |   0.5808 | -0.0308 |
| ari_vs_canon_k5                 |   0.2940 |   0.3220 |  0.0280 |

## Padding effect at K=9, closure held at fullweek

|                                 |   native |   padded |    delta |
|:--------------------------------|---------:|---------:|---------:|
| silhouette                      |   0.1070 |   0.0975 |  -0.0095 |
| activity_eta2                   |   0.3204 |   0.3239 |   0.0035 |
| zero_bin_eta2                   |   0.2057 |   0.1774 |  -0.0282 |
| timing_mean_eta2                |   0.4264 |   0.4305 |   0.0041 |
| night_tube_extension_share_eta2 |   0.2868 |   0.2877 |   0.0008 |
| weekend_common_ratio_eta2       |   0.5657 |   0.5061 |  -0.0596 |
| min_cluster_n                   |  14.0000 |  16.0000 |   2.0000 |
| seed_ari_mean                   | nan      | nan      | nan      |
| bootstrap_ari_mean              | nan      | nan      | nan      |
| ari_vs_canon_k5                 |   0.3665 |   0.3960 |   0.0295 |

## Padding effect at K=9, closure held at daytype

|                                 |   native |   padded |    delta |
|:--------------------------------|---------:|---------:|---------:|
| silhouette                      |   0.0437 |   0.0431 |  -0.0006 |
| activity_eta2                   |   0.3657 |   0.3502 |  -0.0155 |
| zero_bin_eta2                   |   0.6093 |   0.6133 |   0.0040 |
| timing_mean_eta2                |   0.6374 |   0.6304 |  -0.0069 |
| night_tube_extension_share_eta2 |   0.7340 |   0.7372 |   0.0032 |
| weekend_common_ratio_eta2       |   0.2254 |   0.2250 |  -0.0004 |
| min_cluster_n                   |  23.0000 |  23.0000 |   0.0000 |
| seed_ari_mean                   | nan      | nan      | nan      |
| bootstrap_ari_mean              | nan      | nan      | nan      |
| ari_vs_canon_k5                 |   0.2173 |   0.2085 |  -0.0088 |
