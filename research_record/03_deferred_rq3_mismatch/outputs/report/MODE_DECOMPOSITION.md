# RQ3 mode decomposition: is the mismatch a bus story, a rail story, or both?

Reuses the totals already computed by build_msoa_panels.py -- no new aggregation. Fits rail and bus separately against the same OD totals used in the combined model.

- Rail is present in 279/979 MSOAs (most MSOAs have no Underground station); bus is present in 979/979. The two mode-specific models below are fit on different, non-nested MSOA subsets and are not directly comparable in coverage -- read R² and residual patterns with that in mind.

- **origin / rail**: `log1p(rail_entry_total) ~ log1p(od_origin_total)`, R²=0.397, slope=0.882, n=279.
- **origin / bus**: `log1p(bus_boarding_total) ~ log1p(od_origin_total)`, R²=0.593, slope=1.034, n=979.
- **destination / rail**: `log1p(rail_exit_total) ~ log1p(od_destination_total)`, R²=0.355, slope=0.681, n=279.
- **destination / bus**: `log1p(bus_alighting_total) ~ log1p(od_destination_total)`, R²=0.483, slope=0.956, n=979.

## Where rail is present: does rail or bus track the combined-model gap better?

- **origin** (n=279 MSOAs with both modes present): combined-model residual correlates r=0.87 with the rail-only residual, r=0.52 with the bus-only residual.
- **destination** (n=279 MSOAs with both modes present): combined-model residual correlates r=0.84 with the rail-only residual, r=0.46 with the bus-only residual.