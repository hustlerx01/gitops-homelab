import os, pathlib, shutil, subprocess, urllib.request, pytest, yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
APPS = {p.stem: yaml.safe_load(p.read_text()) for p in (ROOT / "apps").glob("*.yaml")}
PROJ = yaml.safe_load((ROOT / "bootstrap/project.yaml").read_text())
REPO = yaml.safe_load((ROOT / "bootstrap/root-app.yaml").read_text())["spec"]["source"]["repoURL"]
need = pytest.mark.skipif(not (shutil.which("kubeconform") and shutil.which("kustomize")), reason="tools missing")

def test_every_app_is_in_restricted_project():
    assert all(a["spec"]["project"] == "homelab" for a in APPS.values())
    assert PROJ["spec"]["sourceRepos"] != ["*"]

def test_sources_allowed_by_project():
    allowed = set(PROJ["spec"]["sourceRepos"])
    for n, a in APPS.items(): assert a["spec"]["source"]["repoURL"] in allowed, n

def test_helm_charts_pinned_to_exact_semver():
    import re
    for n, a in APPS.items():
        s = a["spec"]["source"]
        if "chart" in s: assert re.fullmatch(r"\d+\.\d+\.\d+", s["targetRevision"]), n

def test_git_paths_exist_and_build():
    for n, a in APPS.items():
        s = a["spec"]["source"]
        if s["repoURL"] == REPO: assert (ROOT / s["path"] / "kustomization.yaml").exists(), n

def test_selfheal_prune_and_finalizer():
    for n, a in APPS.items():
        assert a["spec"]["syncPolicy"]["automated"] == {"prune": True, "selfHeal": True}, n
        assert "resources-finalizer.argocd.argoproj.io" in a["metadata"]["finalizers"]

def test_sync_waves_order_crds_before_users():
    w = {n: int(a["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"]) for n, a in APPS.items()}
    assert w["namespaces"] < w["kyverno"] < w["kyverno-policies"]   # policy CRDs exist before ClusterPolicy
    assert w["sealed-secrets"] < w["hello"]                          # SealedSecret CRD before workload

def test_no_plaintext_secrets_in_repo():
    for p in ROOT.rglob("*.yaml"):
        if ".git" in p.parts: continue
        for d in yaml.safe_load_all(p.read_text()):
            if isinstance(d, dict): assert d.get("kind") != "Secret", p

@need
def test_kubeconform_all_valid(tmp_path):
    p = subprocess.run(["./scripts/validate.sh"], cwd=ROOT, env={**os.environ, "OUT": str(tmp_path)}, capture_output=True, text=True)
    assert p.returncode == 0 and "Invalid: 0, Errors: 0, Skipped: 0" in p.stdout, p.stdout + p.stderr

@need
def test_kubeconform_catches_typo(tmp_path):
    bad = yaml.safe_load((ROOT / "apps/hello.yaml").read_text())
    bad["spec"]["syncPolicy"]["automated"]["selfheal"] = True        # wrong case
    (tmp_path / "bad.yaml").write_text(yaml.safe_dump(bad))
    crd = "https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json"
    p = subprocess.run(["kubeconform", "-strict", "-schema-location", "default", "-schema-location", crd, str(tmp_path / "bad.yaml")], capture_output=True, text=True)
    assert p.returncode != 0 and "selfheal" in p.stdout

@pytest.mark.skipif(os.environ.get("OFFLINE") == "1", reason="offline")
def test_pinned_chart_versions_exist_upstream():
    for n, a in APPS.items():
        s = a["spec"]["source"]
        if "chart" not in s: continue
        idx = yaml.safe_load(urllib.request.urlopen(s["repoURL"].rstrip("/") + "/index.yaml", timeout=30).read())
        assert s["targetRevision"] in {e["version"] for e in idx["entries"][s["chart"]]}, n
