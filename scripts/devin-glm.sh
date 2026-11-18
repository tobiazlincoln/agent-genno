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

# Write credentials in the format the CLI checks
cat > "$HOME/.local/share/devin/credentials.toml" <<EOF
api_key = "$DEVIN_API_KEY"
api_url = "https://api.devin.ai"
webapp_host = "app.devin.ai"
devin_webapp_host = "app.devin.ai"
devin_api_url = "https://api.devin.ai"
EOF

exec "$DEVIN" -p --model glm --permission-mode dangerous -- "$*"
