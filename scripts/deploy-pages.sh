#!/usr/bin/env bash
# SAFE gh-pages deploy — pure plumbing, never touches worktree/index, never runs `add -A`.
# Usage: scripts/deploy-pages.sh   (expects built files in hackathon/site/)
set -euo pipefail
cd "$(dirname "$0")/.."

parent=$(git rev-parse origin/gh-pages 2>/dev/null || true)
tmpidx=$(mktemp)
trap 'rm -f "$tmpidx"' EXIT
export GIT_INDEX_FILE="$tmpidx"
git read-tree --empty

git update-index --add --cacheinfo "100644,$(git hash-object hackathon/site/index.html),index.html"
git update-index --add --cacheinfo "100644,$(git hash-object hackathon/site/favicon.svg),favicon.svg"
for f in hackathon/site/assets/*; do
  name=$(basename "$f")
  git update-index --add --cacheinfo "100644,$(git hash-object "$f"),assets/$name"
done

tree=$(git write-tree)
echo "tree contains exactly $(git ls-tree -r "$tree" | wc -l | tr -d ' ') files:"
git ls-tree -r --name-only "$tree"

parentarg=""
[ -n "$parent" ] && parentarg="-p $parent"
commit=$(git commit-tree "$tree" $parentarg -m "deploy pages $(date -u +%FT%TZ)")
git push origin "$commit:gh-pages"
echo "deployed: $commit"
