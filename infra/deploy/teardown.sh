#!/usr/bin/env bash
# Fully tear down the Kardiaflow development environment in a safe order.
#
# This specific sequence avoids dependency and deletion issues:
#
# 1. Delete Databricks workspace
#    - Releases the control plane and ensures access connectors are no longer in use.
#
# 2. Remove RBAC from access connectors
#    - Clears role assignments to prevent permission errors during deletion.
#
# 3. Delete all Databricks access connectors (main + managed RGs)
#    - Required before deleting their resource groups.
#
# 4. Delete managed resource group
#    - Holds Databricks-managed infra; only safe to delete after connector cleanup.
#
# 5. Delete main resource group
#    - Removed last to ensure no remaining dependencies exist.

set -euo pipefail

# -------------------------------------------------
# 1. Load environment and resolve paths
# -------------------------------------------------

here="$(cd "$(dirname "$0")" && pwd)"
infra_root="$here/.."
env_file="$infra_root/.env"

[[ -f "$env_file" ]] && source "$env_file"

: "${RG:?Set RG in infra/.env}"
: "${WORKSPACE:?Set WORKSPACE in infra/.env}"
SUB="${SUB:-}"
MANAGED_RG="${MANAGED_RG:-}"

[[ -n "$SUB" ]] && az account set --subscription "$SUB" >/dev/null

# -------------------------------------------------
# 2. Ensure Databricks CLI extension exists
# -------------------------------------------------

az extension add -n databricks -y >/dev/null 2>&1 || az extension update -n databricks -y >/dev/null 2>&1

# -------------------------------------------------
# 3. Define helper functions
# -------------------------------------------------

rg_exists()       { [[ "$(az group exists --name "$1" -o tsv 2>/dev/null)" == "true" ]]; }
ws_exists()       { az databricks workspace show -g "$RG" -n "$WORKSPACE" &>/dev/null; }
remove_rg_locks() { az lock list --resource-group "$1" -o tsv --query "[].id" | xargs -r -L1 az lock delete --ids; }
wait_until_gone() { local rg="$1"; for _ in {1..90}; do rg_exists "$rg" || return 0; sleep 10; done; return 1; }

# -------------------------------------------------
# 4. Attempt to discover managed RG if not supplied
# -------------------------------------------------

discover_managed_rg() {
  local id ac_rg sa_rg

  # 1. Try the workspace's managedResourceGroupId property
  if ws_exists; then
    id="$(az databricks workspace show -g "$RG" -n "$WORKSPACE" \
          --query 'managedResourceGroupId' -o tsv 2>/dev/null || true)"
    [[ -n "$id" ]] && { echo "${id##*/}"; return; }
  fi

  # 2. Conventional managed RG name
  if rg_exists "${WORKSPACE}-managed"; then
    echo "${WORKSPACE}-managed"
    return
  fi

  # 3. Use the access connector RG if there's exactly one
  ac_rg="$(az resource list --resource-type Microsoft.Databricks/accessConnectors \
          -o tsv --query "[].resourceGroup" 2>/dev/null | sort -u || true)"
  if [[ -n "$ac_rg" && "$(wc -l <<< "$ac_rg")" -eq 1 ]]; then
    echo "$ac_rg"
    return
  fi

  # 4. Use the storage account RG if there's exactly one matching dbstorage pattern
  sa_rg="$(az storage account list -o tsv \
          --query "[?contains(name,'dbstorage')].resourceGroup" 2>/dev/null | sort -u || true)"
  if [[ -n "$sa_rg" && "$(wc -l <<< "$sa_rg")" -eq 1 ]]; then
    echo "$sa_rg"
    return
  fi

  # 5. Not found
  echo ""
}

# -------------------------------------------------
# 5. Remove all RBAC roles for connector identity
# -------------------------------------------------

# Remove all role assignments from the managed identity of a given access connector.
# This effectively strips its RBAC permissions before the connector itself is deleted.
strip_connector_rbac() {
  local id="$1"

  # Get the principalId of the connector's system-assigned identity.
  local principal
  principal="$(az resource show --ids "$id" --query "identity.principalId" -o tsv 2>/dev/null || true)"
  # If no identity is present, nothing to do.
  [[ -z "$principal" ]] && return 0

  # List all role assignment IDs for that principal.
  local ra_ids
  ra_ids="$(az role assignment list --assignee "$principal" -o tsv --query "[].id" 2>/dev/null || true)"

  # Delete each role assignment to revoke all granted roles.
  if [[ -n "$ra_ids" ]]; then
    while IFS= read -r rid; do
      [[ -n "$rid" ]] && az role assignment delete --ids "$rid" >/dev/null 2>&1 || true
    done <<< "$ra_ids"
  fi
}

# -----------------------------------------------------------
# 6. Delete Databricks access connectors in a resource group
# -----------------------------------------------------------

# For each connector:
#   1. Revoke its RBAC by stripping its managed identity role assignments.
#   2. Delete the connector using the dedicated CLI; fall back to generic resource deletion on failure.
delete_access_connectors_in_rg() {
  local rg="$1"

  # No-op if rg is empty or does not exist.
  [[ -n "$rg" ]] && rg_exists "$rg" || return 0

  # List access connector IDs in this resource group.
  local ids
  ids="$(az databricks access-connector list -g "$rg" --query "[].id" -o tsv 2>/dev/null || true)"
  [[ -z "$ids" ]] && return 0

  echo "Deleting access connectors in RG '$rg'"

  while IFS= read -r id; do
    [[ -z "$id" ]] && continue

    # Revoke RBAC from the connector's managed identity.
    strip_connector_rbac "$id"

    # Resolve the connector name so we can call the dedicated delete command.
    local name
    name="$(az resource show --ids "$id" --query name -o tsv 2>/dev/null || true)"
    if [[ -n "$name" ]]; then
      # Attempt deletion via Databricks CLI; if that fails, fallback to generic resource delete.
      az databricks access-connector delete -g "$rg" -n "$name" --yes >/dev/null 2>&1 \
        || az resource delete --ids "$id" >/dev/null 2>&1 || true
    fi
  done <<< "$ids"
}

# ----------------------------------------------
# 7. Begin teardown execution
# ----------------------------------------------

echo "Teardown: RG=$RG WORKSPACE=$WORKSPACE"

# ------------------------------------------------------------------------
# 8. Discover the managed resource group used by the Databricks workspace.
# ------------------------------------------------------------------------

if [[ -z "$MANAGED_RG" ]]; then
  MANAGED_RG="$(discover_managed_rg || true)"
fi

echo "Discovered MANAGED_RG=${MANAGED_RG:-<unknown>}"

# ----------------------------------------------
# 9. Delete Databricks workspace (control plane)
# ----------------------------------------------

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


# 9. Remove access connectors (main + managed RGs)
delete_access_connectors_in_rg "$RG"
delete_access_connectors_in_rg "$MANAGED_RG"

# ----------------------------------------------
# 10. Remove access connectors from both RGs
# ----------------------------------------------

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

# ----------------------------------------------
# 12. Delete main resource group
# ----------------------------------------------

if rg_exists "$RG"; then
  echo "Deleting main RG '$RG'..."
  remove_rg_locks "$RG" || true
  az group delete --name "$RG" --yes --no-wait || true

  if ! wait_until_gone "$RG"; then
    echo "WARNING: RG '$RG' still present; check locks or protection policies."
  fi
fi

echo "Teardown complete. (NetworkWatcherRG is left intact.)"
