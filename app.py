"""Rank investigation hypotheses using only cited log/deployment evidence."""
from datetime import datetime, timezone


PATTERNS = {
    "database_connection": ("connection refused", "too many connections", "database unavailable"),
    "request_timeout": ("timeout", "deadline exceeded", "upstream timed out"),
    "configuration": ("missing environment", "invalid configuration", "secret not found"),
}
NEXT_CHECK = {
    "database_connection": "Check DB availability, pool limits, and connection settings.",
    "request_timeout": "Inspect downstream latency and request traces.",
    "configuration": "Compare environment variables and secrets with the previous release.",
    "recent_deployment": "Compare the new release with the previous version and consider rollback criteria.",
}


def _time(raw):
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)


def investigate(alert, logs, deployments):
    alert_time = _time(alert["at"])
    hypotheses = {}

    def add(cause, points, reference, observation):
        item = hypotheses.setdefault(cause, {"cause": cause, "score": 0, "evidence": []})
        item["score"] += points
        item["evidence"].append({"ref": reference, "observation": observation})

    seen_ids = set()
    for log in logs:
        if log["id"] in seen_ids:
            raise ValueError("Duplicate log ID")
        seen_ids.add(log["id"])
        delta = (alert_time - _time(log["at"])).total_seconds()
        if not (0 <= delta <= 3600):
            continue
        message = log["message"].lower()
        for cause, phrases in PATTERNS.items():
            if any(phrase in message for phrase in phrases):
                add(cause, 2, f"log:{log['id']}", "Matching error in the alert window")

    recent_deployments = []
    for deploy in deployments:
        delta = (alert_time - _time(deploy["at"])).total_seconds()
        if 0 <= delta <= 3600 and deploy.get("service") == alert["service"]:
            recent_deployments.append(deploy)
    if recent_deployments:
        most_recent = max(recent_deployments, key=lambda deploy: _time(deploy["at"]))
        add("recent_deployment", 1, f"deploy:{most_recent['id']}",
            "Same service deployed within one hour; timing alone does not establish causality")

    ranked = sorted(hypotheses.values(), key=lambda x: (-x["score"], x["cause"]))
    for item in ranked:
        item["next_check"] = NEXT_CHECK[item["cause"]]
    return {"alert_id": alert["id"], "status": "hypotheses" if ranked and ranked[0]["score"] >= 2
            else "insufficient_evidence", "hypotheses": ranked[:3]}


def create_issue(report, approved, issues):
    if approved is not True:
        raise PermissionError("Developer approval required")
    if report["status"] != "hypotheses":
        raise ValueError("Investigate further before opening a cause-specific issue")
    alert_id = report["alert_id"]
    if alert_id in issues:
        return {"alert_id": alert_id, "status": "already_open"}
    issue = {"alert_id": alert_id, "status": "open", "hypotheses": report["hypotheses"]}
    issues[alert_id] = issue
    return issue
