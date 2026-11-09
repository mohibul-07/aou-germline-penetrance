#!/usr/bin/env bash
# SpliceAI and PhyloP, distilled from the same gnomAD v4.1 regions (no Illumina account, no UCSC download).
# Notes from ACMG_SETUP.md:
#  - gnomAD stores only spliceai_ds_max; it is written into all four DS fields. Every ACMG consumer reads
#    max_delta_score(), so classification is unaffected. DP position fields are placeholders (0).
#  - gnomAD phyloP is the Zoonomia 241-mammal score, not UCSC phyloP100way; fastVEP's phylop_conserved=2.0
#    default was calibrated on Zoonomia.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
# Reconstruction, not an authenticated export of the historical commands.
: "${ALLOW_UNVERIFIED_FASTVEP:?Review pinned sources/helper compatibility first}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")" "$SCRATCH_DIR"
exec >>"$PIPELINE_LOG" 2>&1
test -f "$FVEP_REPO/scripts/extract_gnomad_scores.py"
cd "$FV/sa_sources"

for chr in $PANEL_CHROMS; do
  python3 "$FVEP_REPO/scripts/extract_gnomad_scores.py" --chrom "$chr" --regions "$TARGETS_BED" --out-dir .
  "$FVEP_BIN" sa-build --source spliceai -i "spliceai_chr${chr}.vcf" -o "../sa_databases/spliceai_chr${chr}" --assembly GRCh38
  "$FVEP_BIN" sa-build --source phylop   -i "phylop_chr${chr}.tsv"   -o "../sa_databases/phylop_chr${chr}"   --assembly GRCh38
  rm -f "spliceai_chr${chr}.vcf" "phylop_chr${chr}.tsv"
done
