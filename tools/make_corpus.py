#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from packet_gen import directed_cases, random_cases


def write_corpus(path: Path, cases) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"cases": [case.to_json_dict() for case in cases]}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Ethernet parser packet corpora")
    parser.add_argument("--directed-out", default="corpus/directed.json")
    parser.add_argument("--random-out", default="corpus/random.json")
    parser.add_argument("--random", type=int, default=500)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    write_corpus(Path(args.directed_out), directed_cases())
    write_corpus(Path(args.random_out), random_cases(args.random, args.seed))
    print(f"Wrote {args.directed_out} ({len(directed_cases())} cases)")
    print(f"Wrote {args.random_out} ({args.random} cases, seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
