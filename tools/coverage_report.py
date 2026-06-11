#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from parse_trace import parse_trace


def _load_cases(paths: list[Path]) -> list[dict]:
    cases: list[dict] = []
    for path in paths:
        if path.exists():
            cases.extend(json.loads(path.read_text(encoding="utf-8")).get("cases", []))
    return cases


def _tag_counts(cases: list[dict]) -> Counter:
    counts: Counter = Counter()
    for case in cases:
        for tag in case.get("tags", []):
            counts[tag] += 1
    return counts


def generate_report(corpus_paths: list[Path], regression_path: Path, trace_path: Path) -> str:
    cases = _load_cases(corpus_paths)
    tags = _tag_counts(cases)
    regression = {}
    if regression_path.exists():
        regression = json.loads(regression_path.read_text(encoding="utf-8"))
    trace = parse_trace(trace_path)

    lines = [
        "# Coverage Report",
        "",
        "## Regression Summary",
        "",
        f"- Directed cases: {regression.get('directed', {}).get('passed', 0)}/{regression.get('directed', {}).get('total', 0)} passed",
        f"- Random cases: {regression.get('random', {}).get('passed', 0)}/{regression.get('random', {}).get('total', 0)} passed",
        f"- Seed: {regression.get('seed', 'n/a')}",
        "",
        "## Protocol Coverage",
        "",
        f"- IPv4 cases: {tags['ipv4']}",
        f"- UDP cases: {tags['udp']}",
        f"- VLAN cases: {tags['vlan']}",
        f"- No-VLAN cases: {tags['no_vlan']}",
        f"- Unsupported EtherType cases: {tags['unsupported_ethertype']}",
        f"- Unsupported VLAN inner EtherType cases: {tags['unsupported_inner_ethertype']}",
        f"- Unsupported L4 protocol cases: {tags['unsupported_l4_protocol']}",
        "",
        "## Error Coverage",
        "",
        f"- Short Ethernet frames: {tags['error_short_frame']}",
        f"- IPv4 bad version: {tags['error_ipv4_bad_version']}",
        f"- IPv4 options unsupported: {tags['error_ipv4_options_unsupported']}",
        f"- IPv4 total length errors: {tags['error_ipv4_total_length']}",
        f"- UDP length errors: {tags['error_udp_length']}",
        f"- Unexpected EOP/truncation: {tags['error_unexpected_eop'] + tags['truncated']}",
        "",
        "## Backpressure Coverage",
        "",
        f"- Cases with meta_ready stalls: {tags['meta_ready_backpressure']}",
        f"- Cases with input valid gaps: {tags['input_valid_gaps']}",
        f"- Observed stalled metadata cycles: {trace['meta_ready_stalls']}",
        "",
        "## Trace Statistics",
        "",
        f"- Metadata emissions accepted: {trace['packets']}",
        f"- Bytes driven: {trace['bytes']}",
        f"- Min frame length: {trace['min_frame_length']}",
        f"- Max frame length: {trace['max_frame_length']}",
        "",
        "## Error Flags Observed In Trace",
        "",
    ]
    for name, count in trace["errors"].items():
        lines.append(f"- {name}: {count}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Markdown coverage report")
    parser.add_argument("--directed", default="corpus/directed.json")
    parser.add_argument("--random", default="corpus/random.json")
    parser.add_argument("--regression", default="results/regression.json")
    parser.add_argument("--trace", default="logs/regression.trace")
    parser.add_argument("--out", default="results/coverage.md")
    args = parser.parse_args()

    report = generate_report(
        [Path(args.directed), Path(args.random)],
        Path(args.regression),
        Path(args.trace),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
