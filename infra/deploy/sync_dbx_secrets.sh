#!/usr/bin/env bash
# Sync AD app creds into a Databricks secret scope (idempotent).
set -euo pipefail

: "${SCOPE:=kardia}"                           # default scope
: "${CLIENT_ID:?Set CLIENT_ID in env}"         # bare GUID
: "${TENANT_ID:?Set TENANT_ID in env}"         # bare GUID
: "${CLIENT_SECRET:?Set CLIENT_SECRET in env}" # raw string

# Make sure scope exists (ignore "already exists" error)
databricks secrets create-scope --scope "$SCOPE" --initial-manage-principal users >/dev/null 2>&1 || true

# Write/overwrite values
databricks secrets put --scope "$SCOPE" --key sp_client_id     --string-value "$CLIENT_ID"
databricks secrets put --scope "$SCOPE" --key sp_tenant_id     --string-value "$TENANT_ID"
databricks secrets put --scope "$SCOPE" --key sp_client_secret --string-value "$CLIENT_SECRET"

echo "Synced Databricks secrets to scope '$SCOPE'."
