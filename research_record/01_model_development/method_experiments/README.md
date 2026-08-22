# Method experiments: learning what each decision changed

Many early revisions altered several assumptions at once. The experiments collected here were created to separate them: spatial aggregation from filtering, filtering from compositional transformation, smoothing from reliability, and common time windows from normalisation closure. Some produced useful validations, some failed their own adoption gates, and some showed that an initially promising change introduced a different weakness.

Together they explain why the final pipeline is deliberately conservative. The adopted choices are not presented as universally optimal; they are the combination that remained interpretable after the project's main data-quality and stability concerns were tested. Each subfolder retains the sample and modelling conditions of its own moment in the project.

The sequence now includes the early grouped day-regime model; the 15-minute versus one-hour comparison; hub-zero, hub-first and StopArea-only spatial-unit tests; fixed-sample and grid-based smoothing checks; Bus Hellinger and Rail ILR sensitivities; historical K validation; and the provisional context-metric layer. Several of these are negative or superseded results, but that is precisely why they matter to the research record.
