#!/usr/bin/env bash
# Authenticate Databricks CLI using environment variables from .env

# If sourced, avoid -e (errexit) so a failure doesn't kill the interactive shell.
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  set -u -o pipefail
  SOURCED=1
else
  set -euo pipefail
  SOURCED=0
fi

# Load .env automatically if vars are missing
if [[ -z "${DATABRICKS_PAT:-}" || -z "${RG:-}" || -z "${WORKSPACE:-}" ]]; then
  if [[ -f infra/.env ]]; then
    set -a
    # shellcheck disable=SC1091
    . infra/.env
    set +a
  fi
fi

# Required vars
: "${DATABRICKS_PAT:?Set DATABRICKS_PAT in infra/.env}"
: "${RG:?Set RG in infra/.env}"
: "${WORKSPACE:?Set WORKSPACE in infra/.env}"

# Ensure correct subscription if SUB is provided
if [[ -n "${SUB:-}" ]]; then
  az account set --subscription "$SUB" >/dev/null 2>&1 || true
fi

# Ensure the Databricks CLI extension exists
az extension show --name databricks >/dev/null 2>&1 || az extension add --name databricks >/dev/null

# Resolve workspace URL (don’t crash terminal on failure)
workspace_url=$(az databricks workspace show -g "$RG" -n "$WORKSPACE" --query workspaceUrl -o tsv 2>/dev/null)
if [[ -z "$workspace_url" ]]; then
  echo "Failed to resolve Databricks workspace URL.
Try: az login; az account set --subscription \"$SUB\"; az extension add --name databricks" >&2
  if [[ $SOURCED -eq 1 ]]; then return 1; else exit 1; fi
fi

export DATABRICKS_TOKEN="${DATABRICKS_PAT}"
export DATABRICKS_HOST="https://${workspace_url}"
echo "DATABRICKS_HOST set to ${DATABRICKS_HOST}"