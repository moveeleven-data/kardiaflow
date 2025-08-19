#!/usr/bin/env bash
# Build kflow wheel and publish to Workspace, plus a stable requirements file (Workspace).

set -euo pipefail

# Paths
here="$(cd "$(dirname "$0")" && pwd)"        # infra/deploy
infra_root="$here/.."                        # infra
repo_root="$infra_root/.."                   # project root
cd "$repo_root"

ENV_FILE="$infra_root/.env"

# Sanity checks
[[ -f "$ENV_FILE" ]] || { echo "ERROR: .env not found at $ENV_FILE" >&2; exit 1; }
# shellcheck disable=SC1090
source "$ENV_FILE"

: "${RG:?Set RG in infra/.env}"
: "${DEPLOY:?Set DEPLOY in infra/.env}"
: "${DATABRICKS_PAT:?Set DATABRICKS_PAT in infra/.env}"

command -v az >/dev/null         || { echo "ERROR: az not found on PATH" >&2; exit 1; }
command -v databricks >/dev/null || { echo "ERROR: databricks CLI not found on PATH" >&2; exit 1; }
command -v python >/dev/null     || { echo "ERROR: python not found on PATH" >&2; exit 1; }

# Read project version from pyproject.toml
KFLOW_VER="$(python - <<'PY'
import sys
if sys.version_info >= (3, 11):
    import tomllib as T
else:
    import tomli as T
with open("pyproject.toml","rb") as f:
    print(T.load(f)["project"]["version"])
PY
)"
wheel_glob="dist/kflow-${KFLOW_VER}-py3-none-any.whl"

# Build wheel
python -m pip install -q --upgrade build setuptools wheel
python -m build --wheel >/dev/null

[[ -e "$wheel_glob" ]] || { echo "ERROR: Wheel not found at $wheel_glob" >&2; exit 1; }
wheel_path="$(ls -t $wheel_glob | head -1)"
wheel_name="$(basename "$wheel_path")"

# Auth for Databricks CLI via env vars
DB_HOST="$(az deployment group show \
  --resource-group "$RG" --name "$DEPLOY" \
  --query 'properties.outputs.databricksUrl.value' -o tsv)"
export DATABRICKS_HOST="https://${DB_HOST}"
export DATABRICKS_TOKEN="$DATABRICKS_PAT"

# Quick auth check (no output on success)
databricks workspace list / >/dev/null

# Publish wheel to Workspace files (this is what Jobs will consume on 15.x)
WS_DIR="/Workspace/Shared/libs"
databricks workspace mkdirs "$WS_DIR" 2>/dev/null || true
# New CLI: TARGET first, then --file
databricks workspace import "${WS_DIR}/${wheel_name}" \
  --file "$wheel_path" --format RAW --overwrite

# Stable requirements file (Workspace) pointing at the newest wheel
REQ_TMP="$(mktemp)"; trap 'rm -f "$REQ_TMP"' EXIT
printf "/Workspace/Shared/libs/%s\n" "$wheel_name" > "$REQ_TMP"

databricks workspace import "${WS_DIR}/kflow-requirements.txt" \
  --file "$REQ_TMP" --format RAW --overwrite

# Summary
echo "Published:"
echo "  Workspace wheel:    /Workspace/Shared/libs/${wheel_name}"
echo "  Workspace req file: /Workspace/Shared/libs/kflow-requirements.txt"
echo "Every task should have this requirements file attached:"
echo '  "libraries": [ { "requirements": "/Workspace/Shared/libs/kflow-requirements.txt" } ]'
