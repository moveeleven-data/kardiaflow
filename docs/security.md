## Kardiaflow Security Policy

### Overview
Kardiaflow runs on Azure Databricks and is torn down after use. The focus is on keeping things safe and simple: no 
secrets in git, light CI checks, least-privilege storage access, basic data-quality tests, and a clean teardown.

### Secrets
Secrets are never committed. Credentials live in a Databricks secret scope and are read at runtime.

### CI Checks
A lightweight GitHub Actions workflow runs on pushes:
- **Gitleaks** scans for leaked secrets  
- **Checkov** scans `infra/bicep` for IaC issues

### Infrastructure
Blob public access is disabled, and TLS 1.2 with HTTPS-only traffic is enforced. For simplicity, 
`publicNetworkAccess` remains Enabled on ADLS and Databricks. Stronger hardening options (private endpoints, 
customer-managed keys) are intentionally left out to keep the setup straightforward.

### Access
The service principal has Storage Blob Data Contributor at the container (or account if container scope isn’t available). Broad Owner/Contributor rights are not used.

### Teardown
Resources are cleaned up with scripts under `infra/deploy/`. The environment is not intended to stay up beyond a demo run.
