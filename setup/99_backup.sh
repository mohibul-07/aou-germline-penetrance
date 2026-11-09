#!/usr/bin/env bash
# Back up everything durable to GCS. Run at the end of EVERY session.
# Large reference files are skipped by default (re-download is cheaper than storing them).
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
: "${BACKUP_BUCKET:?Set BACKUP_BUCKET to your workspace bucket (gs://...) first; see config/params.env}"

gsutil -m cp -r "$WS"/notebook "$BACKUP_BUCKET"/
gsutil -m cp -r "$COHORT_DIR"/* "$BACKUP_BUCKET"/01_cohort/
gsutil -m cp -r "$RESULTS_DIR"/* "$BACKUP_BUCKET"/02_results/
gsutil -m rsync -r "$FV/sa_databases" "$BACKUP_BUCKET/fastVEP/sa_databases"
gsutil cp "$FVEP_BIN" "$BACKUP_BUCKET/fastVEP/"
