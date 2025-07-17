// KardiaFlow minimal ADLS + Databricks w/ storage MSI (v1.4c · 2025-07-17)
targetScope = 'resourceGroup'

/*──────────────────── Parameters ────────────────────*/
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

/*──────────────── ADLS Gen2 Storage ─────────────────*/
resource adls 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name     : adlsAccountName
  location : location
  sku      : { name: 'Standard_LRS' }
  kind     : 'StorageV2'
  properties: {
    isHnsEnabled             : true
    allowBlobPublicAccess    : false
    minimumTlsVersion        : 'TLS1_2'
    supportsHttpsTrafficOnly : true
    publicNetworkAccess      : 'Enabled'
  }
}

resource adlsBlob 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent     : adls
  name       : 'default'
  properties : {}
}

resource adlsRaw 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = {
  parent     : adlsBlob
  name       : adlsRawContainerName
  properties : { publicAccess: 'None' }
}

/*──────── Databricks Workspace ────────────────────*/
resource databricks 'Microsoft.Databricks/workspaces@2025-03-01-preview' = {
  name     : databricksWorkspaceName
  location : location
  sku      : { name: 'standard' }
  tags     : {
    owner       : 'KardiaFlow'
    env         : 'dev'
    costCenter  : 'data-engineering'
    billingTier : 'minimal'
  }
  properties: {
    managedResourceGroupId : '/subscriptions/${subscription().subscriptionId}/resourceGroups/${managedRgName}'
    publicNetworkAccess    : 'Enabled'
    parameters: {
      enableNoPublicIp: { value: false }
    }
    // Enable system‑assigned storage identity for MSI access
    storageAccountIdentity: {}
  }
}

/*── Grant Blob Data Reader to workspace storage MSI ───*/
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  // static name so Bicep can calculate at compile time
  name : guid(resourceGroup().id, adlsRaw.id, 'reader')
  scope: adlsRaw
  properties: {
    // Use the storage MSI principal from workspace properties
    principalId     : databricks.properties.storageAccountIdentity.principalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'  // Storage Blob Data Reader
    )
  }
}

/*──────────────────── Outputs ────────────────────*/
var suffix = environment().suffixes.storage

output adlsRawUri   string = 'abfss://${adlsRawContainerName}@${adlsAccountName}.dfs.${suffix}/'
output databricksUrl string = databricks.properties.workspaceUrl
