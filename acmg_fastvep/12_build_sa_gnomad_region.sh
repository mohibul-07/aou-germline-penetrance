#!/usr/bin/env bash
# gnomAD v4.1 exome sites, REGION-RESTRICTED to the 27-gene panel via tabix.
# Full download is ~200 GB (exomes) / 563 GB (genomes); the panel slices are a few MB per chromosome.
# Use v4.1, not v4.0: v4.1 carries spliceai_ds_max and phylop in INFO, which feed 13_build_sa_spliceai_phylop.sh.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
# Reconstruction, not an authenticated export of the historical commands.
: "${ALLOW_UNVERIFIED_FASTVEP:?Review pinned sources/helper compatibility first}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")" "$SCRATCH_DIR"
exec >>"$PIPELINE_LOG" 2>&1
cd "$FV/sa_sources"
[[ "${TARGETS_COORDINATE_SYSTEM:-}" == bed0 ]] || exit 1
BASE="$GNOMAD_EXOMES_BASE_URL"

for chr in $PANEL_CHROMS; do
  url="${BASE}.chr${chr}.vcf.bgz"
  tabix -H "$url" > "gnomad_chr${chr}.vcf"
  awk -v c="chr${chr}" -v n="${chr}" '$1==c || $1==n {print c":"$2+1"-"$3}' "$TARGETS_BED" \
    | xargs -n 200 tabix "$url" | sort -u -k1,1 -k2,2n -k4,4 -k5,5 >> "gnomad_chr${chr}.vcf"
  bgzip -f "gnomad_chr${chr}.vcf"
  "$FVEP_BIN" sa-build --source gnomad -i "gnomad_chr${chr}.vcf.gz" \
      -o "../sa_databases/gnomad_chr${chr}" --assembly GRCh38
  # keep the slice: 13_build_sa_spliceai_phylop.sh reads the same regions
done
