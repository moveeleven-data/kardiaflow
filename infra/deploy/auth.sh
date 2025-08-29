#!/usr/bin/env bash
# infra/deploy/auth.sh
# Authenticate Databricks CLI using Azure + env vars.
# Loads infra/.env, resolves workspace URL, and exports DATABRICKS_HOST/TOKEN.

set -u -o pipefail


# --- Load environment ---

here="$(cd "$(dirname "$0")" && pwd)"
infra_root="$here/.."
ENV_FILE="$infra_root/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  # Return if sourced, exit if executed
  return 1 2>/dev/null || exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"


# --- Required variables ---

if [ -z "${DATABRICKS_PAT:-}" ] || [ -z "${RG:-}" ] || [ -z "${WORKSPACE:-}" ]; then
  echo "Missing required env vars. Run:  source infra/.env" >&2
  return 1 2>/dev/null || exit 1
fi


# --- Azure subscription (optional) ---

# Use SUB if provided, ignore errors
if [ -n "${SUB:-}" ]; then
  az account set --subscription "$SUB" >/dev/null 2>&1 || true
fi


# --- Ensure Azure Databricks CLI extension ---

az extension show --name databricks >/dev/null 2>&1 \
  || az extension add --name databricks >/dev/null 2>&1


# --- Resolve workspace URL ---

workspace_url="$(az databricks workspace show \
  -g "$RG" -n "$WORKSPACE" \
  --query workspaceUrl -o tsv 2>/dev/null || true)"

if [ -z "$workspace_url" ]; then
  echo "Failed to resolve Databricks workspace URL for RG='$RG', WORKSPACE='$WORKSPACE'." >&2
  echo "Fix: az login; az account set --subscription \"${SUB:-<your-sub>}\"; az extension add --name databricks" >&2
  return 1 2>/dev/null || exit 1
fi


# --- Export for Databricks CLI ---

export DATABRICKS_TOKEN="$DATABRICKS_PAT"
export DATABRICKS_HOST="https://${workspace_url}"

echo "DATABRICKS_HOST set to ${DATABRICKS_HOST}"