from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ALERTS_YAML = REPO_ROOT / "infra/prometheus/alerts.yml"
PROMETHEUS_YAML = REPO_ROOT / "infra/compose/prometheus.yml"
COMPOSE_YAML = REPO_ROOT / "infra/compose/docker-compose.yml"


def _load_alerts():
    return yaml.safe_load(ALERTS_YAML.read_text())


def _alerts_by_name():
    data = _load_alerts()
    rules = data["groups"][0]["rules"]
    return {rule["alert"]: rule for rule in rules}


def test_alerts_yaml_parses():
    data = _load_alerts()
    groups = data["groups"]
    assert len(groups) == 1
    rules = groups[0]["rules"]
    assert len(rules) == 3


def test_alert_names_present():
    names = set(_alerts_by_name().keys())
    expected = {
        "ASRApiErrorRateHigh",
        "ASRQueueBacklogHigh",
        "ASRWorkerHeartbeatMissing",
    }
    assert expected == names, f"got {names}"


def test_api_error_rate_alert_uses_requests_metric():
    rule = _alerts_by_name()["ASRApiErrorRateHigh"]
    assert "asr_api_requests_total" in rule["expr"]


def test_queue_backlog_alert_uses_backlog_metric():
    rule = _alerts_by_name()["ASRQueueBacklogHigh"]
    assert "asr_queue_backlog_jobs" in rule["expr"]


def test_worker_heartbeat_alert_covers_stale_and_absent():
    rule = _alerts_by_name()["ASRWorkerHeartbeatMissing"]
    expr = rule["expr"]
    assert "asr_worker_heartbeat_timestamp_seconds" in expr
    assert "absent(" in expr


def test_compose_mounts_alert_rules_and_grafana():
    compose = yaml.safe_load(COMPOSE_YAML.read_text())
    services = compose["services"]

    # Prometheus mounts the alert rules file
    prom = services["prometheus"]
    prom_volumes = prom["volumes"]
    assert any(
        "infra/prometheus/alerts.yml" in v and "/etc/prometheus/alerts.yml" in v
        for v in prom_volumes
    ), f"prometheus volumes missing alerts mount: {prom_volumes}"

    # prometheus.yml references the rules file
    prom_cfg = yaml.safe_load(PROMETHEUS_YAML.read_text())
    assert "/etc/prometheus/alerts.yml" in prom_cfg.get("rule_files", [])

    # Grafana service exists with required wiring
    grafana = services["grafana"]
    assert "3000:3000" in grafana["ports"]
    grafana_volumes = grafana["volumes"]
    assert any(
        "infra/grafana/provisioning" in v and "/etc/grafana/provisioning" in v
        for v in grafana_volumes
    ), f"grafana provisioning mount missing: {grafana_volumes}"
    assert any(
        "infra/grafana/dashboards" in v and "/var/lib/grafana/dashboards" in v
        for v in grafana_volumes
    ), f"grafana dashboards mount missing: {grafana_volumes}"
    depends_on = grafana.get("depends_on", [])
    if isinstance(depends_on, dict):
        assert "prometheus" in depends_on
    else:
        assert "prometheus" in depends_on
