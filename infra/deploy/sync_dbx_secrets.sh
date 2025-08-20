#!/usr/bin/env bash
# infra/deploy/sync_dbx_secrets.sh
# Ensure Databricks secret scope exists and upsert SP credentials.
# Inputs: SCOPE, TENANT_ID, CLIENT_ID, CLIENT_SECRET (env).

set -euo pipefail

: "${SCOPE:?SCOPE missing}"
: "${TENANT_ID:?TENANT_ID missing}"
: "${CLIENT_ID:?CLIENT_ID missing}"
: "${CLIENT_SECRET:?CLIENT_SECRET missing}"
command -v databricks >/dev/null || { echo "ERROR: Databricks CLI not found"; exit 1; }

# Ensure scope (new CLI positional; fall back to old flags quietly)
databricks secrets list-scopes -o json 2>/dev/null | grep -q "\"name\": *\"$SCOPE\"" || \
  databricks secrets create-scope "$SCOPE" --initial-manage-principal users >/dev/null 2>&1 || \
  databricks secrets create-scope --scope "$SCOPE" --initial-manage-principal users >/dev/null 2>&1 || true

# If still missing, fail clearly
databricks secrets list-scopes -o json 2>/dev/null | grep -q "\"name\": *\"$SCOPE\"" || {
  echo "ERROR: Secret scope '$SCOPE' doesn't exist and could not be created (check permissions)."
  exit 1
}

# Upsert secrets (positional SCOPE KEY)
databricks secrets put-secret "$SCOPE" sp_tenant_id     --string-value "$TENANT_ID"     >/dev/null
databricks secrets put-secret "$SCOPE" sp_client_id     --string-value "$CLIENT_ID"     >/dev/null
databricks secrets put-secret "$SCOPE" sp_client_secret --string-value "$CLIENT_SECRET" >/dev/null