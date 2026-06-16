#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "obj_dir" / "eth_parser_sim"


def run(cmd: list[str], log_path: Path | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write("$ " + " ".join(cmd) + "\n")
            log.write(proc.stdout)
            log.write(proc.stderr)
            if proc.stdout and not proc.stdout.endswith("\n"):
                log.write("\n")
    return proc


def parse_summary(output: str) -> tuple[int, int]:
    for line in output.splitlines()[::-1]:
        if line.startswith("Regression:"):
            passed, total = line.split()[1].split("/")
            return int(passed), int(total)
    return 0, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and run Ethernet parser regressions")
    parser.add_argument("--directed", type=int, default=1, help="run directed corpus when nonzero")
    parser.add_argument("--random", type=int, default=500, help="number of random tests")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    logs = ROOT / "logs"
    results = ROOT / "results"
    logs.mkdir(exist_ok=True)
    results.mkdir(exist_ok=True)
    regression_log = logs / "regression.log"
    trace_log = logs / "regression.trace"
    regression_log.write_text("", encoding="utf-8")
    trace_log.write_text("", encoding="utf-8")

    corpus_cmd = [
        sys.executable,
        "tools/make_corpus.py",
        "--random",
        str(args.random),
        "--seed",
        str(args.seed),
    ]
    proc = run(corpus_cmd, regression_log)
    print(proc.stdout, end="")
    if proc.returncode != 0:
        print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode

    if not args.no_build:
        proc = run(["make", "build"], regression_log)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            print(proc.stderr, end="", file=sys.stderr)
            return proc.returncode

    summary = {"seed": args.seed, "directed": {"passed": 0, "total": 0}, "random": {"passed": 0, "total": 0}}
    if args.directed:
        proc = run([str(SIM), "--corpus", "corpus/directed.json", "--trace", str(trace_log), "--seed", str(args.seed)], regression_log)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            print(proc.stderr, end="", file=sys.stderr)
            return proc.returncode
        passed, total = parse_summary(proc.stdout)
        summary["directed"] = {"passed": passed, "total": total}

    if args.random > 0:
        proc = run([str(SIM), "--corpus", "corpus/random.json", "--trace", str(trace_log), "--seed", str(args.seed + 1)], regression_log)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            print(proc.stderr, end="", file=sys.stderr)
            return proc.returncode
        passed, total = parse_summary(proc.stdout)
        summary["random"] = {"passed": passed, "total": total}

    (results / "regression.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    proc = run([sys.executable, "tools/parse_trace.py", str(trace_log), "--json-out", "results/trace_summary.json"], regression_log)
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode

    proc = run([sys.executable, "tools/coverage_report.py"], regression_log)
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode

    print(
        f"Regression complete: directed {summary['directed']['passed']}/{summary['directed']['total']} "
        f"random {summary['random']['passed']}/{summary['random']['total']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
