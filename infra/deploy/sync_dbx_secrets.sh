#!/usr/bin/env bash
# sync_dbx_secrets.sh
# Uploads Azure service principal credentials into a Databricks secret scope.
# This script is idempotent — it will create or update secrets as needed.

set -euo pipefail

# Set secret scope (if not already defined)
: "${SCOPE:=kardia}"                           # default scope

# Verify required env vars are set
: "${CLIENT_ID:?Set CLIENT_ID in env}"         # bare GUID
: "${TENANT_ID:?Set TENANT_ID in env}"         # bare GUID
: "${CLIENT_SECRET:?Set CLIENT_SECRET in env}" # raw string

# Ensure the Databricks secret scope exists (no-op if already created)
databricks secrets create-scope --scope "$SCOPE" --initial-manage-principal users >/dev/null 2>&1 || true

# Upload all credentials to the secret scope
databricks secrets put --scope "$SCOPE" --key sp_client_id     --string-value "$CLIENT_ID"
databricks secrets put --scope "$SCOPE" --key sp_tenant_id     --string-value "$TENANT_ID"
databricks secrets put --scope "$SCOPE" --key sp_client_secret --string-value "$CLIENT_SECRET"

echo "Synced service principal credentials to Databricks scope '$SCOPE'."