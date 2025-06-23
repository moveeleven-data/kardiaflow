# KardiaFlow: Azure-Based Healthcare Data Platform

## Scenario

This project simulates a hospital network integrating data from multiple
heterogeneous healthcare systems. The aim is to replicate the challenges of 
ingesting, transforming, validating, and securing sensitive healthcare data
in a modern, cloud-native environment.

### Architecture Overview

This high-level diagram shows how structured and semi-structured healthcare data flows from ingestion to transformation, validation, and secure storage using Azure-native tools.

![KardiaFlow Architecture](https://github.com/okv627/KardiaFlow/docs/kardiaflow.lineage.png)

### Data Sources

- **EHR Data (Structured)** — from an on-prem Oracle or SQL Server instance:
  - `patients.csv`: demographic and ID information
  - `encounters.csv`: hospital visit metadata
  - `procedures.csv`: performed medical procedures

- **Insurance Claims Data (Structured)** — stored in a PostgreSQL database:
  - `claims.csv`: claim cost, provider, coverage, billing codes
  - `providers.csv`: metadata about insurers and medical providers

- **Patient Feedback / Device Logs (Semi-Structured)** — stored in MongoDB:
  - `feedback.json`: patient satisfaction surveys
  - `device_data.json`: wearable health metrics (e.g., heart rate, step count)

---

## Goals

Design and implement an end-to-end, cloud-based data engineering pipeline that:

- Ingests structured and semi-structured data using **Azure Data Factory (ADF)**
- Cleans, joins, and transforms data using **Azure Databricks with PySpark**
- Stores analytics-ready datasets in **PostgreSQL or Azure SQL Database**
- Simulates compliance with **HIPAA Security Rule** through masking and governance
- Implements **automated data validation** using **QuerySurge**, **Datagaps**,
- or Python/SQL-based assertions

---

## Tech Stack

| Layer        | Tools / Services                                   |
|--------------|----------------------------------------------------|
| **Cloud**    | Azure Data Factory, Azure Databricks               |
| **Compute**  | PySpark on Databricks                              |
| **Databases**| Oracle XE, SQL Server, PostgreSQL, MongoDB         |
| **Validation**| QuerySurge, Datagaps (or custom SQL/Python checks) |
| **DevOps**   | Docker, GitHub, Python virtualenv, CLI tools       |

---

## Compliance Focus

This project simulates responsible healthcare data practices by incorporating:

- **Simulated HIPAA Security Rule adherence**, especially regarding ePHI
- **PHI identification and masking** for fields like name, birthdate, and medical record number
- **Security best practices**, such as separation of secrets, encryption in transit, and audit logging
- **Data governance artifacts**, including data lineage diagrams, update frequency, and ownership tracking

---

### Note: Oracle XE Access via `sqlplus` (WSL)

To run SQL queries directly against our Oracle XE database, we use [`sqlplus`](https://docs.oracle.com/en/database/oracle/oracle-database/21/sqpug/using-SQL-Plus.html)—a command-line client bundled with Oracle's Instant Client. Since `sqlplus` is not available through `apt`, we install it manually.

We downloaded and extracted the following Linux packages into `~/oracle/`:
- `instantclient-basic-linux.x64-21.*.zip`
- `instantclient-sqlplus-linux.x64-21.*.zip`
- `instantclient-sdk-linux.x64-21.*.zip` (optional, for dev work)

After unzipping, we configured our environment by appending the following to `~/.zshrc` (or `~/.bashrc`):

export LD_LIBRARY_PATH=~/oracle/instantclient_21_*/:$LD_LIBRARY_PATH
export PATH=~/oracle/instantclient_21_*/:$PATH

Then reload the shell:
source ~/.zshrc

Now we connect to Oracle XE from WSL:
sqlplus system/oracle@//localhost:1521/XE
