#!/usr/bin/env bash
# Gene-level databases: gnomAD constraint and ClinGen Gene-Disease Validity.
#
# ClinGen GDV is written under the "omim" json_key (historical name). It REPLACES OMIM genemap2.txt.
# Without a gene-disease source, PVS1 never fires and loss-of-function variants silently stay VUS:
# Missing gene-disease evidence changed classification; historical small counts withheld.
# Do NOT commit or redistribute genemap2.txt (OMIM license).
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
# Reconstruction, not an authenticated export of the historical commands.
: "${ALLOW_UNVERIFIED_FASTVEP:?Review pinned sources/helper compatibility first}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")" "$SCRATCH_DIR"
exec >>"$PIPELINE_LOG" 2>&1
cd "$FV/sa_sources"

curl --fail -L -o gnomad.v4.1.constraint_metrics.tsv "$GNOMAD_CONSTRAINT_URL"
"$FVEP_BIN" sa-build --source gnomad_genes -i gnomad.v4.1.constraint_metrics.tsv -o ../sa_databases/gnomad_genes --assembly GRCh38

curl --fail -L -o clingen_gene_validity.csv "${CLINGEN_GDV_URL:?Restore or pin reviewed snapshot}"
python3 "$FVEP_REPO/analysis/acmg_benchmark/scripts/sa_sources/clingen_gdv_to_oga.py" \
    clingen_gene_validity.csv clingen_gdv.tsv
"$FVEP_BIN" sa-build --source omim -i clingen_gdv.tsv -o ../sa_databases/omim --assembly GRCh38
