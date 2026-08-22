# Bus 05:00 cutoff sensitivity

The final Bus analysis uses an 18:00–05:00 night window, but this boundary was reached after earlier preprocessing extended to 06:00. This side branch was created to isolate that temporal decision and determine which inputs and downstream stages would need to change if the last hour were removed.

The folder contains the available preprocessing and clustering code fragments recovered from the local workspace. No complete, internally verified result report was found, so it is retained as a **planned or partial sensitivity**, not as evidence that the 05:00 and 06:00 solutions were empirically equivalent.

Its value is procedural: it documents that the cutoff was recognised as a testable assumption and prevents the surviving code from being mistaken for a completed robustness result. Any future rerun must first reconnect the scripts to authorised BUSTO inputs, verify the 18:00–05:00 extraction and use a separate output directory.
