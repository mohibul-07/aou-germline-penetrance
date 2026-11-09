#!/usr/bin/env bash
# Restore the workspace after a Dataproc cluster restart.
# Dataproc local disk is wiped on every restart; everything durable lives in the GCS backup bucket.
#
# Gotcha: `gsutil cp -r src/ dest/` nests a directory (notebooks/notebooks/...).
#         Always copy the CONTENTS: `gsutil -m cp -r src/* dest/`.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
: "${BACKUP_BUCKET:?Set BACKUP_BUCKET to your workspace bucket (gs://...) first; see config/params.env}"

mkdir -p "$WS"
gsutil -m cp -r "$BACKUP_BUCKET"/* "$WS"/

# Command-line tools (not preinstalled on the AoU Dataproc image)
sudo apt-get install -y tabix samtools

# The restored fastVEP binary loses its execute bit
if [[ -f "$FVEP_BIN" ]]; then
  chmod +x "$FVEP_BIN"
  "$FVEP_BIN" --version || echo "Restored binary failed; rebuild with setup/01_install_fastvep.sh"
fi

# Controlled-tier mount sometimes does not appear on a new cluster
ls "$CT_ROOT" >/dev/null 2>&1 \
  && echo "Controlled-tier mount OK" \
  || echo "WARNING: controlled-tier mount missing. Recreate the cluster from the Workbench UI, or use gsutil -u \$GOOGLE_PROJECT gs://vwb-aou-datasets-controlled/v9/..."
