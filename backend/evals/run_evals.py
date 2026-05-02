from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.analyzer import AnalyzerService
from app.services.document_loader import DocumentLoader


def _load_gold(gold_path: Path) -> list[dict]:
    return json.loads(gold_path.read_text(encoding="utf-8"))


def _citation_recall(citations: list[dict], expected: list[dict]) -> float:
    if not expected:
        return 0.0
    lowered_found = [item.get("citation", "").lower() for item in citations]
    matched = 0
    for target in expected:
        expected_text = target.get("expected_citation", "").lower()
        if expected_text and any(expected_text in found for found in lowered_found):
            matched += 1
    return matched / len(expected)


def _run_adversarial_cases(root: Path) -> dict[str, int]:
    analyzer = AnalyzerService()
    base_docs = DocumentLoader(root / "documents").load_documents()
    cases = _load_gold(root / "evals" / "adversarial_cases.json")
    passed = 0
    for case in cases:
        docs = dict(base_docs)
        docs.update(case.get("documents_override", {}))
        report = analyzer.analyze(docs).model_dump()
        verified_issues = len([f for f in report["findings"] if f["status"] == "verified_issue"])
        quote_checks = len(report["quote_verifications"])
        max_issues = case["assertions"].get("max_verified_issues", 99)
        max_quotes = case["assertions"].get("max_quote_checks", 99)
        if verified_issues <= max_issues and quote_checks <= max_quotes:
            passed += 1
    return {"adversarial_passed": passed, "adversarial_total": len(cases)}


def _match_expected(finding: dict, expected: dict) -> bool:
    return (
        finding.get("type") == expected["expected_type"]
        and expected["expected_claim_contains"].lower() in finding.get("motion_claim", "").lower()
        and finding.get("status") == expected["expected_status"]
    )


def _run_dependency_audit(repo_root: Path) -> dict[str, str | int]:
    checks = [
        (
            "pip_audit",
            [sys.executable, "-m", "pip_audit", "--progress-spinner", "off"],
            repo_root,
        ),
        (
            "npm_audit",
            ["npm", "audit", "--json", "--audit-level=high"],
            repo_root / "frontend",
        ),
    ]
    result: dict[str, str | int] = {}
    for name, command, cwd in checks:
        if not cwd.exists():
            result[f"{name}_status"] = "skipped"
            result[f"{name}_issues"] = -1
            continue
        try:
            run = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except FileNotFoundError:
            result[f"{name}_status"] = "tool_not_installed"
            result[f"{name}_issues"] = -1
            continue
        except subprocess.TimeoutExpired:
            result[f"{name}_status"] = "timeout"
            result[f"{name}_issues"] = -1
            continue

        if name == "npm_audit":
            issues = 0
            try:
                payload = json.loads(run.stdout or "{}")
                vulnerabilities = payload.get("metadata", {}).get("vulnerabilities", {})
                issues = int(vulnerabilities.get("high", 0)) + int(vulnerabilities.get("critical", 0))
            except json.JSONDecodeError:
                issues = -1
            result[f"{name}_issues"] = issues
        else:
            if "No module named pip_audit" in (run.stderr or ""):
                result[f"{name}_status"] = "tool_not_installed"
                result[f"{name}_issues"] = -1
                continue
            issues = 0
            for line in (run.stdout or "").splitlines():
                if line.strip() and not line.startswith("No known vulnerabilities"):
                    issues += 1
            result[f"{name}_issues"] = issues
        result[f"{name}_status"] = "ok" if run.returncode == 0 else "issues_found"
    return result


def run() -> dict[str, object]:
    root = ROOT
    docs = DocumentLoader(root / "documents").load_documents()
    report = AnalyzerService().analyze(docs).model_dump()
    findings = report["findings"]
    citations = report["citations"]
    authority_checks = report["citation_verifications"]
    quote_checks = report["quote_verifications"]
    gold = _load_gold(root / "evals" / "gold_cases.json")
    gold_citations = _load_gold(root / "evals" / "gold_citations.json")

    matched = 0
    for expected in gold:
        if any(_match_expected(finding, expected) for finding in findings):
            matched += 1

    false_positive = 0
    for finding in findings:
        if not any(_match_expected(finding, expected) for expected in gold):
            false_positive += 1

    precision = matched / len(findings) if findings else 0.0
    recall = matched / len(gold) if gold else 0.0
    hallucination_rate = false_positive / len(findings) if findings else 0.0
    citation_extraction_recall = _citation_recall(citations, gold_citations)
    could_not_verify_rate = (
        len([c for c in authority_checks if c["support_level"] == "could_not_verify"]) / len(authority_checks)
        if authority_checks
        else 0.0
    )
    adversarial = _run_adversarial_cases(root)
    dependency_audit = _run_dependency_audit(root)

    result = {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "hallucination_rate": round(hallucination_rate, 3),
        "citation_extraction_recall": round(citation_extraction_recall, 3),
        "authority_could_not_verify_rate": round(could_not_verify_rate, 3),
        "quote_checks": len(quote_checks),
        "matched_known_flaws": matched,
        "total_findings": len(findings),
        "gold_flaws": len(gold),
    }
    result.update(adversarial)
    result.update(dependency_audit)
    return result


if __name__ == "__main__":
    metrics = run()
    print(json.dumps(metrics, indent=2))
