#!/bin/bash
# Project verification: runs the cheapest meaningful check available.
# Exit 0 = verified. Extend this per-project as needed.

cd "$DEVIN_PROJECT_DIR" || exit 1

if [ -d demo/tests ]; then
  python3 -m unittest discover -s demo/tests -t demo -v 2>&1
  exit $?
fi

if [ -d tests ]; then
  python3 -m unittest discover -s tests -t . -v 2>&1
  exit $?
fi

if [ -f package.json ]; then
  npm test 2>&1
  exit $?
fi

# nothing to verify against
echo "no test suite found"
exit 0
