#!/usr/bin/env bash
# Fully tear down the Kardiaflow development environment in a safe order.
#
# This sequence avoids dependency and deletion issues:
# - Workspace must be deleted first to lift system deny assignment on the managed RG.
# - Access connectors must be deleted after revoking RBAC to avoid lingering identities or errors.
# - Managed and main RGs are deleted last to ensure all dependent resources are fully cleaned up.
#
# 1. Delete Databricks workspace             - ensures access connectors are no longer in use.
# 2. Remove RBAC from access connectors      - clears role assignments to prevent permission errors during deletion.
# 3. Delete all Databricks access connectors - required before deleting their resource groups.
# 4. Delete managed resource group           - only safe to delete after connector cleanup.
# 5. Delete main resource group              - removed last to ensure no remaining dependencies exist.

set -euo pipefail

# -------------------------------------------------
# 1. Load environment and resolve paths
# -------------------------------------------------

here="$(cd "$(dirname "$0")" && pwd)"
infra_root="$here/.."
env_file="$infra_root/.env"

[[ -f "$env_file" ]] && # shellcheck source=/dev/null
source "$env_file"

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
ws_exists()       { az databricks workspace show -g "$RG" -n "$WORKSPACE" >/dev/null 2>&1; }
remove_rg_locks() { az lock list --resource-group "$1" -o tsv --query "[].id" 2>/dev/null | xargs -r -L1 az lock delete --ids >/dev/null 2>&1; }

# Robust wait: loop until the workspace 404s (there is no 'az databricks workspace wait --deleted')
wait_ws_deleted() {
  local tries=0 max_tries=180
  while (( tries < max_tries )); do
    if ! az databricks workspace show -g "$RG" -n "$WORKSPACE" >/dev/null 2>&1; then
      return 0
    fi
    sleep 10
    ((tries++))
  done
  return 1
}

wait_rg_deleted() {
  local rg="$1" tries=0 max_tries=180
  while (( tries < max_tries )); do
    if ! rg_exists "$rg"; then
      return 0
    fi
    sleep 10
    ((tries++))
  done
  return 1
}

# -------------------------------------------------
# 4. Attempt to discover managed RG if not supplied
# -------------------------------------------------

discover_managed_rg() {
  local id ac_rg sa_rg

  # 1) From workspace property
  if ws_exists; then
    id="$(az databricks workspace show -g "$RG" -n "$WORKSPACE" --query 'managedResourceGroupId' -o tsv 2>/dev/null || true)"
    if [[ -n "$id" ]]; then
      echo "${id##*/}"
      return
    fi
  fi

  # 2) Conventional name
  if rg_exists "${WORKSPACE}-managed"; then
    echo "${WORKSPACE}-managed"
    return
  fi

  # 3) Single access connector RG heuristic
  ac_rg="$(az resource list --resource-type Microsoft.Databricks/accessConnectors -o tsv --query "[].resourceGroup" 2>/dev/null | sort -u || true)"
  if [[ -n "$ac_rg" && "$(wc -l <<<"$ac_rg")" -eq 1 ]]; then
    echo "$ac_rg"
    return
  fi

  # 4) Single dbstorage* SA RG heuristic
  sa_rg="$(az storage account list -o tsv --query "[?contains(name,'dbstorage')].resourceGroup" 2>/dev/null | sort -u || true)"
  if [[ -n "$sa_rg" && "$(wc -l <<<"$sa_rg")" -eq 1 ]]; then
    echo "$sa_rg"
    return
  fi

  echo ""
}

# -------------------------------------------------
# 5. Remove all RBAC roles for connector identity
# -------------------------------------------------

strip_connector_rbac() {
  local id="$1"
  local principal
  principal="$(az resource show --ids "$id" --query "identity.principalId" -o tsv 2>/dev/null || true)"
  [[ -z "$principal" ]] && return 0

  local ra_ids
  ra_ids="$(az role assignment list --assignee "$principal" -o tsv --query "[].id" 2>/dev/null || true)"
  if [[ -n "$ra_ids" ]]; then
    while IFS= read -r rid; do
      [[ -n "$rid" ]] && az role assignment delete --ids "$rid" >/dev/null 2>&1 || true
    done <<<"$ra_ids"
  fi
}

# -----------------------------------------------------------
# 6. Delete Databricks access connectors in a resource group
# -----------------------------------------------------------

delete_access_connectors_in_rg() {
  local rg="$1"
  [[ -z "$rg" ]] && return 0
  rg_exists "$rg" || return 0

  local ids
  ids="$(az databricks access-connector list -g "$rg" --query "[].id" -o tsv 2>/dev/null || true)"
  [[ -z "$ids" ]] && return 0

  echo "Deleting access connectors in RG '$rg'..."
  while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    strip_connector_rbac "$id"

    local name
    name="$(az resource show --ids "$id" --query name -o tsv 2>/dev/null || true)"
    if [[ -n "$name" ]]; then
      az databricks access-connector delete -g "$rg" -n "$name" --yes >/dev/null 2>&1 \
        || az resource delete --ids "$id" >/dev/null 2>&1 || true
    fi
  done <<<"$ids"
}

# -----------------------------------------------------------
# 7. Delete storage accounts in a resource group (best-effort)
# -----------------------------------------------------------

delete_storage_accounts_in_rg() {
  local rg="$1"
  [[ -z "$rg" ]] && return 0
  rg_exists "$rg" || return 0

  az storage account list -g "$rg" -o tsv --query "[].name" 2>/dev/null | while IFS= read -r sa; do
    [[ -z "$sa" ]] && continue
    echo "Deleting storage account '$sa' in RG '$rg'..."
    az storage account delete -g "$rg" -n "$sa" --yes >/dev/null 2>&1 || true
  done
}

# ----------------------------------------------
# 8. Begin teardown execution
# ----------------------------------------------

echo "Teardown: RG=$RG WORKSPACE=$WORKSPACE"

# Discover managed RG if not provided
if [[ -z "${MANAGED_RG:-}" ]]; then
  MANAGED_RG="$(discover_managed_rg || true)"
fi
echo "Discovered MANAGED_RG=${MANAGED_RG:-<unknown>}"

# ----------------------------------------------
# 9. Delete Databricks workspace (control plane)
# ----------------------------------------------

if ws_exists; then
  echo "Deleting Databricks workspace '$WORKSPACE'..."
  az databricks workspace delete -g "$RG" -n "$WORKSPACE" --yes >/dev/null 2>&1 || true
  # Wait until the workspace truly disappears (lifts deny assignments on managed RG)
  if ! wait_ws_deleted; then
    echo "WARNING: timed out waiting for workspace deletion; continuing..."
  fi
fi

# ----------------------------------------------
# 10. Remove access connectors (main + managed RGs)
# ----------------------------------------------

delete_access_connectors_in_rg "$RG"
delete_access_connectors_in_rg "${MANAGED_RG:-}"

# ----------------------------------------------
# 11. Proactively delete storage accounts (incl. dbstorage* and ADLS)
# ----------------------------------------------

delete_storage_accounts_in_rg "${MANAGED_RG:-}"
delete_storage_accounts_in_rg "$RG"

# ----------------------------------------------
# 12. Delete managed resource group
# ----------------------------------------------

if [[ -n "${MANAGED_RG:-}" ]] && rg_exists "$MANAGED_RG"; then
  echo "Deleting managed RG '$MANAGED_RG'..."
  remove_rg_locks "$MANAGED_RG" || true
  az group delete --name "$MANAGED_RG" --yes --no-wait >/dev/null 2>&1 || true
  if ! wait_rg_deleted "$MANAGED_RG"; then
    echo "WARNING: Managed RG '$MANAGED_RG' still present; check locks or protection policies."
  fi
fi

# ----------------------------------------------
# 13. Delete main resource group
# ----------------------------------------------

if rg_exists "$RG"; then
  echo "Deleting main RG '$RG'..."
  remove_rg_locks "$RG" || true
  az group delete --name "$RG" --yes --no-wait >/dev/null 2>&1 || true
  if ! wait_rg_deleted "$RG"; then
    echo "WARNING: RG '$RG' still present; check locks or protection policies."
  fi
fi

echo "Teardown complete. (NetworkWatcherRG is left intact.)"