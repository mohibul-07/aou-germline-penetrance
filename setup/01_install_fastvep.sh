#!/usr/bin/env bash
# Build fastVEP from source (only needed if the backed-up binary fails).
# Also clones the repo separately for helper scripts (check_acmg_stack.py, extract_gnomad_scores.py, ...).
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
: "${BACKUP_BUCKET:?Set BACKUP_BUCKET to your workspace bucket (gs://...) first; see config/params.env}"

# conda is not writable on the AoU image; rustup installs to $HOME
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Helper-script clone (separate from the working dir, which holds data)
[[ -d "$FVEP_REPO" ]] || git clone https://github.com/Huang-lab/fastVEP.git "$FVEP_REPO"

cd "$FVEP_REPO" && cargo build --release
mkdir -p "$FV"
cp target/release/fastvep "$FVEP_BIN"     # note: binary name is lowercase `fastvep`
"$FVEP_BIN" --version

# Back up the binary so the next restart can skip the build
gsutil cp "$FVEP_BIN" "$BACKUP_BUCKET/fastVEP/"
