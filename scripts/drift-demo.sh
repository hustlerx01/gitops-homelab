#!/usr/bin/env bash
# NOT RUN on the authoring box (no Docker/kind). Shows ArgoCD selfHeal reverting manual drift.
set -euo pipefail
kind create cluster --name homelab
kubectl create ns argocd
kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deploy/argocd-repo-server --timeout=300s
kubectl apply -f bootstrap/
echo "waiting for hello to sync..."; until kubectl -n hello get deploy hello >/dev/null 2>&1; do sleep 10; done
kubectl -n hello scale deploy hello --replicas=5          # manual drift
sleep 60; kubectl -n hello get deploy hello -o jsonpath='{.spec.replicas}{"\n"}'   # expect 2 (selfHeal)
