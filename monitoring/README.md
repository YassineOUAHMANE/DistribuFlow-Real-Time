\# Monitoring Setup



This directory contains the monitoring infrastructure for the cybersecurity attack detection project.



\## Components



\- \*\*Prometheus\*\*: Metrics collection and storage

\- \*\*Grafana\*\*: Metrics visualization and dashboards

\- \*\*Alertmanager\*\*: Alert management

\- \*\*Node Exporter\*\*: System-level metrics

\- \*\*Kube State Metrics\*\*: Kubernetes cluster metrics



\## Prerequisites



\- Minikube running with at least 8GB RAM and 4 CPUs

\- kubectl configured

\- Ansible installed (optional, can use manual commands)



\## Installation



\### Method 1: Using Ansible (Recommended)

```bash

\# Install Ansible if needed

pip install ansible



\# Run the playbook

ansible-playbook monitoring/setup-prometheus-grafana.yaml

```



\### Method 2: Manual Installation

```bash

\# Create namespace

kubectl create namespace monitoring



\# Install Helm

curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash



\# Add Prometheus Helm repo

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo update



\# Install kube-prometheus-stack

helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \\

&nbsp; --namespace monitoring \\

&nbsp; --set prometheus.prometheusSpec.retention=30d \\

&nbsp; --set grafana.adminPassword=admin \\

&nbsp; --set grafana.service.type=NodePort



\# Wait for pods to be ready

kubectl wait --for=condition=ready pod --all -n monitoring --timeout=600s

```



\## Accessing Grafana



\### Via NodePort

```bash

\# Get the URL

echo "http://$(minikube ip):$(kubectl get svc kube-prometheus-stack-grafana -n monitoring -o jsonpath='{.spec.ports\[0].nodePort}')"

```



\### Via Port Forwarding

```bash

kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

\# Then open: http://localhost:3000

```



\*\*Default credentials:\*\*

\- Username: `admin`

\- Password: `admin`



\## Accessing Prometheus

```bash

kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

\# Then open: http://localhost:9090

```



\## Pre-configured Dashboards



Grafana comes with 50+ pre-built dashboards including:



\- Kubernetes / Compute Resources / Cluster

\- Kubernetes / Compute Resources / Namespace (Pods)

\- Kubernetes / Networking / Cluster

\- Node Exporter / Nodes

\- Prometheus / Overview



\## Custom Dashboards (TODO)



We need to create custom dashboards for:



\- \[ ] Attack detection rates by type

\- \[ ] Kafka topic throughput and lag

\- \[ ] Spark job processing metrics

\- \[ ] ML model inference latency

\- \[ ] False positive/negative rates



\## Monitoring Architecture

```

┌─────────────────────────────────────────┐

│         Kubernetes Cluster              │

│                                         │

│  ┌────────────┐  ┌──────────────┐     │

│  │   Kafka    │  │    Spark     │     │

│  │  (Metrics) │  │  (Metrics)   │     │

│  └─────┬──────┘  └──────┬───────┘     │

│        │                 │             │

│        └────────┬────────┘             │

│                 ▼                      │

│         ┌──────────────┐               │

│         │  Prometheus  │               │

│         │   (Scrape)   │               │

│         └──────┬───────┘               │

│                ▼                       │

│         ┌──────────────┐               │

│         │   Grafana    │               │

│         │ (Visualize)  │               │

│         └──────────────┘               │

└─────────────────────────────────────────┘

```



\## Cleanup

```bash

\# Uninstall monitoring stack

helm uninstall kube-prometheus-stack -n monitoring



\# Delete namespace

kubectl delete namespace monitoring

```

