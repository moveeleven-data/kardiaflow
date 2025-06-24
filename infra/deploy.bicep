// KardiaFlow minimal stack  (v1.3f · 2025-06-22)
targetScope = 'resourceGroup'

@description('Azure region for all resources')
param location string = resourceGroup().location

param keyVaultName            string = 'kardia-kv'
param databricksWorkspaceName string = 'kardia-dbx'
param managedRgName           string = 'kardia-dbx-managed'
param deploymentTimestamp     string = utcNow()

var commonTags = {
  owner       : 'KardiaFlow'
  env         : 'dev'
  costCenter  : 'data-engineering'
  billingTier : 'minimal'
  provisioned : deploymentTimestamp
}

/*──────── Key Vault ────────*/
resource kv 'Microsoft.KeyVault/vaults@2021-06-01-preview' = {
  name       : keyVaultName
  location   : location
  tags       : commonTags
  properties : {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name  : 'standard'
    }
    enableSoftDelete          : true
    softDeleteRetentionInDays : 7
    publicNetworkAccess       : 'Enabled'
    accessPolicies            : []
  }
}

/*──────── Databricks workspace — public IPs, NO NAT GW ────────*/
resource databricks 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name       : databricksWorkspaceName
  location   : location
  tags       : commonTags
  sku        : { name: 'standard' }
  properties : {
    managedResourceGroupId : '/subscriptions/${subscription().subscriptionId}/resourceGroups/${managedRgName}'
    publicNetworkAccess    : 'Enabled'
    parameters: {
      enableNoPublicIp: { value: false }
    }
  }
}

/*──────── Outputs ────────*/
output databricksUrl string = databricks.properties.workspaceUrl
output keyVaultUri   string = kv.properties.vaultUri
