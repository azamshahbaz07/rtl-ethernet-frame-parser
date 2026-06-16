#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable


ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_ARP = 0x0806
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_IPV6 = 0x86DD
IPPROTO_UDP = 17

MATRIX_FIELDS = ("vlan", "ethertype", "ipv4", "udp", "frame_length")


@dataclass(frozen=True)
class MatrixBin:
    vlan: str
    ethertype: str
    ipv4: str
    udp: str
    frame_length: str

    def as_tuple(self) -> tuple[str, str, str, str, str]:
        return (self.vlan, self.ethertype, self.ipv4, self.udp, self.frame_length)


REQUIRED_BINS = [
    MatrixBin("no_vlan", "ipv4", "valid_ipv4", "valid_udp", "min_udp"),
    MatrixBin("no_vlan", "ipv4", "valid_ipv4", "valid_udp", "small"),
    MatrixBin("no_vlan", "ipv4", "valid_ipv4", "valid_udp", "medium"),
    MatrixBin("no_vlan", "ipv4", "valid_ipv4", "valid_udp", "large"),
    MatrixBin("vlan", "vlan_ipv4", "valid_ipv4", "valid_udp", "min_udp"),
    MatrixBin("vlan", "vlan_ipv4", "valid_ipv4", "valid_udp", "small"),
    MatrixBin("vlan", "vlan_ipv4", "valid_ipv4", "valid_udp", "medium"),
    MatrixBin("vlan", "vlan_ipv4", "valid_ipv4", "valid_udp", "large"),
    MatrixBin("no_vlan", "arp", "no_ipv4", "no_udp", "small"),
    MatrixBin("no_vlan", "ipv6", "no_ipv4", "no_udp", "small"),
    MatrixBin("no_vlan", "other_unsupported", "no_ipv4", "no_udp", "small"),
    MatrixBin("vlan", "vlan_unsupported_inner", "no_ipv4", "no_udp", "small"),
    MatrixBin("no_vlan", "ipv4", "bad_version", "valid_udp", "min_udp"),
    MatrixBin("no_vlan", "ipv4", "options_unsupported", "valid_udp", "min_udp"),
    MatrixBin("no_vlan", "ipv4", "total_length_error", "length_too_large", "min_udp"),
    MatrixBin("no_vlan", "ipv4", "unsupported_l4", "no_udp", "small"),
    MatrixBin("no_vlan", "ipv4", "truncated_ipv4", "no_udp", "partial_headers"),
    MatrixBin("no_vlan", "ipv4", "valid_ipv4", "truncated_udp", "partial_headers"),
    MatrixBin("no_vlan", "ipv4", "valid_ipv4", "length_too_small", "min_udp"),
    MatrixBin("no_vlan", "ipv4", "valid_ipv4", "length_too_large", "min_udp"),
    MatrixBin("short_unknown", "short_eth", "no_ipv4", "no_udp", "short_eth"),
]


def be16(frame: bytes, index: int) -> int:
    value = 0
    if index < len(frame):
        value |= frame[index] << 8
    if index + 1 < len(frame):
        value |= frame[index + 1]
    return value


def frame_length_bucket(frame_len: int, vlan: bool) -> str:
    min_udp_len = 46 if vlan else 42
    if frame_len < 14:
        return "short_eth"
    if frame_len < min_udp_len:
        return "partial_headers"
    if frame_len == min_udp_len:
        return "min_udp"
    if frame_len <= 96:
        return "small"
    if frame_len <= 256:
        return "medium"
    return "large"


def classify_case(case: dict) -> dict[str, str | bool | float | int]:
    frame = bytes.fromhex(case.get("frame_hex", ""))
    frame_len = len(frame)
    tags = set(case.get("tags", []))
    input_gap_prob = float(case.get("input_gap_prob", 0.0))
    meta_stall_cycles = int(case.get("meta_stall_cycles", 0))

    vlan = "short_unknown"
    ethertype_bin = "short_eth"
    ipv4_bin = "no_ipv4"
    udp_bin = "no_udp"
    vlan_present = False

    if frame_len >= 14:
        ethertype = be16(frame, 12)
        if ethertype == ETHERTYPE_VLAN:
            vlan_present = True
            vlan = "vlan"
            if frame_len < 18:
                ethertype_bin = "vlan_truncated"
            else:
                inner = be16(frame, 16)
                ethertype_bin = "vlan_ipv4" if inner == ETHERTYPE_IPV4 else "vlan_unsupported_inner"
        else:
            vlan = "no_vlan"
            if ethertype == ETHERTYPE_IPV4:
                ethertype_bin = "ipv4"
            elif ethertype == ETHERTYPE_ARP:
                ethertype_bin = "arp"
            elif ethertype == ETHERTYPE_IPV6:
                ethertype_bin = "ipv6"
            else:
                ethertype_bin = "other_unsupported"

    ip_base = 18 if ethertype_bin == "vlan_ipv4" else 14
    ipv4_present = ethertype_bin in {"ipv4", "vlan_ipv4"}
    udp_present = False
    if ipv4_present:
        if frame_len < ip_base + 20:
            ipv4_bin = "truncated_ipv4"
        else:
            version = frame[ip_base] >> 4
            ihl = frame[ip_base] & 0x0F
            total_length = be16(frame, ip_base + 2)
            protocol = frame[ip_base + 9]
            if version != 4:
                ipv4_bin = "bad_version"
            elif ihl != 5:
                ipv4_bin = "options_unsupported"
            elif total_length < 20 or frame_len < ip_base + total_length:
                ipv4_bin = "total_length_error"
            elif protocol != IPPROTO_UDP:
                ipv4_bin = "unsupported_l4"
            else:
                ipv4_bin = "valid_ipv4"

            udp_present = protocol == IPPROTO_UDP
            if udp_present:
                udp_base = ip_base + 20
                if frame_len < udp_base + 8:
                    udp_bin = "truncated_udp"
                else:
                    udp_length = be16(frame, udp_base + 4)
                    payload_len = total_length - 20 if total_length >= 20 else 0
                    if udp_length < 8:
                        udp_bin = "length_too_small"
                    elif udp_length > payload_len:
                        udp_bin = "length_too_large"
                    else:
                        udp_bin = "valid_udp"

    backpressure = "none"
    if input_gap_prob > 0 and meta_stall_cycles > 0:
        backpressure = "input_and_meta"
    elif input_gap_prob > 0:
        backpressure = "input_gaps"
    elif meta_stall_cycles > 0:
        backpressure = "meta_ready_stalls"

    frame_bucket = frame_length_bucket(frame_len, vlan_present)
    return {
        "name": case.get("name", ""),
        "vlan": vlan,
        "ethertype": ethertype_bin,
        "ipv4": ipv4_bin,
        "udp": udp_bin,
        "frame_length": frame_bucket,
        "matrix_key": (vlan, ethertype_bin, ipv4_bin, udp_bin, frame_bucket),
        "negative": any(tag.startswith("error_") or tag.startswith("unsupported") or tag == "truncated" for tag in tags),
        "input_gap_prob": input_gap_prob,
        "meta_stall_cycles": meta_stall_cycles,
        "backpressure": backpressure,
    }


def coverage_summary(cases: Iterable[dict]) -> dict:
    classified = [classify_case(case) for case in cases]
    matrix_counts: Counter = Counter(row["matrix_key"] for row in classified)
    examples: dict[tuple[str, str, str, str, str], list[str]] = defaultdict(list)
    for row in classified:
        key = row["matrix_key"]
        if len(examples[key]) < 3:
            examples[key].append(str(row["name"]))

    dimension_counts = {field: Counter(str(row[field]) for row in classified) for field in MATRIX_FIELDS}
    backpressure_counts = Counter(str(row["backpressure"]) for row in classified)
    negative_count = sum(1 for row in classified if row["negative"])

    required = [goal.as_tuple() for goal in REQUIRED_BINS]
    hit_required = [goal for goal in required if matrix_counts[goal] > 0]
    missed_required = [goal for goal in required if matrix_counts[goal] == 0]
    return {
        "classified": classified,
        "matrix_counts": matrix_counts,
        "examples": examples,
        "dimension_counts": dimension_counts,
        "backpressure_counts": backpressure_counts,
        "negative_count": negative_count,
        "required": required,
        "hit_required": hit_required,
        "missed_required": missed_required,
    }
