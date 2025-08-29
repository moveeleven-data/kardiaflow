#!/usr/bin/env bash
# infra/deploy/teardown.sh
# Tear down the KardiaFlow dev environment in safe order.
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


# 1. Load environment and resolve paths
here="$(cd "$(dirname "$0")" && pwd)"
infra_root="$here/.."
env_file="$infra_root/.env"

[[ -f "$env_file" ]] && source "$env_file"  # shellcheck disable=SC1090
: "${RG:?Set RG in infra/.env}"
: "${WORKSPACE:?Set WORKSPACE in infra/.env}"
SUB="${SUB:-}"
MANAGED_RG="${MANAGED_RG:-}"

[[ -n "$SUB" ]] && az account set --subscription "$SUB" >/dev/null


# Ensure Databricks CLI extension exists
az extension add -n databricks -y >/dev/null 2>&1 || az extension update -n databricks -y >/dev/null 2>&1


# Define helper functions
rg_exists() {
  [[ "$(az group exists --name "$1" -o tsv 2>/dev/null)" == "true" ]]
}

ws_exists() {
  az databricks workspace show -g "$RG" -n "$WORKSPACE" >/dev/null 2>&1
}

remove_rg_locks() {
  az lock list --resource-group "$1" -o tsv --query "[].id" 2>/dev/null \
    | xargs -r -L1 az lock delete --ids >/dev/null 2>&1
}

# Poll until the workspace no longer exists (no built-in 'wait --deleted')
wait_ws_deleted() {
  local tries=0 max_tries=180
  while (( tries < max_tries )); do
    ! ws_exists && return 0
    sleep 10; ((tries++))
  done; return 1
}

wait_rg_deleted() {
  local rg="$1" tries=0 max_tries=180
  while (( tries < max_tries )); do
    ! rg_exists "$rg" && return 0
    sleep 10; ((tries++))
  done; return 1
}


# Attempt to discover managed RG if not supplied
discover_managed_rg() {
  local id ac_rg sa_rg

  # a. Ask the workspace itself which managed RG it uses
  if ws_exists; then
    id="$(az databricks workspace show \
      -g "$RG" -n "$WORKSPACE" \
      --query 'managedResourceGroupId' -o tsv 2>/dev/null || true)"
    [[ -n "$id" ]] && { echo "${id##*/}"; return; }
  fi

  # b. Fall back to the conventional "<workspace>-managed" name
  if rg_exists "${WORKSPACE}-managed"; then
    echo "${WORKSPACE}-managed"
    return
  fi

  # c. If there’s exactly one RG with access connectors, assume that’s it
  ac_rg="$(az resource list \
    --resource-type Microsoft.Databricks/accessConnectors \
    -o tsv --query "[].resourceGroup" 2>/dev/null | sort -u || true)"
  [[ -n "$ac_rg" && "$(wc -l <<<"$ac_rg")" -eq 1 ]] && { echo "$ac_rg"; return; }

  # d. If there’s exactly one RG containing a dbstorage account, assume that’s it
  sa_rg="$(az storage account list \
    -o tsv --query "[?contains(name,'dbstorage')].resourceGroup" 2>/dev/null | sort -u || true)"
  [[ -n "$sa_rg" && "$(wc -l <<<"$sa_rg")" -eq 1 ]] && { echo "$sa_rg"; return; }

  echo ""
}


# Remove all RBAC roles for connector identity
strip_connector_rbac() {
  local id="$1" principal ra_ids

  # Look up the service principal ID for this connector
  principal="$(az resource show --ids "$id" \
    --query "identity.principalId" -o tsv 2>/dev/null || true)"
  [[ -z "$principal" ]] && return 0

  # Get all role assignment IDs for this principal
  ra_ids="$(az role assignment list --assignee "$principal" \
    -o tsv --query "[].id" 2>/dev/null || true)"
  [[ -z "$ra_ids" ]] && return 0

  # Remove each role assignment
  while IFS= read -r rid; do
    [[ -n "$rid" ]] && az role assignment delete --ids "$rid" >/dev/null 2>&1 || true
  done <<<"$ra_ids"
}


# Delete Databricks access connectors in a resource group
delete_access_connectors_in_rg() {
  local rg="$1" ids name

  # Skip if RG not provided or doesn’t exist
  [[ -z "$rg" ]] || rg_exists "$rg" || return 0

  # List connector IDs in this RG
  ids="$(az databricks access-connector list \
    -g "$rg" --query "[].id" -o tsv 2>/dev/null || true)"
  [[ -z "$ids" ]] && return 0

  echo "Deleting access connectors in RG '$rg'..."

  while IFS= read -r id; do
    [[ -z "$id" ]] && continue

    # Remove role assignments before deleting
    strip_connector_rbac "$id"

    # Try to delete by name, fall back to generic resource delete
    name="$(az resource show --ids "$id" --query name -o tsv 2>/dev/null || true)"
    [[ -n "$name" ]] && {
      az databricks access-connector delete -g "$rg" -n "$name" --yes >/dev/null 2>&1 \
        || az resource delete --ids "$id" >/dev/null 2>&1 || true
    }
  done <<<"$ids"
}


# Delete storage accounts in a resource group
delete_storage_accounts_in_rg() {
  local rg="$1"

  # Skip if RG not provided or doesn’t exist
  [[ -z "$rg" ]] && return 0
  rg_exists "$rg" || return 0

  # List and delete storage accounts in the RG
  az storage account list -g "$rg" -o tsv --query "[].name" 2>/dev/null \
    | while IFS= read -r sa; do
        [[ -z "$sa" ]] && continue
        echo "Deleting storage account '$sa' in RG '$rg'..."
        az storage account delete -g "$rg" -n "$sa" --yes >/dev/null 2>&1 || true
      done
}


# --- Begin teardown execution ---
echo "Teardown: RG=$RG WORKSPACE=$WORKSPACE"

# Discover managed RG if not provided
if [[ -z "${MANAGED_RG:-}" ]]; then
  MANAGED_RG="$(discover_managed_rg || true)"
fi
echo "Discovered MANAGED_RG=${MANAGED_RG:-<unknown>}"


# 1. Delete Databricks workspace
if ws_exists; then
  echo "Deleting Databricks workspace '$WORKSPACE'..."

  # Kick off workspace deletion
  az databricks workspace delete -g "$RG" -n "$WORKSPACE" --yes >/dev/null 2>&1 || true

  # Wait until the workspace is really gone, warn if not
  wait_ws_deleted \
    || echo "WARNING: timed out waiting for workspace deletion; continuing..."
fi


# 2. Remove access connectors (main + managed RGs)
delete_access_connectors_in_rg "$RG"
delete_access_connectors_in_rg "${MANAGED_RG:-}"


# 3. Delete storage accounts
delete_storage_accounts_in_rg "${MANAGED_RG:-}"
delete_storage_accounts_in_rg "$RG"


# 4. Delete managed resource group
if [[ -n "${MANAGED_RG:-}" ]] && rg_exists "$MANAGED_RG"; then
  echo "Deleting managed RG '$MANAGED_RG'..."

  # Remove any locks before attempting deletion
  remove_rg_locks "$MANAGED_RG" || true

  # Kick off the delete (no-wait so we can poll manually)
  az group delete --name "$MANAGED_RG" --yes --no-wait >/dev/null 2>&1 || true

  # Wait until the RG is actually gone, warn if not
  wait_rg_deleted "$MANAGED_RG" \
    || echo "WARNING: Managed RG '$MANAGED_RG' still present; check locks/policies."
fi


# 5. Delete main resource group
if rg_exists "$RG"; then
  echo "Deleting main RG '$RG'..."

  # Remove any locks before attempting deletion
  remove_rg_locks "$RG" || true

  # Kick off the delete (no-wait so we can poll manually)
  az group delete --name "$RG" --yes --no-wait >/dev/null 2>&1 || true

  # Wait until the RG is actually gone, warn if not
  wait_rg_deleted "$RG" \
    || echo "WARNING: RG '$RG' still present; check locks/policies."
fi

echo "Teardown complete. (NetworkWatcherRG is left intact.)"