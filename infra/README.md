# KardiaFlow Infrastructure Deployment Guide

This folder contains the infrastructure-as-code (IaC) scripts for safely deploying and tearing down the minimal KardiaFlow cloud environment in Azure using Bicep and the Azure CLI.

---

## What It Deploys

- Azure Resource Group (`kardia-rg-dev`)
- Azure Key Vault (`kardia-kv`)
- Azure Databricks Workspace (`kardia-dbx`)

This stack uses no VNet injection, no ADLS, no Unity Catalog, and no costly NAT Gateways — just a clean, safe, minimal dev environment.

---

## Deploy Instructions

> **Start from a clean shell session and ensure you're logged in to the correct Azure subscription.**

# 1. Create the dev resource group (required before deploying)
az group create --name kardia-rg-dev --location eastus

# 2. Run the deployment (this provisions Databricks, Key Vault, ADF)
az deployment group create \
  --resource-group kardia-rg-dev \
  --template-file infra/deploy.bicep

---

Teardown Instructions
Destroys all dev resources, including managed RGs.

# From the project root
./infra/teardown.sh

This script will:

Delete the Databricks workspace (which deletes the managed RG too)

Delete the main resource group (kardia-rg-dev)

Print a confirmation message

Resources will disappear over the next 2–5 minutes.

---

Dry-Run Deployment
To preview the deployment without applying:

az deployment group what-if \
  --resource-group kardia-rg-dev \
  --template-file automation/infra/deploy.bicep
