#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
import random
from typing import Iterable


ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_ARP = 0x0806
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_IPV6 = 0x86DD

IPPROTO_ICMP = 1
IPPROTO_TCP = 6
IPPROTO_UDP = 17


@dataclass
class PacketCase:
    name: str
    frame: bytes
    tags: list[str] = field(default_factory=list)
    input_gap_prob: float = 0.0
    meta_stall_cycles: int = 0

    def to_json_dict(self) -> dict:
        return {
            "name": self.name,
            "frame_hex": self.frame.hex(),
            "tags": self.tags,
            "input_gap_prob": self.input_gap_prob,
            "meta_stall_cycles": self.meta_stall_cycles,
        }


def _normalize_tags(case: PacketCase) -> PacketCase:
    case.tags = sorted(set(case.tags))
    return case


def _with_backpressure(case: PacketCase, rng: random.Random) -> PacketCase:
    if rng.random() < 0.45:
        case.input_gap_prob = rng.choice([0.05, 0.10, 0.20, 0.35])
        case.tags.append("input_valid_gaps")
        case.tags.append("random_input_gaps")
    if rng.random() < 0.45:
        case.meta_stall_cycles = rng.randrange(1, 9)
        case.tags.append("meta_ready_backpressure")
        case.tags.append("random_meta_ready_stalls")
    if case.input_gap_prob > 0 and case.meta_stall_cycles > 0:
        case.tags.append("random_backpressure_both")
    return _normalize_tags(case)


def _mac_to_bytes(value: int | bytes | Iterable[int]) -> bytes:
    if isinstance(value, bytes):
        if len(value) != 6:
            raise ValueError("MAC bytes must be exactly 6 bytes")
        return value
    if isinstance(value, int):
        return value.to_bytes(6, "big")
    data = bytes(value)
    if len(data) != 6:
        raise ValueError("MAC iterable must produce exactly 6 bytes")
    return data


def _ip_to_bytes(value: int | str | bytes) -> bytes:
    if isinstance(value, bytes):
        if len(value) != 4:
            raise ValueError("IP bytes must be exactly 4 bytes")
        return value
    if isinstance(value, int):
        return value.to_bytes(4, "big")
    return ipaddress.IPv4Address(value).packed


def ethernet_header(dst_mac: int | bytes | Iterable[int], src_mac: int | bytes | Iterable[int], ethertype: int) -> bytes:
    return _mac_to_bytes(dst_mac) + _mac_to_bytes(src_mac) + ethertype.to_bytes(2, "big")


def vlan_tag(tci: int, inner_ethertype: int) -> bytes:
    return tci.to_bytes(2, "big") + inner_ethertype.to_bytes(2, "big")


def ipv4_header(
    src_ip: int | str | bytes,
    dst_ip: int | str | bytes,
    protocol: int,
    total_length: int,
    ihl: int = 5,
    version: int = 4,
    ttl: int = 64,
    identification: int = 0x1234,
    flags_fragment: int = 0,
    checksum: int = 0,
    dscp_ecn: int = 0,
) -> bytes:
    return b"".join(
        [
            bytes([(version << 4) | (ihl & 0x0F), dscp_ecn & 0xFF]),
            total_length.to_bytes(2, "big"),
            identification.to_bytes(2, "big"),
            flags_fragment.to_bytes(2, "big"),
            bytes([ttl & 0xFF, protocol & 0xFF]),
            checksum.to_bytes(2, "big"),
            _ip_to_bytes(src_ip),
            _ip_to_bytes(dst_ip),
        ]
    )


def udp_header(src_port: int, dst_port: int, length: int, checksum: int = 0) -> bytes:
    return b"".join(
        [
            src_port.to_bytes(2, "big"),
            dst_port.to_bytes(2, "big"),
            length.to_bytes(2, "big"),
            checksum.to_bytes(2, "big"),
        ]
    )


def make_ipv4_udp_frame(
    name: str,
    payload: bytes = b"",
    dst_mac: int = 0xFFFFFFFFFFFF,
    src_mac: int = 0x001122334455,
    src_ip: int | str | bytes = "192.168.1.10",
    dst_ip: int | str | bytes = "8.8.8.8",
    src_port: int = 12345,
    dst_port: int = 53,
    vlan_tci: int | None = None,
    ipv4_version: int = 4,
    ipv4_ihl: int = 5,
    ipv4_protocol: int = IPPROTO_UDP,
    ipv4_total_length: int | None = None,
    udp_length: int | None = None,
    truncate_to: int | None = None,
    input_gap_prob: float = 0.0,
    meta_stall_cycles: int = 0,
    tags: list[str] | None = None,
) -> PacketCase:
    udp_len = len(payload) + 8 if udp_length is None else udp_length
    default_total_len = len(payload) + (28 if ipv4_protocol == IPPROTO_UDP else 20)
    total_len = default_total_len if ipv4_total_length is None else ipv4_total_length
    ethertype = ETHERTYPE_VLAN if vlan_tci is not None else ETHERTYPE_IPV4
    frame = ethernet_header(dst_mac, src_mac, ethertype)
    case_tags = ["ipv4"]

    if vlan_tci is not None:
        frame += vlan_tag(vlan_tci, ETHERTYPE_IPV4)
        case_tags.append("vlan")
    else:
        case_tags.append("no_vlan")

    frame += ipv4_header(
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=ipv4_protocol,
        total_length=total_len,
        ihl=ipv4_ihl,
        version=ipv4_version,
    )

    if ipv4_protocol == IPPROTO_UDP:
        frame += udp_header(src_port, dst_port, udp_len)
        case_tags.append("udp")

    frame += payload
    if truncate_to is not None:
        frame = frame[:truncate_to]
        case_tags.append("truncated")

    if tags:
        case_tags.extend(tags)

    return PacketCase(
        name=name,
        frame=frame,
        tags=sorted(set(case_tags)),
        input_gap_prob=input_gap_prob,
        meta_stall_cycles=meta_stall_cycles,
    )


def make_unsupported_ethertype(name: str, ethertype: int, payload_len: int = 46) -> PacketCase:
    frame = ethernet_header(0xFFFFFFFFFFFF, 0x001122334455, ethertype) + bytes((i & 0xFF) for i in range(payload_len))
    tags = ["unsupported_ethertype"]
    if ethertype == ETHERTYPE_ARP:
        tags.append("unsupported_arp")
    elif ethertype == ETHERTYPE_IPV6:
        tags.append("unsupported_ipv6")
    else:
        tags.append("unsupported_other_ethertype")
    return PacketCase(name=name, frame=frame, tags=tags)


def make_vlan_unsupported_inner(name: str, inner_ethertype: int, payload_len: int = 42) -> PacketCase:
    frame = (
        ethernet_header(0xFFFFFFFFFFFF, 0x001122334455, ETHERTYPE_VLAN)
        + vlan_tag(0x5123, inner_ethertype)
        + bytes((0xA0 + i) & 0xFF for i in range(payload_len))
    )
    return PacketCase(name=name, frame=frame, tags=["vlan", "unsupported_inner_ethertype"])


def directed_cases() -> list[PacketCase]:
    payload32 = bytes(range(32))
    return [
        make_ipv4_udp_frame("valid_ipv4_udp_min_payload", payload=b"", tags=["valid", "directed", "payload_0"]),
        make_ipv4_udp_frame("valid_ipv4_udp_payload_32", payload=payload32, tags=["valid", "directed", "payload_32"]),
        make_ipv4_udp_frame("valid_vlan_ipv4_udp", payload=b"hello", vlan_tci=0xA123, tags=["valid", "directed"]),
        make_unsupported_ethertype("unsupported_arp", ETHERTYPE_ARP),
        make_unsupported_ethertype("unsupported_ipv6", ETHERTYPE_IPV6),
        make_vlan_unsupported_inner("unsupported_vlan_inner_arp", ETHERTYPE_ARP),
        make_ipv4_udp_frame("ipv4_bad_version", ipv4_version=6, tags=["error_ipv4_bad_version", "directed"]),
        make_ipv4_udp_frame("ipv4_ihl_options_unsupported", ipv4_ihl=6, tags=["error_ipv4_options_unsupported", "directed"]),
        make_ipv4_udp_frame("ipv4_total_length_too_small", ipv4_total_length=19, tags=["error_ipv4_total_length", "directed"]),
        make_ipv4_udp_frame("ipv4_protocol_tcp_unsupported", ipv4_protocol=IPPROTO_TCP, payload=b"tcp-ish", tags=["unsupported_l4_protocol", "directed"]),
        make_ipv4_udp_frame("ipv4_protocol_icmp_unsupported", ipv4_protocol=IPPROTO_ICMP, payload=b"icmp-ish", tags=["unsupported_l4_protocol", "directed"]),
        make_ipv4_udp_frame("udp_length_too_small", udp_length=7, tags=["error_udp_length", "directed"]),
        make_ipv4_udp_frame("udp_length_too_large", udp_length=64, tags=["error_udp_length", "directed"]),
        PacketCase("short_frame_less_than_eth_header", b"\xff\xff\xff\xff\xff\xff", tags=["error_short_frame", "directed", "truncated"]),
        make_ipv4_udp_frame("short_frame_ipv4_partial", truncate_to=19, tags=["error_unexpected_eop", "directed"]),
        make_ipv4_udp_frame("short_frame_udp_partial", truncate_to=38, tags=["error_unexpected_eop", "directed"]),
        make_ipv4_udp_frame(
            "meta_ready_backpressure",
            payload=b"bp",
            meta_stall_cycles=5,
            tags=["valid", "meta_ready_backpressure", "directed"],
        ),
        make_ipv4_udp_frame(
            "input_valid_gaps",
            payload=b"gaps",
            input_gap_prob=0.45,
            tags=["valid", "input_valid_gaps", "directed"],
        ),
    ]


def coverage_closure_cases() -> list[PacketCase]:
    cases = [
        make_ipv4_udp_frame("cov_no_vlan_min_udp", payload=b"", tags=["coverage_goal", "valid"]),
        make_ipv4_udp_frame("cov_no_vlan_small_udp", payload=bytes(range(8)), tags=["coverage_goal", "valid"]),
        make_ipv4_udp_frame("cov_no_vlan_medium_udp", payload=bytes(range(128)), tags=["coverage_goal", "valid"]),
        make_ipv4_udp_frame("cov_no_vlan_large_udp", payload=bytes((i & 0xFF) for i in range(512)), tags=["coverage_goal", "valid"]),
        make_ipv4_udp_frame("cov_vlan_min_udp", payload=b"", vlan_tci=0x0123, tags=["coverage_goal", "valid"]),
        make_ipv4_udp_frame("cov_vlan_small_udp", payload=bytes(range(8)), vlan_tci=0x1123, tags=["coverage_goal", "valid"]),
        make_ipv4_udp_frame("cov_vlan_medium_udp", payload=bytes(range(128)), vlan_tci=0x2123, tags=["coverage_goal", "valid"]),
        make_ipv4_udp_frame("cov_vlan_large_udp", payload=bytes((i & 0xFF) for i in range(512)), vlan_tci=0x3123, tags=["coverage_goal", "valid"]),
        make_unsupported_ethertype("cov_unsupported_arp", ETHERTYPE_ARP, payload_len=46),
        make_unsupported_ethertype("cov_unsupported_ipv6", ETHERTYPE_IPV6, payload_len=46),
        make_unsupported_ethertype("cov_unsupported_other_ethertype", 0x88B5, payload_len=46),
        make_vlan_unsupported_inner("cov_vlan_unsupported_inner", ETHERTYPE_ARP, payload_len=42),
        make_ipv4_udp_frame("cov_bad_version", ipv4_version=6, tags=["coverage_goal", "error_ipv4_bad_version"]),
        make_ipv4_udp_frame("cov_bad_ihl", ipv4_ihl=6, tags=["coverage_goal", "error_ipv4_options_unsupported"]),
        make_ipv4_udp_frame("cov_total_length_too_small", ipv4_total_length=19, tags=["coverage_goal", "error_ipv4_total_length"]),
        make_ipv4_udp_frame(
            "cov_unsupported_tcp",
            ipv4_protocol=IPPROTO_TCP,
            ipv4_total_length=36,
            payload=bytes(range(16)),
            tags=["coverage_goal", "unsupported_l4_protocol"],
        ),
        make_ipv4_udp_frame("cov_truncated_ipv4", truncate_to=19, tags=["coverage_goal", "error_unexpected_eop"]),
        make_ipv4_udp_frame("cov_truncated_udp", ipv4_total_length=24, truncate_to=38, tags=["coverage_goal", "error_unexpected_eop"]),
        make_ipv4_udp_frame("cov_udp_length_too_small", udp_length=7, tags=["coverage_goal", "error_udp_length"]),
        make_ipv4_udp_frame("cov_udp_length_too_large", udp_length=64, tags=["coverage_goal", "error_udp_length"]),
        PacketCase("cov_short_eth", b"\xff\xff\xff\xff\xff\xff", tags=["coverage_goal", "error_short_frame", "truncated"]),
    ]

    cases[1].input_gap_prob = 0.20
    cases[1].tags.extend(["input_valid_gaps", "coverage_input_gaps"])
    cases[5].meta_stall_cycles = 4
    cases[5].tags.extend(["meta_ready_backpressure", "coverage_meta_ready_stalls"])
    cases[13].input_gap_prob = 0.10
    cases[13].meta_stall_cycles = 3
    cases[13].tags.extend(["input_valid_gaps", "meta_ready_backpressure", "coverage_backpressure_both"])
    return [_normalize_tags(case) for case in cases]


def _random_payload(rng: random.Random, max_len: int = 512) -> bytes:
    length = rng.choice([0, 1, 8, 32, 128, 512, rng.randrange(0, max_len + 1)])
    return bytes(rng.randrange(0, 256) for _ in range(length))


def random_case(index: int, rng: random.Random) -> PacketCase:
    roll = rng.random()
    payload = _random_payload(rng)
    dst_mac = rng.randrange(0, 1 << 48)
    src_mac = rng.randrange(0, 1 << 48)
    src_ip = rng.randrange(1, 0xFFFFFFFF)
    dst_ip = rng.randrange(1, 0xFFFFFFFF)
    src_port = rng.randrange(1, 65536)
    dst_port = rng.randrange(1, 65536)

    if roll < 0.70:
        return _with_backpressure(make_ipv4_udp_frame(
            f"random_{index:04d}_valid_ipv4_udp",
            payload=payload,
            dst_mac=dst_mac,
            src_mac=src_mac,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            tags=["valid", "random"],
        ), rng)
    if roll < 0.80:
        tci = (rng.randrange(0, 8) << 13) | (rng.randrange(0, 2) << 12) | rng.randrange(0, 4096)
        return _with_backpressure(make_ipv4_udp_frame(
            f"random_{index:04d}_valid_vlan_ipv4_udp",
            payload=payload,
            dst_mac=dst_mac,
            src_mac=src_mac,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            vlan_tci=tci,
            tags=["valid", "random"],
        ), rng)
    if roll < 0.90:
        ethertype = rng.choice([ETHERTYPE_ARP, ETHERTYPE_IPV6, rng.randrange(0x0000, 0xFFFF)])
        if ethertype in (ETHERTYPE_IPV4, ETHERTYPE_VLAN):
            ethertype = 0x88B5
        case = make_unsupported_ethertype(f"random_{index:04d}_unsupported_ethertype", ethertype, payload_len=len(payload))
        case.tags.append("random")
        return _with_backpressure(case, rng)

    malformed = rng.choice(["bad_version", "bad_ihl", "small_total", "udp_small", "udp_large", "truncate_ip", "truncate_udp"])
    if malformed == "bad_version":
        return _with_backpressure(make_ipv4_udp_frame(f"random_{index:04d}_bad_version", payload=payload, ipv4_version=rng.choice([0, 5, 6]), tags=["random", "error_ipv4_bad_version"]), rng)
    if malformed == "bad_ihl":
        return _with_backpressure(make_ipv4_udp_frame(f"random_{index:04d}_bad_ihl", payload=payload, ipv4_ihl=rng.choice([0, 4, 6, 15]), tags=["random", "error_ipv4_options_unsupported"]), rng)
    if malformed == "small_total":
        return _with_backpressure(make_ipv4_udp_frame(f"random_{index:04d}_small_total", payload=payload, ipv4_total_length=rng.randrange(0, 20), tags=["random", "error_ipv4_total_length"]), rng)
    if malformed == "udp_small":
        return _with_backpressure(make_ipv4_udp_frame(f"random_{index:04d}_udp_small", payload=payload, udp_length=rng.randrange(0, 8), tags=["random", "error_udp_length"]), rng)
    if malformed == "udp_large":
        return _with_backpressure(make_ipv4_udp_frame(f"random_{index:04d}_udp_large", payload=payload, udp_length=len(payload) + 32, tags=["random", "error_udp_length"]), rng)
    if malformed == "truncate_ip":
        return _with_backpressure(make_ipv4_udp_frame(f"random_{index:04d}_truncate_ip", payload=payload, truncate_to=rng.randrange(14, 34), tags=["random", "error_unexpected_eop"]), rng)
    return _with_backpressure(make_ipv4_udp_frame(f"random_{index:04d}_truncate_udp", payload=payload, truncate_to=rng.randrange(34, 42), tags=["random", "error_unexpected_eop"]), rng)


def random_cases(count: int, seed: int) -> list[PacketCase]:
    rng = random.Random(seed)
    closure = coverage_closure_cases()
    cases = closure[:count]
    cases.extend(random_case(i, rng) for i in range(len(cases), count))
    return cases
