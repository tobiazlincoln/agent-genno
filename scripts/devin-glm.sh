#!/bin/bash
# Run a GLM experiment against the Devin CLI using DEVIN_API_KEY from .env
# Usage: scripts/devin-glm.sh "your prompt here"

set -e
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

if [ -z "$DEVIN_API_KEY" ]; then
  echo "DEVIN_API_KEY is empty — put your API key in .env first" >&2
  exit 1
fi

DEVIN="/Applications/Devin.app/Contents/Resources/app/extensions/windsurf/devin/bin/devin"

# Only write credentials if the CLI is not already authenticated (avoids
# clobbering a valid login with a stale DEVIN_API_KEY from .env).
if ! "$DEVIN" auth status > /dev/null 2>&1; then
  cat > "$HOME/.local/share/devin/credentials.toml" <<EOF
api_key = "$DEVIN_API_KEY"
api_url = "https://api.devin.ai"
webapp_host = "app.devin.ai"
devin_webapp_host = "app.devin.ai"
devin_api_url = "https://api.devin.ai"
EOF
fi

# Cost-optimized defaults; override with DEVIN_MODEL / DEVIN_PERMISSION_MODE env.
MODEL="${DEVIN_MODEL:-swe-2-high}"
MODE="${DEVIN_PERMISSION_MODE:-accept-edits}"
exec "$DEVIN" -p --model "$MODEL" --permission-mode "$MODE" --verbosity 0 -- "$*"
