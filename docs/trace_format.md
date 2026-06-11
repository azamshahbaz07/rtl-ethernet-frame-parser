# Trace Format

The simulator writes simple key/value trace lines.

Accepted byte:

```text
cycle=12 event=byte data=0xff sop=1 eop=0 state=1 byte_idx=0 in_ready=1
```

Metadata:

```text
cycle=49 event=meta ready=1 dst_mac=0xffffffffffff src_mac=0x001122334455 ethertype=0x0800 vlan=0 ipv4=1 udp=1 src_ip=0xc0a8010a dst_ip=0x08080808 udp_src=0x3039 udp_dst=0x0035 udp_len=0x0008 frame_len=42 header_bytes=42 error_udp_length=0
```

`tools/parse_trace.py` consumes these logs and writes `results/trace_summary.json`.
