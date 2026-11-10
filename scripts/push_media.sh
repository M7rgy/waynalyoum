#!/usr/bin/env bash
# Publishes today's generated images/videos to the orphan "media" branch (force-pushed, so repo history stays small)
# and records the commit in content/<date>/media.json. jsDelivr then serves them publicly for Instagram to fetch.
set -euo pipefail
DATE="$1"
SRC="assets/$DATE"
[ -d "$SRC" ] || { echo "no $SRC"; exit 1; }
TMP=$(mktemp -d)
mkdir -p "$TMP/assets/$DATE"
find "$SRC" -maxdepth 1 -type f \( -name '*.jpg' -o -name '*.mp4' \) -exec cp {} "$TMP/assets/$DATE/" \;
cd "$TMP"
git init -q -b media
git config user.name "waynalyoum-bot"; git config user.email "actions@users.noreply.github.com"
git add -A && git commit -qm "media $DATE"
SHA=$(git rev-parse HEAD)
git push -qf "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" media:media
cd - >/dev/null
FILES=$(cd "$TMP/assets/$DATE" && ls | python3 -c 'import sys,json;print(json.dumps([l.strip() for l in sys.stdin]))')
printf '{"sha": "%s", "files": %s}\n' "$SHA" "$FILES" > "content/$DATE/media.json"
echo "media: $SHA ($(echo "$FILES" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))') files)"
