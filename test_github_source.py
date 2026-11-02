import io
import json
import os
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from github_source import get_deployments, get_workflow_runs
from evaluate import evaluate


class FakeResponse(io.BytesIO):
    pass


class GitHubSourceTests(unittest.TestCase):
    def test_maps_real_api_shape_without_posting(self):
        def opener(request, timeout):
            self.assertEqual(request.full_url,
                             "https://api.github.com/repos/pars1905/demo/deployments?per_page=100")
            self.assertEqual(timeout, 10)
            self.assertEqual(request.get_method(), "GET")
            return FakeResponse(json.dumps([{
                "id": 123, "created_at": "2026-11-01T09:00:00Z"}]).encode())
        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
            results = get_deployments("pars1905", "demo", "checkout", opener)
        self.assertEqual(results[0]["id"], "123")
        self.assertEqual(results[0]["service"], "checkout")

    def test_invalid_repo_rejected_before_network(self):
        with self.assertRaises(ValueError):
            get_deployments("pars1905", "../another", "checkout")

    def test_maps_actions_runs_as_context(self):
        def opener(request, timeout):
            self.assertEqual(request.full_url,
                             "https://api.github.com/repos/pars1905/incident-investigation-assistant/actions/runs?per_page=30")
            self.assertEqual(request.get_method(), "GET")
            return FakeResponse(json.dumps({"workflow_runs": [{
                "id": 42, "name": "Tests", "status": "completed", "conclusion": "success",
                "created_at": "2026-11-01T10:00:00Z", "html_url": "https://github.com/example/actions/runs/42"
            }]}).encode())
        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
            runs = get_workflow_runs("pars1905", "incident-investigation-assistant", opener)
        self.assertEqual(runs[0]["conclusion"], "success")
        self.assertEqual(runs[0]["id"], "42")

    def test_benchmark_has_100_balanced_cases(self):
        data = json.loads((Path(__file__).parent / "data" / "incidents_100.json").read_text())
        result = evaluate(data)
        self.assertEqual(result["examples"], 100)
        self.assertEqual({x["total"] for x in result["by_class"].values()}, {25})

    def test_dot_segments_rejected_before_network(self):
        for owner in (".", ".."):
            with self.subTest(owner=owner):
                with self.assertRaises(ValueError):
                    get_workflow_runs(owner, "demo")

    def test_network_failure_is_reported_as_runtime_error(self):
        def opener(request, timeout):
            raise urllib.error.URLError("dns failure")
        for call in (lambda: get_deployments("o", "r", "checkout", opener),
                     lambda: get_workflow_runs("o", "r", opener)):
            with self.assertRaises(RuntimeError):
                call()


if __name__ == "__main__":
    unittest.main()
