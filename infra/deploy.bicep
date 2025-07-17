// KardiaFlow minimal stack + ADLS raw landing (v1.3j · 2025-07-17)
targetScope = 'resourceGroup'

/*─────────────────────── Parameters ───────────────────────*/
@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Azure Databricks workspace name')
param databricksWorkspaceName string = 'kardia-dbx'

@description('Name of the Databricks managed resource group (must exist or be created separately).')
param managedRgName string = 'kardia-dbx-managed'

@description('Globally-unique storage account name for ADLS Gen2 (lowercase, 3–24 chars).')
param adlsAccountName string = 'kardiaadlsdemo'

@description('Container name to hold raw landing data.')
param adlsRawContainerName string = 'raw'

@description('Deployment timestamp tag value.')
param deploymentTimestamp string = utcNow()


/*─────────────────────── Common Tags ───────────────────────*/
var commonTags = {
  owner       : 'KardiaFlow'
  env         : 'dev'
  costCenter  : 'data-engineering'
  billingTier : 'minimal'
  provisioned : deploymentTimestamp
}


/*──────────────────── ADLS Gen2 Storage ────────────────────*/

// Storage account with hierarchical namespace (ADLS Gen2)
resource adls 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name     : adlsAccountName
  location : location
  tags     : commonTags
  sku      : {
    name: 'Standard_LRS'                             // lowest-cost redundancy
  }
  kind     : 'StorageV2'
  properties: {
    isHnsEnabled             : true                  // enable hierarchical namespace (required for ADLS)
    allowBlobPublicAccess    : false                 // block anonymous access
    minimumTlsVersion        : 'TLS1_2'
    supportsHttpsTrafficOnly : true
    publicNetworkAccess      : 'Enabled'             // avoid PE/NAT cost in demo
  }
}

// Required default blob service (parent to containers)
resource adlsBlob 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent     : adls
  name       : 'default'
  properties : {}
}

// Raw landing container (e.g., for providers, claims)
resource adlsRaw 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = {
  parent     : adlsBlob
  name       : adlsRawContainerName
  properties : {
    publicAccess: 'None'                             // block public read access
  }
}


/*───────────────────── Databricks Workspace ─────────────────────*/
resource databricks 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name     : databricksWorkspaceName
  location : location
  tags     : commonTags
  sku      : {
    name: 'standard'
  }
  properties: {
    managedResourceGroupId : '/subscriptions/${subscription().subscriptionId}/resourceGroups/${managedRgName}'
    publicNetworkAccess    : 'Enabled'
    parameters: {
      enableNoPublicIp: {
        value: false                                     // allow public IPs (no NAT)
      }
    }
  }
}


/*──────────────────────── Outputs ────────────────────────*/

// Databricks workspace URL (e.g., adb-xxxx.azuredatabricks.net)
output databricksUrl string = databricks.properties.workspaceUrl

// Environment-aware storage suffix (e.g., core.windows.net, core.usgovcloudapi.net, etc.)
var storageSuffix = environment().suffixes.storage

// Convenience ABFSS URI for raw container (for Spark config)
// abfss://<container>@<acct>.dfs.<suffix>/
output adlsRawUri string = 'abfss://${adlsRawContainerName}@${adlsAccountName}.dfs.${storageSuffix}/'

// Storage account name (used in notebook Spark config)
output adlsAccount string = adls.name
