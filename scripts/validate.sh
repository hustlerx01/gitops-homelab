#!/usr/bin/env bash
# Offline-ish validation: kustomize build every git-sourced path + kubeconform (strict) with CRD schemas.
set -euo pipefail; cd "$(dirname "$0")/.."
OUT=${OUT:-results}; mkdir -p "$OUT/rendered"
K8S=${K8S_VERSION:-1.33.0}
CRD='https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'
for d in platform/namespaces platform/kyverno-policies workloads/hello/overlays/homelab; do
  kustomize build "$d" > "$OUT/rendered/$(echo $d | tr / _).yaml"
done
kubeconform -strict -summary -output text -kubernetes-version "$K8S" \
  -schema-location default -schema-location "$CRD" \
  bootstrap/ apps/ "$OUT/rendered/" | tee "$OUT/kubeconform.txt"
