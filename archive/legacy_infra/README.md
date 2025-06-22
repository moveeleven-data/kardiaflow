# KardiaFlow – Azure Data Factory Linked Services

This document describes the four linked services configured in Azure Data Factory (`kardiaflow-adf`) to support the KardiaFlow ingestion pipelines. Each linked service connects to a source or target system and defines the integration runtime, authentication, and other connection properties.

---

## 1. `ls_oracle_xe`

- **Type:** Oracle
- **Purpose:** Connects to Oracle XE 11g running in Docker
- **Integration Runtime:** `kardiaflow-shir` (Self-hosted Integration Runtime)
- **Authentication:** Username/password stored in **Azure Key Vault** (`oracle-pwd`)
- **Connection Notes:**
  - Uses `host.docker.internal:1521`
  - Requires Oracle Instant Client on SHIR host

---

## 2. `ls_postgres_claims`

- **Type:** PostgreSQL
- **Purpose:** Connects to local PostgreSQL 15 container exposing DB `claims`
- **Integration Runtime:** `kardiaflow-shir`
- **Authentication:** Username/password stored in **Azure Key Vault** (`pg-pwd`)
- **Connection Notes:**
  - Connects via `host.docker.internal:5433`
  - SSL disabled (local dev only)

---

## 3. `ls_mongo_healthcare`

- **Type:** MongoDB
- **Purpose:** Connects to MongoDB 7 container with `healthcare` DB
- **Integration Runtime:** `kardiaflow-shir`
- **Authentication:** No auth (default local mode)
- **Connection Notes:**
  - URI: `mongodb://host.docker.internal:27017/healthcare`
  - May append `?authSource=admin` if users are added

---

## 4. `ls_adls_bronze`

- **Type:** Azure Data Lake Storage Gen2
- **Purpose:** Destination for raw data files (bronze zone)
- **Integration Runtime:** `AutoResolveIntegrationRuntime` (cloud)
- **Authentication:** **Account key**, stored in **Azure Key Vault** (`adls-key`)
- **Connection Notes:**
  - Targets `kardiaflowstorage`
  - Hierarchical namespace enabled for Gen2 features

---

## Notes

- Self-Hosted IR (`kardiaflow-shir`) runs locally to bridge Docker-hosted databases to Azure.
- Key Vault name: `kardiaflow-kv`
- Each linked service was tested successfully as of `2025-06-02`.

