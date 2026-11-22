#!/bin/bash
# Waits until the priority (deposit/withdraw) set is fully fetched, then runs the analysis.
cd "$(dirname "$0")/.."
TOTAL=$(python3 -c "import json;print(len(json.load(open('BRAIN/research/rings/priority.json'))['sigs']))")
while true; do
  HAVE=$(python3 - <<'PY'
import json
p={s for s in json.load(open('BRAIN/research/rings/priority.json'))['sigs']}
have={json.loads(l)['sig'] for l in open('BRAIN/research/rings/tx.jsonl')}
print(len(p & have))
PY
)
  echo "$(date +%H:%M) $HAVE/$TOTAL" >> BRAIN/research/rings/finisher.log
  [ "$HAVE" -ge $((TOTAL - 30)) ] && break
  sleep 300
done
python3 tools/rings-analyze.py --perms 200 > BRAIN/research/rings/analysis-run.log 2>&1
python3 tools/rings-behaviour.py > BRAIN/research/rings/behaviour-run.log 2>&1
echo "$(date +%H:%M) DONE report=BRAIN/research/rings/LEAK-REPORT.md" >> BRAIN/research/rings/finisher.log
