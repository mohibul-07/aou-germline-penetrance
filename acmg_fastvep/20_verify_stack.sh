#!/usr/bin/env bash
# Purpose: verify evaluated ACMG criteria with a reviewed external probe.
# Inputs: ACMG_PROBE_VCF and restored fastVEP references; output ACMG_PROBE_JSON/log.
# Decision: fail closed if required criteria are not evaluated; probe output is internal.
# User reconstruction repaired; exact historical probe and binary commit must be restored.
set -euo pipefail
source "$(dirname "$0")/../config/params.env"
: "${ALLOW_UNVERIFIED_FASTVEP:?Review binary and helper compatibility}"
[[ "$ALLOW_UNVERIFIED_FASTVEP" == 1 ]] || exit 1
mkdir -p "$(dirname "$PIPELINE_LOG")"
exec >>"$PIPELINE_LOG" 2>&1
"$FVEP_BIN" annotate -i "$ACMG_PROBE_VCF" --gff3 "$ACMG_PROBE_GFF" --fasta "$ACMG_PROBE_FASTA" \
 --sa-dir "$FV/sa_databases/" --acmg --output-format json --pick --canonical -o "$ACMG_PROBE_JSON"
python3 - <<'CHECK'
import json,os
with open(os.environ['ACMG_PROBE_JSON']) as f: data=json.load(f)
required=set(os.environ['ACMG_REQUIRED_CRITERIA'].split(','))
evaluated=set()
for record in data:
 for tc in record.get('transcript_consequences',[]):
  for criterion in tc.get('acmg',{}).get('criteria',[]):
   if criterion.get('evaluated') is True: evaluated.add(criterion['code'])
if not required <= evaluated:
 raise ValueError('Required criteria were not evaluated; review internal JSON')
CHECK
