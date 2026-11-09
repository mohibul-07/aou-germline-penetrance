#!/usr/bin/env bash
# Purpose: reconstruct coordinate VAT extraction and sites-only VCF preparation.
# Inputs: VAT, TARGETS_BED; outputs PANEL_VAT, PANEL_SITES, PANEL_AC (Workbench only).
# Decision: zero-based BED start becomes one-based tabix start; header-based fields.
# Confirm the BED coordinate convention before execution. Region extraction includes
# neighboring genes; target-gene filtering belongs in reconciliation.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
: "${TARGETS_COORDINATE_SYSTEM:?Set the verified convention in config}"
[[ "$TARGETS_COORDINATE_SYSTEM" == bed0 ]] || exit 1
python3 -m carriers.extract_vat_panel
