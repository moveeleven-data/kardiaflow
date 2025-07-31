# Authenticate Databricks CLI via environment variables
export DATABRICKS_TOKEN="${DATABRICKS_PAT:?Set DATABRICKS_PAT first}"
export DATABRICKS_HOST="https://$(
  az databricks workspace show \
    -g "$RG" -n "$WORKSPACE" \
    --query workspaceUrl -o tsv
)"