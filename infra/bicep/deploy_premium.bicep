// infra/bicep/deploy.bicep
// KardiaFlow infra: ADLS Gen2 + Databricks (v1.6 · 2025-07-25).
// Creates storage account/containers and a Premium Databricks workspace.
// Demo posture keeps public access enabled; harden for production.

targetScope = 'resourceGroup'


@description('Azure region')
param location string = resourceGroup().location

@description('Databricks workspace name')
param databricksWorkspaceName string = 'kardia-dbx'

@description('Managed resource group for Databricks')
param managedRgName string = 'kardia-dbx-managed'

@description('ADLS Gen2 account name (lowercase)')
param adlsAccountName string = 'kardiaadlsdemo'

@description('Raw container name')
param adlsRawContainerName string = 'raw'


// ADLS Gen2
resource adls 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: adlsAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    // Public endpoint remains enabled for the demo.
    // Hardened deployments should set this to 'Disabled'.
    publicNetworkAccess: 'Enabled'
  }
}

resource adlsBlob 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent: adls
  name: 'default'
  properties: {}
}

resource adlsLake 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = {
  parent: adlsBlob
  name: 'lake'
  properties: {
    publicAccess: 'None'
  }
}


// Databricks
resource databricks 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name: databricksWorkspaceName
  location: location
  sku: {
    name: 'premium'
  }
  properties: {
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups', managedRgName)

    // Public endpoint remains enabled for the demo.
    // Hardened deployments should set this to 'Disabled'.
    publicNetworkAccess: 'Enabled'

    // Use legacy Hive metastore only (prevents Unity Catalog creation).
    defaultCatalog: {
      initialType: 'HiveMetastore'
    }

    parameters: {
      enableNoPublicIp: {
        value: false
      }
    }
  }
}


// Outputs
output databricksUrl string = databricks.properties.workspaceUrl
