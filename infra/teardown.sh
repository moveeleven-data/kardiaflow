#!/usr/bin/env bash
# Safe teardown script for KardiaFlow dev environment
# Deletes Databricks workspace, then removes the parent resource group.
set -euo pipefail

# Load environment variables
source "$(dirname "$0")/.env"

# Delete Databricks workspace (will also delete the managed RG)
az databricks workspace delete --resource-group "$RG" --name "$WORKSPACE" --yes || true

# Delete parent resource group (non‑blocking)
az group delete --name "$RG" --yes --no-wait || true

echo "Teardown initiated. Azure will finish deleting resources in the background."
