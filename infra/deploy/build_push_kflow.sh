#!/usr/bin/env bash
# Build kflow wheel and upload it to /Workspace/Shared/libs in the Databricks workspace

set -euo pipefail

# 1. Set working directories and verify required .env config
here="$(cd "$(dirname "$0")" && pwd)"   # …/infra/deploy
infra_root="$here/.."                   # …/infra
repo_root="$infra_root/.."              # project root
cd "$repo_root"

ENV_FILE="$infra_root/.env"
[[ -f "$ENV_FILE" ]] || {
  echo "ERROR: .env not found at $ENV_FILE" >&2; exit 1; }

# Load Databricks token from .env
source "$ENV_FILE"
: "${DATABRICKS_PAT:?ERROR: Set DATABRICKS_PAT in infra/.env}"


# 2. Read the current kflow version from pyproject.toml
KFLOW_VER="$(python - <<'PY'
import sys, pathlib
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

with open("pyproject.toml", "rb") as f:
    print(tomllib.load(f)["project"]["version"])
PY
)"
wheel_glob="dist/kflow-${KFLOW_VER}-py3-none-any.whl"


# 3. Build the wheel file using setuptools
python -m pip install --quiet --upgrade build setuptools wheel
python -m build --wheel >/dev/null

[[ -e $wheel_glob ]] || {
  echo "ERROR: Wheel not found at $wheel_glob" >&2; exit 1; }

wheel_path="$(ls $wheel_glob | head -1)"
wheel_name="$(basename "$wheel_path")"


# 4. Authenticate with Databricks CLI using values from the deployment output
DB_HOST="$(az deployment group show \
  --resource-group "$RG" \
  --name "$DEPLOY" \
  --query 'properties.outputs.databricksUrl.value' -o tsv)"

export DATABRICKS_HOST="https://${DB_HOST}"
export DATABRICKS_TOKEN="$DATABRICKS_PAT"

databricks configure --token \
  --host  "$DATABRICKS_HOST" \
  --token "$DATABRICKS_TOKEN" \
  --profile "$PROFILE" >/dev/null


# 5. Upload the wheel to Databricks Workspace under /Workspace/Shared/libs
WS_DEST_DIR="/Workspace/Shared/libs"
WS_DEST_PATH="${WS_DEST_DIR}/${wheel_name}"

databricks workspace mkdirs "$WS_DEST_DIR" --profile "$PROFILE" 2>/dev/null || true

databricks workspace import \
  --file "$wheel_path" \
  "$WS_DEST_PATH" \
  --format RAW --overwrite \
  --profile "$PROFILE"

echo "Uploaded $wheel_name to $WS_DEST_PATH – kflow$KFLOW_VER ready."