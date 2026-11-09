#!/usr/bin/env bash
# RepeatMasker intervals (BP3). --name repeatmasker is load-bearing: the classifier finds the track by a key
# containing "repeat"; any other name loads and is then ignored.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
# Reconstruction, not an authenticated export of the historical commands.
: "${ALLOW_UNVERIFIED_FASTVEP:?Review pinned sources/helper compatibility first}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")" "$SCRATCH_DIR"
exec >>"$PIPELINE_LOG" 2>&1
cd "$FV/sa_sources"
curl --fail -L -o rmsk.txt.gz "$REPEATMASKER_URL"
python3 "$FVEP_REPO/analysis/acmg_benchmark/scripts/sa_sources/repeatmasker_to_bed.py" rmsk.txt.gz > repeatmasker.bed
"$FVEP_BIN" sa-build --source custom_bed --name repeatmasker -i repeatmasker.bed -o ../sa_databases/repeatmasker --assembly GRCh38
