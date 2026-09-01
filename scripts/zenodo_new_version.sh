#!/usr/bin/env bash
#
# Deposit the current tagged release as a NEW VERSION of the existing Zenodo
# concept DOI 10.5281/zenodo.21536448 — the same operation publish.yml's
# `zenodo` job performs on a GitHub release, runnable locally.
#
#   export ZENODO_TOKEN=...            # scopes: deposit:write + deposit:actions
#   bash scripts/zenodo_new_version.sh           # version from pyproject.toml
#   bash scripts/zenodo_new_version.sh 0.2.0     # explicit
#
# Guards: refuses without a token; refuses if the tag vVERSION does not exist;
# skips (exit 0) if Zenodo's latest version already equals VERSION.
set -euo pipefail
cd "$(dirname "$0")/.."

CONCEPT_RECID="21536448"
VERSION="${1:-$(python3 -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")}"
TAG="v${VERSION}"
AUTH="Authorization: Bearer ${ZENODO_TOKEN:?set ZENODO_TOKEN (scopes deposit:write + deposit:actions)}"

git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null || {
  echo "tag ${TAG} does not exist — tag the release first:  git tag ${TAG} && git push origin ${TAG}" >&2; exit 1; }

LATEST=$(curl -sfL "https://zenodo.org/api/records/${CONCEPT_RECID}")
LATEST_ID=$(echo "$LATEST" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
LATEST_VER=$(echo "$LATEST" | python3 -c "import json,sys;print(json.load(sys.stdin)['metadata'].get('version',''))")
echo "concept ${CONCEPT_RECID}: latest record ${LATEST_ID} at version '${LATEST_VER}'"
if [ "$LATEST_VER" = "$VERSION" ]; then echo "already at ${VERSION} — nothing to do"; exit 0; fi

NEWV=$(curl -sf -X POST -H "$AUTH" "https://zenodo.org/api/deposit/depositions/${LATEST_ID}/actions/newversion")
DRAFT_URL=$(echo "$NEWV" | python3 -c "import json,sys;print(json.load(sys.stdin)['links']['latest_draft'])")
DRAFT=$(curl -sf -H "$AUTH" "$DRAFT_URL")
DRAFT_ID=$(echo "$DRAFT" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
BUCKET=$(echo "$DRAFT" | python3 -c "import json,sys;print(json.load(sys.stdin)['links']['bucket'])")
echo "draft deposition ${DRAFT_ID}"

# the new version is exactly the tagged source archive — drop inherited files
echo "$DRAFT" | python3 -c "import json,sys;[print(f['id']) for f in json.load(sys.stdin).get('files',[])]" |
while read -r FID; do
  curl -sf -X DELETE -H "$AUTH" "https://zenodo.org/api/deposit/depositions/${DRAFT_ID}/files/${FID}" || true
done

ARCHIVE="biology_as_code-${TAG}.tar.gz"
git archive --format=tar.gz --prefix="biology_as_code-${TAG}/" -o "$ARCHIVE" "$TAG"
curl -sf -X PUT -H "$AUTH" --upload-file "$ARCHIVE" "${BUCKET}/${ARCHIVE}" >/dev/null
echo "uploaded ${ARCHIVE} ($(du -h "$ARCHIVE" | cut -f1))"
rm -f "$ARCHIVE"

# metadata: take .zenodo.json as source of truth, set version + today's date
python3 - "$VERSION" > metadata.json <<'PYEOF'
import json, sys, datetime
meta = json.load(open(".zenodo.json"))
meta["version"] = sys.argv[1]
meta["publication_date"] = datetime.date.today().isoformat()
print(json.dumps({"metadata": meta}))
PYEOF
curl -sf -X PUT -H "$AUTH" -H "Content-Type: application/json" -d @metadata.json \
  "https://zenodo.org/api/deposit/depositions/${DRAFT_ID}" >/dev/null
rm -f metadata.json

PUB=$(curl -sf -X POST -H "$AUTH" "https://zenodo.org/api/deposit/depositions/${DRAFT_ID}/actions/publish")
echo "$PUB" | python3 -c "import json,sys;d=json.load(sys.stdin);print('PUBLISHED', d['metadata']['version'], '->', 'https://doi.org/'+d['doi'])"
echo "concept DOI (cite this): https://doi.org/10.5281/zenodo.${CONCEPT_RECID}"
