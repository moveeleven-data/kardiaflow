# Authenticate Databricks CLI via environment variables
set -euo pipefail
: "${DATABRICKS_PAT:?Set DATABRICKS_PAT in infra/.env}"
: "${RG:?Set RG in infra/.env}"
: "${WORKSPACE:?Set WORKSPACE in infra/.env}"

export DATABRICKS_TOKEN="${DATABRICKS_PAT}"
export DATABRICKS_HOST="https://$(
  az databricks workspace show -g "$RG" -n "$WORKSPACE" --query workspaceUrl -o tsv
)"
