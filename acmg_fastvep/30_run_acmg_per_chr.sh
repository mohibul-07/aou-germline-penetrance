#!/usr/bin/env bash
# Run fastVEP ACMG over the panel sites VCF, one chromosome at a time.
# Full-genome run: ~8 min just to load, then slow; per-chromosome: 1.34M variants in ~16 min total.
# Output: tab format per chromosome (ACMG class + criteria parsed downstream).
# Note: tab output does not include the ACMG column in all fastVEP versions; if missing, use
#       --output-format vcf (ACMG and ACMG_CRITERIA in CSQ) which is ~40x smaller than JSON.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
# Reconstruction, not an authenticated export of the historical commands.
: "${ALLOW_UNVERIFIED_FASTVEP:?Review pinned sources/helper compatibility first}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")" "$SCRATCH_DIR"
exec >>"$PIPELINE_LOG" 2>&1
SITES="${1:-$FV/panel_27_sites.vcf}"
FORMAT="${FORMAT:-vcf}"
OUT="$FV/acmg_out" && mkdir -p "$OUT"

for chr in $PANEL_CHROMS; do
  { printf '##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n'
    grep -P "^chr${chr}\t" "$SITES" || true; } > "${SCRATCH_DIR}/chr${chr}.vcf"
  [[ $(grep -vc '^#' "${SCRATCH_DIR}/chr${chr}.vcf") -eq 0 ]] && { echo "no variants"; continue; }
  "$FVEP_BIN" annotate -i "${SCRATCH_DIR}/chr${chr}.vcf" \
    --gff3 "$FV/data/chr${chr}.gff3" --fasta "$FV/data/chr${chr}.fa" \
    --sa-dir "$FV/sa_databases/" --acmg --pick --canonical --symbol --hgvs \
    --output-format "$FORMAT" -o "$OUT/acmg_chr${chr}.${FORMAT}" 2>&1 | tail -2
  rm -f "${SCRATCH_DIR}/chr${chr}.vcf"
done
