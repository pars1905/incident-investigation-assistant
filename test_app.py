import unittest
from app import create_issue, investigate
from demo import ALERT, DEPLOYS, LOGS


class IncidentTests(unittest.TestCase):
    def test_log_cause_has_source_and_deploy_is_only_hypothesis(self):
        report = investigate(ALERT, LOGS, DEPLOYS)
        self.assertEqual(report["hypotheses"][0]["cause"], "database_connection")
        self.assertEqual(report["hypotheses"][0]["evidence"][0]["ref"], "log:L-1")
        self.assertEqual(report["hypotheses"][1]["cause"], "recent_deployment")

    def test_stale_logs_and_other_service_are_ignored(self):
        stale = [{"id": "old", "at": "2026-01-10T09:00:00Z", "message": "connection refused"}]
        other = [{"id": "different", "service": "billing", "at": "2026-01-10T11:58:00Z"}]
        self.assertEqual(investigate(ALERT, stale, other)["status"], "insufficient_evidence")

    def test_many_deployments_alone_do_not_establish_cause(self):
        deployments = [{"id": f"D-{i}", "service": "checkout", "at": "2026-01-10T11:58:00Z"}
                       for i in range(5)]
        self.assertEqual(investigate(ALERT, [], deployments)["status"], "insufficient_evidence")

    def test_approval_and_duplicate_issue(self):
        report = investigate(ALERT, LOGS, DEPLOYS)
        issues = {}
        with self.assertRaises(PermissionError):
            create_issue(report, False, issues)
        self.assertFalse(issues)
        create_issue(report, True, issues)
        self.assertEqual(create_issue(report, True, issues)["status"], "already_open")

    def test_only_boolean_true_counts_as_approval(self):
        report = investigate(ALERT, LOGS, DEPLOYS)
        issues = {}
        for value in ("false", "no", 1):
            with self.subTest(value=value):
                with self.assertRaises(PermissionError):
                    create_issue(report, value, issues)
        self.assertFalse(issues)


if __name__ == "__main__":
    unittest.main()
