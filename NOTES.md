# NOTES
- 2026-10-11: static validation green (18/18 kubeconform, 10/10 pytest). No cluster.
- Real catches: stale chart versions (kyverno 3.5.2→3.9.1, trivy-operator 0.30.0→0.37.0, kps 77→92.3.0) and the Sealed Secrets repo move to bitnami.github.io.
- Interview angles: pull vs push deploys, selfHeal as drift control, why AppProject restrictions matter (an Application is effectively cluster-admin otherwise), sync waves vs CRD ordering, secrets in GitOps (SealedSecrets vs SOPS vs External Secrets).
- Next: kind + ArgoCD in CI, `helm template` + kubeconform of chart output, Renovate for chart bumps.
