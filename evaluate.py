"""Evaluate on 100 versioned synthetic examples; not a production benchmark."""
import json
from pathlib import Path
from app import investigate


def evaluate(cases):
    by_class = {}
    evidence_ok = 0
    for case in cases:
        report = investigate(case["alert"], case["logs"], case["deployments"])
        expected = case["expected_cause"]
        label = expected or "insufficient_evidence"
        bucket = by_class.setdefault(label, {"total": 0, "correct": 0})
        bucket["total"] += 1
        if expected is None:
            correct = report["status"] == "insufficient_evidence"
        else:
            correct = report["status"] == "hypotheses" and expected in [
                item["cause"] for item in report["hypotheses"]]
        bucket["correct"] += bool(correct)
        refs = [entry["ref"] for item in report["hypotheses"] for entry in item["evidence"]]
        valid_refs = {f"log:{log['id']}" for log in case["logs"]} | {
            f"deploy:{deploy['id']}" for deploy in case["deployments"]}
        evidence_ok += all(ref in valid_refs for ref in refs)
    return {"examples": len(cases), "by_class": {
        label: {**count, "rate": round(count["correct"] / count["total"], 3)}
        for label, count in sorted(by_class.items())},
        "evidence_reference_validity": round(evidence_ok / len(cases), 3) if cases else None}


if __name__ == "__main__":
    cases = json.loads((Path(__file__).parent / "data" / "incidents_100.json").read_text())
    print(json.dumps(evaluate(cases), indent=2))
