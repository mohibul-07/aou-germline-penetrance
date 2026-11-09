#!/usr/bin/env bash
# Ensembl 115 GRCh38 gene models + reference FASTA.
# Sizes: GFF3 ~80 MB compressed / 1.2 GB uncompressed; FASTA ~840 MB compressed / 3 GB uncompressed.
# fastVEP needs the uncompressed FASTA (memory-mapped via the .fai index).
# Checks before downloading so a restored copy is never re-downloaded.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
mkdir -p "$FV/data" && cd "$FV/data"

GFF=Homo_sapiens.GRCh38.115.gff3
FA=Homo_sapiens.GRCh38.dna.primary_assembly.fa

if [[ ! -f "$GFF" ]]; then
  curl -LO "https://ftp.ensembl.org/pub/release-115/gff3/homo_sapiens/${GFF}.gz"
  gunzip "${GFF}.gz"
fi
if [[ ! -f "$FA" ]]; then
  curl -LO "https://ftp.ensembl.org/pub/release-115/fasta/homo_sapiens/dna/${FA}.gz"
  gunzip "${FA}.gz"
fi
[[ -f "${FA}.fai" ]] || samtools faidx "$FA"
ls -lh
