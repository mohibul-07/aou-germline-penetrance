# Running on the All of Us Researcher Workbench

## Every session
1. `source config/params.env`
2. `setup/00_restore_workspace.sh` (restores from GCS, installs tabix/samtools, re-chmods fastvep)
3. Work in **notebooks** (persist via backup) — terminal history is lost when the cluster is deleted.
4. `setup/99_backup.sh` before closing.

## Compute
- Single-node Dataproc, 50-100 GB disk is enough for this project. Delete clusters when idle.
- Never pull raw `condition_occurrence` for 500K people into pandas — aggregate in BigQuery.
- Pre-filter large TSVs with awk/cut before pandas (an 844K-row VAT extract killed a 50 GB kernel).

## Gotchas we hit
| Symptom | Cause | Fix |
|---|---|---|
| `notebooks/notebooks/...` after restore | `gsutil cp -r src/ dest/` | copy `src/*` |
| files gone after restart | Dataproc local disk wiped | back up to GCS every session |
| `WORKSPACE_CDR` unset | not injected on Dataproc | set in `config/params.env` |
| controlled-tier mount missing | new cluster | recreate cluster or `gsutil -u $GOOGLE_PROJECT` |
| tabix/samtools not found | not on image | `sudo apt-get install -y tabix samtools` |
| conda install permission error | env not writable | use apt / rustup |
| `fastvep: Permission denied` | GCS restore drops +x | `chmod +x` |
| fastVEP loads 0 transcripts | contig mismatch or stripped GFF3 header | `setup/03_make_chr_subsets.sh` |
| everything VUS | missing SA database (silent) | `acmg_fastvep/20_verify_stack.sh` |
| REVEL build hangs | 6.5 GB single file | per-chromosome build |
| joins return 0 rows | variant key formats differ | `carriers/keys.py` |
| person_id column holds 3.3e-05 | `awk -F','` on quoted CSV | `csv.reader` |
| sklearn import fails | numpy ABI on Hail image | statsmodels / scipy |
| singular matrix | sex covariate in sex-specific cancer | drop `sex_male` |
| `has_whole_genome_variant` all 0 (v9) | flag not populated | use VDS/ancestry roster |
| file names differ v8 vs v9 | renamed | `vat_complete.bgz.tsv.gz`, `ancestry_preds.tsv` |

See also the Huang Lab All of Us Research Primer: https://huang-lab.github.io/AOU_research_primer/
