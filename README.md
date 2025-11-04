# spezielleProg – Cloud & DevOps Infrastructure

This repository contains the complete DevOps and cloud infrastructure setup for a Python-based service.  
It’s built around modern container and orchestration practices — **Docker for packaging**, **Kubernetes for orchestration**, and **Helm** for reproducible deployments.  
The project is structured for real-world cloud environments, focusing on **automation**, **security**, and **observability** rather than manual configuration.

---

## 🌍 Overview

The main goal of this setup is to make deployments predictable, secure, and portable across different environments (local, staging, production).

The stack includes:
- **Docker** for image creation and reproducibility  
- **Kubernetes** for workload management and scaling  
- **Helm** for parameterized deployments  
- **Trivy** for vulnerability scanning  
- **n8n (self-hosted)** for event-driven automation and failure notifications  
- **(Optional)** Prometheus & Grafana for monitoring and alerting  
- **(Optional)** GitHub Actions or GitLab CI/CD for continuous delivery  

Everything is written to be minimal, transparent, and easily customizable.

---

## 🧱 Repository Structure

```text
.
├─ Dockerfile                 # Defines the container build
├─ requirements.txt           # Python runtime dependencies
├─ kubernetes/                # Base manifests for K8s deployment
│  ├─ deployment.yaml
│  ├─ service.yaml
│  ├─ configmap.yaml
│  └─ secret.yaml
├─ helm/
│  └─ smartops/               # Reusable Helm chart for production rollouts
│     ├─ Chart.yaml
│     ├─ values.yaml
│     └─ templates/
├─ trivy-results.json         # Example output from security scanning
└─ .github/workflows/         # (Optional) GitHub Actions CI/CD
```

Each layer is isolated but works together.
You can deploy the project directly with`kubectl` or use the Helm chart for parameterized multi-environment releases.

## 🐳 Docker
# Build
```bach
docker build -t spezielleprog:latest .
```
# Run locally
```bach
docker run --rm -it \
  -e APP_ENV=local \
  -e LOG_LEVEL=INFO \
  -p 8080:8080 \
  spezielleprog:latest
```
If your application expects other environment variables (tokens, URLs, secrets), they can be mounted through `.env` or passed directly at runtime.
## ☸️ Kubernetes Deployment
### Option 1: Using plain manifests
You can deploy manually to a cluster:
```bach
kubectl apply -f kubernetes/
kubectl get pods -n spezielleprog
```
Typical manifest responsibilities:
`deployment.yaml` defines the pod and container setup
`service.yaml` exposes the app inside the cluster
`configmap.yaml` provides runtime configuration
`secret.yaml` stores sensitive values like API tokens
### Option 2: Helm Deployment (recommended)
Helm makes versioning and parameterization easier:
```bach
helm upgrade --install spezielleprog ./helm/smartops \
  --namespace spezielleprog --create-namespace \
  --set image.repository=spezielleprog \
  --set image.tag=latest \
  --set env.APP_ENV=prod \
  --set env.LOG_LEVEL=INFO
```
#### Common Helm values

| Key | Description | Example |
|-----|--------------|----------|
| `image.repository` | Docker image repository | `ghcr.io/mojeeeb/spezielleprog` |
| `image.tag` | Image tag | `latest` |
| `env.APP_ENV` | Runtime environment | `prod` / `dev` |
| `env.LOG_LEVEL` | Logging level | `INFO` |
| `resources.requests` | CPU/Memory requests | `250m / 256Mi` |
| `resources.limits` | CPU/Memory limits | `500m / 512Mi` |

The Helm chart can be integrated easily into a CI/CD pipeline (see below).

## 🔒 Security Scanning
Security scanning is handled with Trivy, which checks for CVEs in system libraries and Python dependencies.
### Run locally
```bach
trivy image spezielleprog:latest --output trivy-results.json
```
You can also scan infrastructure configurations:
```bach
trivy config kubernetes/
```
### CI Integration Example (GitHub Actions)
```yaml
- name: Security Scan
  run: trivy image $IMAGE_NAME:$TAG --exit-code 1 --severity HIGH,CRITICAL
```
The repository includes an example `trivy-results.json` file for reference.

## 📡 Automation & Notifications
To improve observability and response times in case of build or runtime failures,
this setup integrates n8n, running on a self-hosted private server, as a lightweight automation layer.

Whenever a failure occurs for example, a failed Docker build, a Trivy security scan finding, or a Helm deployment error
an n8n workflow is triggered that automatically sends a Telegram notification to a predefined chat or channel.
### 🧩 Self-Hosted Setup
- Environment: n8n runs on a private VM using Docker Compose or systemd.
- Webhook Access: The CI/CD system sends POST requests to the private server via internal or VPN-secured network.
- Security: Webhook URLs are protected with authentication headers and IP whitelisting.
### Example server endpoint:
```text
https://n8n.internal.company.local/webhook/alert
```
#### 🔧 Example webhook payload
```text
{
  "project": "spezielleProg",
  "stage": "deployment",
  "status": "failed",
  "message": "Helm upgrade failed due to missing secret: BOT_TOKEN"
}
```

### 🚀 Telegram Notification Flow

1. The CI/CD pipeline sends a webhook to the private **n8n** instance.  
2. **n8n** parses the JSON payload and extracts error details.  
3. A **Telegram Bot Node** formats and sends the message to a predefined chat.

**Example message:**

> ⚠️ **Deployment failed**  
> Project: `spezielleProg`  
> Stage: `deployment`  
> Message: Helm upgrade failed due to missing secret: `BOT_TOKEN`

---

### ✅ Benefits

- Runs entirely inside **private infrastructure** (no external dependencies)  
- Immediate alerts for **CI/CD failures** or runtime errors  
- Easy to extend for **Slack**, **Discord**, or **email** integrations  
- Supports both **manual** and **automated** triggers
### Helm Configuration Notes
Your deployment parameters are managed through `values.yaml`.
Below is a simplified example showing key configuration blocks`
### ⚠️ Important:
Before deploying, make sure to update the n8n.webhookUrl value with your own
private n8n webhook endpoint.
This URL defines where your CI/CD pipeline sends alerts for build or deployment failures.
Example:
```yaml
n8n:
  webhookUrl: "https://n8n.yourdomain.local/webhook/alert"

```
This webhook is automatically used by the CI/CD pipeline to send real-time notifications via *n8n* 
ready for all your lovely automations ✨
## 📊 Observability (optional)
The setup supports integration with Prometheus and Grafana for metrics and dashboards.
Liveness and readiness probes should be defined to ensure rolling updates don’t disrupt traffic.
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 20

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```
### Recommended next steps:
Add Prometheus annotations to the deployment (`prometheus.io/scrape: "true`)
## Connect your cluster to Grafana dashboards via Prometheus datasource
🚀 Continuous Integration / Continuous Deployment
Below is an example of how a GitHub Actions pipeline can automate build, scan, and deployment steps.
```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t ghcr.io/mojeeeb/spezielleprog:${{ github.sha }} .

      - name: Push to GitHub Container Registry
        run: docker push ghcr.io/mojeeeb/spezielleprog:${{ github.sha }}

      - name: Run security scan
        run: trivy image ghcr.io/mojeeeb/spezielleprog:${{ github.sha }}

      - name: Deploy via Helm
        env:
          KUBECONFIG: ${{ secrets.KUBECONFIG }}
        run: |
          helm upgrade --install spezielleprog ./helm/smartops \
            --namespace spezielleprog \
            --set image.repository=ghcr.io/mojeeeb/spezielleprog \
            --set image.tag=${{ github.sha }}
```
For production, you can replace this with GitLab CI, Argo CD, or FluxCD for GitOps-style delivery.
## 🧩 Recommended Enhancements

- Add **Argo CD** for declarative, Git-driven deployments  
- Introduce **NetworkPolicies** for stricter pod communication  
- Enable **PodDisruptionBudgets** and **resource quotas**  
- Add **cosign** for image signing and verification  
- Integrate **Prometheus alerts** for latency, restart loops, or CPU saturation  
- Automate nightly **Trivy** scans and generate HTML reports

## 🧠 Philosophy

This repository is not about writing app logic — it’s about **running it properly.**  
It follows a simple principle:

> “Build once, deploy anywhere, monitor everything.”

By separating infrastructure concerns from application code,  
this setup makes your Python service fully cloud-native reproducible, secure, observable, and maintainable at scale.


## 🪶 Author’s Note
This repository is intentionally minimalistic but production-oriented.
Every piece — from Dockerfile to Helm values — is designed to be transparent and educational for anyone learning modern DevOps workflows.
If you’re deploying it in a real cluster, adjust resource limits, secrets, and monitoring targets to fit your environment.
