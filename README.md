# Incident Investigation Assistant

An interview-ready Python prototype for investigating service incidents. It correlates logs with recent GitHub deployment metadata, ranks evidence-linked hypotheses, and requires explicit approval before creating a mock issue. It has no third-party Python dependencies.

**Scenario:** A developer receives an alert, logs, and recent deployment metadata. The assistant ranks possible causes, attaches a source reference for each observation, suggests the next check, and creates a mock GitHub issue only after developer approval.

From this repository's root, run:

```bash
python3 demo.py
python3 evaluate.py
python3 -m unittest discover -v
```

Local fixtures are synthetic. No credentials or packages are needed. Findings are **hypotheses**, not proven root causes; the score prioritizes investigation rather than asserting causality. A weak signal returns an `insufficient_evidence` result. The demo's mock issue is stored only in memory.

To try a model-written reviewer explanation, set `OPENAI_API_KEY` and `OPENAI_MODEL` in your shell and run `python3 demo.py --ai`. The model receives structured findings and cannot authorize or create an issue. This optional API integration is covered by a mocked test but has not been verified with a live model. API usage may incur charges.

## 100-case evaluation

`data/incidents_100.json` contains 25 hand-specified scenario variants for each of three causes and 25 cases without sufficient evidence. The labels come from the scenario design, not independently adjudicated production incidents; many examples reuse phrase templates. This set is useful for exposing known gaps but cannot establish real-world accuracy. Run `python3 evaluate.py`. Current results: 15/25 detected in each of the three cause groups, 25/25 correct abstentions, and 100/100 source references pointing to supplied records. The ten missed cases per cause use wording outside the narrow rule vocabulary. Do not report these figures as production performance.

## Read real GitHub deployment data

Choose a GitHub repository that actually creates GitHub **deployment records**, then run:

```bash
python3 demo.py --github OWNER/REPO --service checkout
```

For a private repository set `GITHUB_TOKEN` in your environment with read access to deployments. Do not commit it. The command reads up to 100 deployment records, uses the current time as the alert time, and makes **no write request**. It does not fetch logs, so a deployment alone correctly yields `insufficient_evidence`. The `--service` value is an operator-supplied mapping of the repository to the application service. A GitHub deployment record alone cannot prove that mapping or establish a root cause. The integration is covered by mocked API tests; no live repository call has been verified yet. An empty result is normal when the chosen repository does not use GitHub Deployments.

The mock issue store is process-local. A real deployment would query an observability platform with bounded time windows, sanitize sensitive log content, link exact source records, verify permissions, and use GitHub's authenticated API for issue creation. Validate top-3 cause recall and evidence relevance on historical incidents before claiming usefulness.

**CV wording:** “Built an incident triage prototype correlating logs and recent deployments, ranking evidence-linked hypotheses, and creating human-approved issue records; evaluated on labeled synthetic incidents.”
