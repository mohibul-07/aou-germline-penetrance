#!/usr/bin/env bash
# REVEL v1.3 (PP3/BP4 missense), built PER CHROMOSOME.
# Building from the single 6.5 GB CSV hung on a 50 GB node; splitting bounds peak memory (same result).
# Download: 667 MB zip -> 6.5 GB CSV (header: chr,hg19_pos,grch38_pos,ref,alt,aaref,aaalt,REVEL,Ensembl_transcriptid).
# Back up revel_with_transcript_ids to GCS to avoid re-downloading.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
# Reconstruction, not an authenticated export of the historical commands.
: "${ALLOW_UNVERIFIED_FASTVEP:?Review pinned sources/helper compatibility first}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")" "$SCRATCH_DIR"
exec >>"$PIPELINE_LOG" 2>&1
cd "$FV/sa_sources"

if [[ ! -f revel_with_transcript_ids ]]; then
  curl --fail -L -o revel-v1.3_all_chromosomes.zip "$REVEL_URL"
  unzip revel-v1.3_all_chromosomes.zip && rm revel-v1.3_all_chromosomes.zip
fi

for chr in $PANEL_CHROMS; do
  [[ -f "../sa_databases/revel_chr${chr}.osa2" ]] && { echo "chr${chr} exists, skip"; continue; }
  head -1 revel_with_transcript_ids > "revel_chr${chr}.csv"
  grep "^${chr}," revel_with_transcript_ids >> "revel_chr${chr}.csv"   # each grep scans the full 6.5 GB file (~1-2 min)
  "$FVEP_BIN" sa-build --source revel -i "revel_chr${chr}.csv" -o "../sa_databases/revel_chr${chr}" --assembly GRCh38
  rm -f "revel_chr${chr}.csv"
done
