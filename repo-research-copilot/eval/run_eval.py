from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx


def load_questions(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("questions file must be a JSON list")
    normalized: list[dict[str, str]] = []
    for idx, item in enumerate(data):
        if isinstance(item, str):
            normalized.append({"id": f"q{idx+1}", "question": item})
            continue
        if not isinstance(item, dict) or "question" not in item:
            raise ValueError("each question must be a string or object with 'question'")
        normalized.append(
            {
                "id": str(item.get("id", f"q{idx+1}")),
                "question": str(item["question"]),
            }
        )
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run API smoke evaluation")
    parser.add_argument("--api-url", required=True, help="Base API URL")
    parser.add_argument(
        "--questions",
        default="eval/questions.json",
        help="Path to question list JSON",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-k retrieval")
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for authenticated endpoints (falls back to API_KEY env var)",
    )
    parser.add_argument(
        "--api-key-header",
        default=None,
        help="Header name for API key (falls back to API_KEY_HEADER_NAME env var)",
    )
    parser.add_argument(
        "--report",
        default="eval/report.json",
        help="Output report path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    questions = load_questions(Path(args.questions))
    endpoint = f"{args.api_url.rstrip('/')}/ask"
    api_key = args.api_key if args.api_key is not None else os.getenv("API_KEY", "")
    api_key_header = (
        args.api_key_header
        if args.api_key_header is not None
        else os.getenv("API_KEY_HEADER_NAME", "X-API-Key")
    )

    headers: dict[str, str] = {}
    if api_key.strip():
        headers[api_key_header] = api_key.strip()

    results: list[dict[str, object]] = []
    failures = 0
    missing_citations = 0

    with httpx.Client(timeout=90.0) as client:
        for item in questions:
            payload = {"question": item["question"], "k": args.k}
            row: dict[str, object] = {"id": item["id"], "question": item["question"]}
            try:
                response = client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
                sources = body.get("sources", [])
                source_count = len(sources) if isinstance(sources, list) else 0
                row["ok"] = True
                row["status_code"] = response.status_code
                row["source_count"] = source_count
                row["answer_preview"] = str(body.get("answer", ""))[:180]
                if source_count == 0:
                    missing_citations += 1
            except Exception as exc:
                failures += 1
                row["ok"] = False
                row["error"] = str(exc)
                row["source_count"] = 0
            results.append(row)

    total = len(results)
    passed = total - failures
    citation_coverage = 0.0 if total == 0 else ((total - missing_citations) / total)

    summary = {
        "total_questions": total,
        "passed": passed,
        "failures": failures,
        "missing_citations": missing_citations,
        "citation_coverage": round(citation_coverage, 4),
    }

    print("Evaluation summary")
    print(json.dumps(summary, indent=2))

    report = {
        "summary": summary,
        "results": results,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Non-zero exit only for API failures. Missing citations are reported but non-blocking.
    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
