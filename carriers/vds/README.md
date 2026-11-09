# VDS pilot reconstruction

Run only inside Workbench after restoring external roster TSV and approved pilot targets. `01_roster_check` reads columns only. `02_variant_access` maps target keys to original global ALT indices using minimal representation. `03_sparse_carrier_qc` describes carriers and GQ/FT. `04_reference_call_pilot` checks dense call partitions and sparse agreement.

Hail 0.2.135 was used historically. These reconstructed scripts have not been executed on Hail/VDS during export. Required pilot target keys are withheld. Default pilot-size limit prevents accidental full-panel use; it is not a scalable extraction pipeline. Intervals are filtered with reference-block metadata before dense conversion. Missing calls remain missing. No final QC pass/exclude policy was adopted.
