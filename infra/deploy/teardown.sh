#!/usr/bin/env bash
# Teardown for KardiaFlow dev env.
# Order matters:
#   1) Delete Databricks workspace
#   2) Remove RBAC from any Microsoft.Databricks/accessConnectors
#   3) Delete access connectors (both RGs)
#   4) Delete managed RG
#   5) Delete main RG

set -euo pipefail

# Paths and Environment
here="$(cd "$(dirname "$0")" && pwd)"
infra_root="$here/.."
env_file="$infra_root/.env"

[[ -f "$env_file" ]] && source "$env_file"

: "${RG:?Set RG in infra/.env}"
: "${WORKSPACE:?Set WORKSPACE in infra/.env}"
SUB="${SUB:-}"
MANAGED_RG="${MANAGED_RG:-}"

[[ -n "$SUB" ]] && az account set --subscription "$SUB" >/dev/null


# Ensure the Databricks CLI extension is present (for access-connector delete)
az extension add -n databricks -y >/dev/null 2>&1 || az extension update -n databricks -y >/dev/null 2>&1


# Helpers
rg_exists()       { [[ "$(az group exists --name "$1" -o tsv 2>/dev/null)" == "true" ]]; }
ws_exists()       { az databricks workspace show -g "$RG" -n "$WORKSPACE" &>/dev/null; }
remove_rg_locks() { az lock list --resource-group "$1" -o tsv --query "[].id" | xargs -r -L1 az lock delete --ids; }
wait_until_gone() { local rg="$1"; for _ in {1..90}; do rg_exists "$rg" || return 0; sleep 10; done; return 1; }


discover_managed_rg() {
  local id ac_rg sa_rg
  if ws_exists; then
    id="$(az databricks workspace show -g "$RG" -n "$WORKSPACE" \
          --query 'managedResourceGroupId' -o tsv 2>/dev/null || true)"
    [[ -n "$id" ]] && echo "${id##*/}" && return
  fi
  if rg_exists "${WORKSPACE}-managed"; then echo "${WORKSPACE}-managed"; return; fi
  ac_rg="$(az resource list --resource-type Microsoft.Databricks/accessConnectors \
          -o tsv --query "[].resourceGroup" 2>/dev/null | sort -u || true)"
  if [[ -n "$ac_rg" && "$(wc -l <<< "$ac_rg")" -eq 1 ]]; then echo "$ac_rg"; return; fi
  sa_rg="$(az storage account list -o tsv \
          --query "[?contains(name,'dbstorage')].resourceGroup" 2>/dev/null | sort -u || true)"
  if [[ -n "$sa_rg" && "$(wc -l <<< "$sa_rg")" -eq 1 ]]; then echo "$sa_rg"; return; fi
  echo ""
}


# Remove RBAC for a connector's managed identity at all scopes where it's assigned
strip_connector_rbac() {
  local id="$1"
  # Get principalId of the connector's system-assigned identity
  local principal
  principal="$(az resource show --ids "$id" --query "identity.principalId" -o tsv 2>/dev/null || true)"
  [[ -z "$principal" ]] && return 0

  # Delete all role assignments for this principal across the subscription
  # (list -> delete by id for reliability)
  local ra_ids
  ra_ids="$(az role assignment list --assignee "$principal" -o tsv --query "[].id" 2>/dev/null || true)"
  if [[ -n "$ra_ids" ]]; then
    while IFS= read -r rid; do
      [[ -n "$rid" ]] && az role assignment delete --ids "$rid" >/dev/null 2>&1 || true
    done <<< "$ra_ids"
  fi
}


# Delete all access connectors in a resource group (after RBAC is stripped)
delete_access_connectors_in_rg() {
  local rg="$1"
  [[ -n "$rg" ]] && rg_exists "$rg" || return 0

  # Use the Databricks CLI extension to list access connectors in this RG
  local ids
  ids="$(az databricks access-connector list -g "$rg" --query "[].id" -o tsv 2>/dev/null || true)"
  [[ -z "$ids" ]] && return 0

  echo "Deleting Access Connectors in RG '$rg'…"
  while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    strip_connector_rbac "$id"
    # Resolve name for delete
    local name
    name="$(az resource show --ids "$id" --query name -o tsv 2>/dev/null || true)"
    if [[ -n "$name" ]]; then
      # Delete with the dedicated command; fall back to generic delete if needed
      az databricks access-connector delete -g "$rg" -n "$name" --yes >/dev/null 2>&1 \
        || az resource delete --ids "$id" >/dev/null 2>&1 || true
    fi
  done <<< "$ids"
}


# Begin Teardown
echo "Teardown: RG=$RG WORKSPACE=$WORKSPACE"

# Discover managed RG if needed
if [[ -z "$MANAGED_RG" ]]; then
  MANAGED_RG="$(discover_managed_rg || true)"
fi
echo "Discovered MANAGED_RG=${MANAGED_RG:-<unknown>}"

# 1) Delete workspace first (so connectors are no longer in use)
if ws_exists; then
  echo "Deleting Databricks workspace '$WORKSPACE'..."
  az databricks workspace delete -g "$RG" -n "$WORKSPACE" --yes || true
  # Wait up to ~15 minutes for control-plane delete to propagate
  for _ in {1..90}; do
    if ! ws_exists; then
      echo "Workspace deleted."
      break
    fi
    sleep 10
  done
fi

# 2) Now remove any access connectors (main + managed RG), stripping RBAC first
delete_access_connectors_in_rg "$RG"
delete_access_connectors_in_rg "$MANAGED_RG"

# 3) Delete managed RG (if exists)
if [[ -n "$MANAGED_RG" && "$(rg_exists "$MANAGED_RG")" == "true" ]]; then
  echo "Deleting managed RG '$MANAGED_RG'..."
  remove_rg_locks "$MANAGED_RG" || true
  # Clear lingering dbstorage accounts proactively
  az storage account list -g "$MANAGED_RG" -o tsv --query "[].name" 2>/dev/null | while read -r sa; do
    [[ -n "$sa" ]] && az storage account delete -g "$MANAGED_RG" -n "$sa" --yes || true
  done
  az group delete --name "$MANAGED_RG" --yes --no-wait || true
  if ! wait_until_gone "$MANAGED_RG"; then
    echo "WARNING: Managed RG '$MANAGED_RG' still present; check locks or protection policies."
  fi
fi

# 4) Delete main RG
if rg_exists "$RG"; then
  echo "Deleting main RG '$RG'..."
  remove_rg_locks "$RG" || true
  az group delete --name "$RG" --yes --no-wait || true
  if ! wait_until_gone "$RG"; then
    echo "WARNING: RG '$RG' still present; check locks or protection policies."
  fi
fi

echo "Teardown complete. (NetworkWatcherRG is left intact.)"
