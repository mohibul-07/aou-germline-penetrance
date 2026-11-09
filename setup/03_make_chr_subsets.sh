#!/usr/bin/env bash
# Per-chromosome GFF3 + FASTA subsets with "chr" contig names.
#
# Why:
#   1. Memory. The full GFF3 (509K transcripts) + 3 GB FASTA + 62 SA databases took ~8 min just
#      to load and was killed repeatedly on a 50 GB node. Per-chromosome subsets load in seconds.
#   2. Contig naming. Ensembl files use "17"; our VCFs (from the VAT) use "chr17".
#      A mismatch produces "Loaded 0 transcripts" and fastVEP refuses to run.
#
# Pitfall we hit: grep-ing only data lines drops the ##gff-version header and fastVEP loads
# 0 transcripts. Keep every '#' line.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
cd "$FV/data"
GFF=Homo_sapiens.GRCh38.115.gff3
FA=Homo_sapiens.GRCh38.dna.primary_assembly.fa
TAB=$'\t'

for chr in $PANEL_CHROMS; do
  [[ -f "chr${chr}.gff3" && -f "chr${chr}.fa.fai" ]] && continue
  echo "chr${chr}"
  samtools faidx "$FA" "$chr" | sed "s/^>${chr}\b.*/>chr${chr}/" > "chr${chr}.fa"
  samtools faidx "chr${chr}.fa"
  awk -v c="$chr" -F'\t' '/^#/ || $1==c' "$GFF" | sed "s/^${chr}${TAB}/chr${chr}${TAB}/" > "chr${chr}.gff3"
done
ls -lh chr*.gff3 chr*.fa
