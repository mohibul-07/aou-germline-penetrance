#!/usr/bin/env bash
# Print VAT column numbers. Column positions can change between releases -- check before hard-coding.
source "$(dirname "$0")/../config/params.env"
zcat "$VAT" | head -1 | tr '\t' '\n' | cat -n
