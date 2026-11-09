#!/usr/bin/env bash
# ClinVar allele-level (.osa2) and protein/splice gene-level (.oga) databases.
# Per ACMG_SETUP.md: download the NCBI release (it carries AF_EXAC/AF_TGP/AF_ESP, the PM2 backstop)
# and build clinvar_protein from variant_summary.txt.gz, NOT from the VCF (the VCF gives no splice index).
# Verify downloads before building: sa-build happily builds an empty/partial DB from a truncated file.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
# Reconstruction, not an authenticated export of the historical commands.
: "${ALLOW_UNVERIFIED_FASTVEP:?Review pinned sources/helper compatibility first}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")" "$SCRATCH_DIR"
exec >>"$PIPELINE_LOG" 2>&1
mkdir -p "$FV/sa_sources" "$FV/sa_databases" && cd "$FV/sa_sources"

curl --fail -L -o clinvar.vcf.gz "${CLINVAR_VCF_URL:?Pin historical release URL}"
gzip -t clinvar.vcf.gz && echo "clinvar gzip OK"
zcat clinvar.vcf.gz | grep '^##INFO=<ID=AF_EXAC' >/dev/null && echo "PM2 backstop field present"
"$FVEP_BIN" sa-build --source clinvar -i clinvar.vcf.gz -o ../sa_databases/clinvar --assembly GRCh38

curl --fail -L -o variant_summary.txt.gz "${CLINVAR_SUMMARY_URL:?Pin matching release URL}"
gzip -t variant_summary.txt.gz
"$FVEP_BIN" sa-build --source clinvar_protein -i variant_summary.txt.gz -o ../sa_databases/clinvar_protein --assembly GRCh38
