import json
import argparse
from datetime import datetime, timezone
from app import create_issue, investigate
from github_source import get_deployments

ALERT = {"id": "INC-17", "service": "checkout", "at": "2026-01-10T12:00:00Z"}
LOGS = [
    {"id": "L-1", "at": "2026-01-10T11:59:00Z", "message": "Database connection refused"},
    {"id": "L-2", "at": "2026-01-10T11:58:00Z", "message": "Checkout database unavailable"},
]
DEPLOYS = [{"id": "D-31", "service": "checkout", "at": "2026-01-10T11:45:00Z"}]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--github", metavar="OWNER/REPO", help="Read recent deployment records")
    parser.add_argument("--service", default="checkout", help="Service represented by that repository")
    parser.add_argument("--ai", action="store_true", help="Optional model-written explanation")
    args = parser.parse_args()
    if args.github:
        try:
            owner, repo = args.github.split("/")
        except ValueError:
            parser.error("--github must be OWNER/REPO")
        alert = {"id": "LIVE-READONLY", "service": args.service,
                 "at": datetime.now(timezone.utc).isoformat()}
        deployments = get_deployments(owner, repo, args.service)
        report = investigate(alert, [], deployments)
        print(json.dumps({"deployments_read": len(deployments)}, indent=2))
    else:
        report = investigate(ALERT, LOGS, DEPLOYS)
    print(json.dumps(report, indent=2))
    if args.ai:
        from ai_explain import explain
        print(explain("incident investigation", report))
    if not args.github:
        print(json.dumps({"approved_issue": create_issue(report, True, {})}, indent=2))
