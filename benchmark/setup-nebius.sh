#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
context=nebius-inference-benchmark
kubectl --context "$context" apply -f vllm/inference-gpu.yaml
kubectl --context "$context" apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.0/standard-install.yaml
helm upgrade --install agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds --version v1.5.0 --kube-context "$context" --namespace agentgateway-system --create-namespace --wait
helm upgrade --install agentgateway oci://cr.agentgateway.dev/charts/agentgateway --version v1.5.0 --kube-context "$context" --namespace agentgateway-system --wait
kubectl --context "$context" apply -f agentgateway/agentgateway.yaml -f agentgateway/agentgateway-backend.yaml -f agentgateway/agentgateway-route.yaml -f agentgateway/agentgateway-rate-limit.yaml
kubectl --context "$context" apply -f monitoring/agentgateway-metrics-service.yaml -f monitoring/prometheus.yaml
kubectl --context "$context" -n inference rollout status deployment/vllm --timeout=20m
kubectl --context "$context" -n agentgateway-system rollout status deployment/inference-gateway --timeout=5m
kubectl --context "$context" -n monitoring rollout status deployment/prometheus --timeout=5m
