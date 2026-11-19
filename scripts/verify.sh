#!/bin/bash
# Project verification: runs all meaningful checks. Exit 0 = all verified.

set -e
cd "$DEVIN_PROJECT_DIR" || exit 1
set -o pipefail
FAIL=0

if [ -d demo/tests ]; then
  python3 -m unittest discover -s demo/tests -t demo 2>&1 | tail -2 || FAIL=1
fi

if [ -d tests ]; then
  python3 -m unittest discover -s tests -t . 2>&1 | tail -2 || FAIL=1
fi

if [ -f package.json ]; then
  npm test 2>&1 | tail -5 || FAIL=1
fi

if [ -d hackathon/contracts ]; then
  export PATH="$HOME/.foundry/bin:$PATH"
  cd hackathon/contracts || exit 1
  forge build 2>&1 | tail -1
  forge test 2>&1 | tail -2 || FAIL=1
fi

if [ "$FAIL" -ne 0 ]; then
  echo "VERIFY: FAILED"
  exit 1
fi
echo "VERIFY: OK"
