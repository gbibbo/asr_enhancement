from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASOURCE_YAML = REPO_ROOT / "infra/grafana/provisioning/datasources/prometheus.yml"
DASHBOARDS_YAML = REPO_ROOT / "infra/grafana/provisioning/dashboards/dashboards.yml"
DASHBOARD_JSON = REPO_ROOT / "infra/grafana/dashboards/asr_operational.json"

FORBIDDEN_PANEL_SUBSTRINGS = (
    "WER",
    "CER",
    "preset ranking",
    "experiment",
    "quality",
    "business",
)


def test_datasource_yaml_parses():
    data = yaml.safe_load(DATASOURCE_YAML.read_text())
    assert data["apiVersion"] == 1
    datasources = data["datasources"]
    assert len(datasources) == 1
    ds = datasources[0]
    assert ds["name"] == "Prometheus"
    assert ds["type"] == "prometheus"
    assert ds["url"] == "http://prometheus:9090"
    assert ds["uid"] == "prometheus"


def test_dashboards_provider_yaml_parses():
    data = yaml.safe_load(DASHBOARDS_YAML.read_text())
    assert data["apiVersion"] == 1
    providers = data["providers"]
    assert len(providers) >= 1
    provider = providers[0]
    assert provider["options"]["path"] == "/var/lib/grafana/dashboards"
    assert provider["type"] == "file"


def test_operational_dashboard_json_parses():
    data = json.loads(DASHBOARD_JSON.read_text())
    assert data["uid"] == "asr-operational"
    assert "Operational" in data["title"]
    panels = data["panels"]
    assert len(panels) >= 5

    top_ds = data["datasource"]
    assert top_ds == {"type": "prometheus", "uid": "prometheus"}

    for panel in panels:
        title = panel.get("title", "")
        for forbidden in FORBIDDEN_PANEL_SUBSTRINGS:
            assert forbidden.lower() not in title.lower(), (
                f"Panel title contains forbidden substring '{forbidden}': {title}"
            )
        for target in panel.get("targets", []):
            ds = target.get("datasource")
            assert ds is not None, f"Panel '{title}' target has no datasource"
            assert ds.get("uid") == "prometheus", (
                f"Panel '{title}' target datasource uid != 'prometheus': {ds}"
            )
