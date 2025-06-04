Day 1: Project Setup & Data Landscape Planning

Defined healthcare scenario (integrating EHR, claims, unstructured data).

Deliverable: Project summary (data sources, pipeline flow).

Selected synthetic datasets (Synthea, Kaggle).

Deliverable: Data files, data dictionary.

Set up Azure services, databases, source control.

Deliverable: Configured environment, test connections.

Designed pipeline architecture (Bronze-Silver-Gold).

Deliverable: Architecture diagram.

Day 2: Source Data Ingestion & Database Setup

Set up local databases (Oracle, PostgreSQL, MongoDB).

Deliverable: Populated source databases.

Validated data (row counts, aggregations).

Deliverable: Validation log.

Documented source schema (relationships, keys).

Deliverable: Schema documentation.

Day 3: Azure Data Factory – Batch Ingestion Pipeline

Provisioned Azure Data Factory.

Set up linked services for data sources (Oracle/SQL Server, PostgreSQL, MongoDB).

Deliverable: Linked services configured.

Built ADF pipeline to copy data to raw landing zone.

Deliverable: ADF pipeline, screenshot.

Monitored and verified data ingestion.

Deliverable: Ingestion run results.

Day 4: Databricks & PySpark – Batch Processing and Transformation

Set up Databricks workspace, cluster.

Deliverable: Notebook with data loading code.

Transformed data using PySpark (joins, cleaning, partitioning).

Deliverable: Transformation notebook.

Loaded transformed data into target store (PostgreSQL/Azure SQL).

Deliverable: Curated data output.

Optimized and documented transformation logic.

Deliverable: Data processing summary.

Day 5: Implementing a Basic Stream Processing Pipeline

Simulated streaming data via Python script.

Deliverable: Python script simulating stream.

Set up Spark structured streaming in Databricks.

Deliverable: Streaming notebook, logs.

Monitored streaming process.

Deliverable: Streaming run log.

Optional: Integrated streaming with ADF.

Deliverable: Integration notes.

Day 6: Data Warehouse and Reporting Preparation

Designed data warehouse schema (star/denormalized).

Deliverable: Schema diagram/description.

Implemented schema in PostgreSQL/Azure SQL.

Deliverable: SQL DDL scripts, tables.

Loaded data into warehouse.

Deliverable: Populated warehouse, integrity checks.

Validated with simple queries.

Deliverable: Query results/reports.

Day 7: Data Validation and Quality Checks

Performed data reconciliation with QuerySurge/Datagaps.

Deliverable: Reconciliation report.

Implemented data quality checks (Great Expectations).

Deliverable: Quality test results.

Addressed quality issues (nulls, mismatches).

Deliverable: Resolved issues.

Documented validation process.

Deliverable: Validation summary.

Day 8: Data Governance, Security & Compliance

Identified sensitive data (PHI) and applied compliance rules.

Deliverable: PHI inventory.

Implemented data masking and encryption.

Deliverable: Data masking evidence.

Secured pipeline (Azure Key Vault, encryption).

Deliverable: Security measures summary.

Documented data lineage and governance.

Deliverable: Data lineage/governance document.

Day 9: Declarative Pipelines with Delta Live Tables + Auto Loader

Created DLT pipeline (raw/clean layers, schema validation).

Deliverable: DLT pipeline, DAG screenshot.

Enabled schema evolution and tested rescue data.

Deliverable: Notebook showing schema changes.

Implemented CDC for incremental data.

Deliverable: CDC query result.

Day 10: Unity Catalog Governance + Serverless SQL & BI

Implemented Unity Catalog for governance and access control.

Deliverable: Unity Catalog scripts.

Set up serverless SQL warehouse and ran analytics.

Deliverable: Serverless SQL queries.

Tested BI connector (Power BI/Tableau).

Deliverable: KPI dashboard.

Noted performance (Photon).

Deliverable: Performance/cost note.

Day 11: Delta Lake 4.0, Iceberg/UniForm & Delta Sharing + Clean Rooms

Upgraded to Delta 4.0 features (CDF, ZORDER).

Deliverable: Delta 4.0 optimizations.

Created UniForm table, tested Iceberg interoperability.

Deliverable: Query result.

Configured Delta Sharing and published data.

Deliverable: Delta sharing setup.

Implemented clean-room policy.

Deliverable: Clean-room policy.

Day 12: Workflows, Observability, CI/CD & AI Demo

Built Databricks Workflow DAG for data pipeline.

Deliverable: Workflow graph, job JSON.

Set up event logging and alerts.

Deliverable: Event-log query, alert.

Set up GitHub Actions for CI/CD.

Deliverable: GitHub Actions YAML.

Integrated AI demo for semantic search.

Deliverable: AI-based matching notebook.

Changelog Integration (2025-06-03):

Developed ADF pipelines for Oracle, PostgreSQL, MongoDB data ingestion into ADLS Gen2.

Validated ingestion and set up ADF logging.

Set up Databricks for PySpark transformations; loaded data into ADLS Gen2, performing initial schema exploration and transformations (e.g., joins, handling missing values, new fields).

Verified data output, preparing for next steps.