#!/usr/bin/env bash
# Authenticate Databricks CLI using environment variables from .env

set -euo pipefail

# 1. Check for required environment variables
: "${DATABRICKS_PAT:?Set DATABRICKS_PAT in infra/.env}"
: "${RG:?Set RG in infra/.env}"
: "${WORKSPACE:?Set WORKSPACE in infra/.env}"

# 2. Set authentication environment variables for Databricks CLI
export DATABRICKS_TOKEN="${DATABRICKS_PAT}"
export DATABRICKS_HOST="https://$(
  az databricks workspace show -g "$RG" -n "$WORKSPACE" --query workspaceUrl -o tsv
)"