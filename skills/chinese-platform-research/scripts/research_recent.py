"""Run the pinned last30days discovery engine with free, explicit sources."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def run_summary(command, env, output):
    """Keep complete engine output on disk and return a small discovery index."""
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output,
                                     prefix="discovery-", suffix=".json", delete=False) as raw:
        raw_path = Path(raw.name)
        log_path = raw_path.with_suffix(".log")
        with log_path.open("x", encoding="utf-8") as log:
            result = subprocess.run(command, env=env, stdout=raw, stderr=log, check=False)
    summary = {"returncode": result.returncode, "raw_report": str(raw_path),
               "engine_log": str(log_path), "reading_stage": "discovery_only"}
    try:
        report = json.loads(raw_path.read_text(encoding="utf-8"))
        candidates = report["ranked_candidates"]
        summary.update({"topic": report.get("topic"), "source_status": report["source_status"],
                        "candidate_count": len(candidates), "candidates": []})
        for candidate in candidates[:8]:
            discussion_urls = list(dict.fromkeys(
                item.get("metadata", {}).get("hn_url")
                for item in candidate.get("source_items", [])
                if item.get("metadata", {}).get("hn_url")))
            summary["candidates"].append({
                "title": candidate.get("title", "")[:240], "url": candidate.get("url"),
                "sources": candidate.get("sources", [candidate.get("source")]),
                "discussion_urls": discussion_urls,
            })
        summary["warnings"] = report.get("warnings", [])
        summary["errors_by_source"] = report.get("errors_by_source", {})
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        summary["output_error"] = "Engine did not return the expected report JSON: " + str(exc)
        summary["returncode"] = result.returncode or 1
    print(json.dumps(summary, ensure_ascii=False))
    return summary["returncode"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--summary", action="store_true", help="Save full output locally; print a compact candidate index (preflight stays complete)")
    parser.add_argument("--engine", type=Path, help="Path to a separately installed last30days.py")
    args = parser.parse_args()
    if not 1 <= args.days <= 365:
        parser.error("--days must be between 1 and 365")

    engine = args.engine
    if engine is None:
        engine_home = Path(os.environ.get("LAST30DAYS_HOME", Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "tools/last30days"))
        candidates = [engine_home / "scripts/last30days.py", engine_home / "skills/last30days/scripts/last30days.py"]
        engine = next((path for path in candidates if path.is_file()), candidates[0])
    engine = engine.expanduser().resolve()
    if not engine.is_file():
        parser.error("last30days is optional and not bundled; provide --engine or LAST30DAYS_HOME pointing to your installed checkout")
    output = args.out.resolve()
    env = os.environ.copy()
    for key in (
        "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY",
        "XAI_API_KEY", "OPENROUTER_API_KEY", "SCRAPECREATORS_API_KEY",
        "LAST30DAYS_API_KEY", "LAST30DAYS_API_BASE",
        "PERPLEXITY_API_KEY", "PARALLEL_API_KEY", "BRAVE_API_KEY", "APIFY_API_TOKEN",
    ):
        env.pop(key, None)
    env.update({
        "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
        "LAST30DAYS_CONFIG_DIR": str(output / "isolated-config"),
        "LAST30DAYS_TRUST_PROJECT_CONFIG": "0", "LAST30DAYS_SKIP_KEYCHAIN": "1",
        "FROM_BROWSER": "off", "LAST30DAYS_STRICT_EXIT": "1",
    })
    # Hide optional auth/paid-provider CLIs; keep the current Python and OS tools.
    system_paths = [str(Path(env.get("SystemRoot", "C:/Windows")) / "System32")] if os.name == "nt" else ["/usr/bin", "/bin"]
    env["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), *system_paths])
    command = [sys.executable, str(engine), args.topic, "--search", "hackernews,github",
               "--quick", "--days", str(args.days), "--web-backend", "none",
               "--no-browser-cookies", "--emit", "json", "--json-profile", "raw",
               "--save-dir", str(output)]
    if args.preflight:
        command.append("--preflight")
    elif args.summary:
        return run_summary(command, env, output)
    return subprocess.run(command, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
