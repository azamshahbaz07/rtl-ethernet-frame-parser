#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ERROR_FIELDS = [
    "error_short_frame",
    "error_ipv4_bad_version",
    "error_ipv4_options_unsupported",
    "error_ipv4_total_length",
    "error_udp_length",
    "error_unexpected_eop",
    "error_missing_eop",
]


def _parse_kv(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in line.strip().split():
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key] = value
    return fields


def parse_trace(path: Path) -> dict:
    stats = {
        "packets": 0,
        "bytes": 0,
        "metadata_emissions": 0,
        "min_frame_length": None,
        "max_frame_length": 0,
        "meta_ready_stalls": 0,
        "errors": {field: 0 for field in ERROR_FIELDS},
    }

    if not path.exists():
        return stats

    for line in path.read_text(encoding="utf-8").splitlines():
        fields = _parse_kv(line)
        if fields.get("event") == "byte":
            stats["bytes"] += 1
        elif fields.get("event") == "meta":
            stats["metadata_emissions"] += 1
            if fields.get("ready") == "0":
                stats["meta_ready_stalls"] += 1
            if fields.get("ready") == "1":
                stats["packets"] += 1
            frame_len = int(fields.get("frame_len", fields.get("frame_length", "0")))
            if frame_len:
                stats["min_frame_length"] = frame_len if stats["min_frame_length"] is None else min(stats["min_frame_length"], frame_len)
                stats["max_frame_length"] = max(stats["max_frame_length"], frame_len)
            for error in ERROR_FIELDS:
                if fields.get(error) == "1":
                    stats["errors"][error] += 1

    if stats["min_frame_length"] is None:
        stats["min_frame_length"] = 0
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse simulator trace logs")
    parser.add_argument("trace", nargs="?", default="logs/regression.trace")
    parser.add_argument("--json-out", default="results/trace_summary.json")
    args = parser.parse_args()

    stats = parse_trace(Path(args.trace))
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
