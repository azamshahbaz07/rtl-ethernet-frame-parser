# Verification Strategy

The C++ testbench resets the DUT, streams each packet byte by byte, asserts `in_sop` and `in_eop`, and waits for metadata. The same packet bytes are parsed by the C++ reference model.

The scoreboard compares every metadata field:

- Ethernet addresses and EtherType
- VLAN presence, TCI-derived fields, and inner EtherType
- IPv4 presence, version, IHL, total length, protocol, TTL, and IP addresses
- UDP presence, ports, and length
- Frame/header lengths
- Unsupported-protocol flags
- Error flags

Directed tests cover named protocol and malformed-frame scenarios. Random tests are generated from a fixed seed; the random corpus begins with coverage-closure cases for the required functional matrix bins, then fills the remaining slots with weighted constrained-random traffic.

The functional coverage matrix is:

```text
VLAN x EtherType x IPv4-validity x UDP-validity x frame-length bucket
```

Randomized stimulus includes valid IPv4/UDP frames, VLAN IPv4/UDP frames, ARP/IPv6/other unsupported EtherTypes, unsupported VLAN inner EtherTypes, unsupported L4 protocols, IPv4 validity failures, UDP length failures, truncation, short frames, input valid gaps, `meta_ready` stalls, and combined input/output backpressure. `make report` writes `results/coverage.md` with required-bin HIT/MISS status and examples.

For signal-level debug, `make waves CASE=<directed_case>` runs one directed packet with Verilator VCD dumping enabled and writes `waves/<directed_case>.vcd`.
