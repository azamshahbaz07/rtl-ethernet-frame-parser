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

Directed tests cover specific protocol and malformed-frame cases. Random tests are generated from a fixed seed and include valid packets, VLAN packets, unsupported EtherTypes, and malformed packets. Backpressure is tested with `meta_ready` stalls and input valid gaps.

For signal-level debug, `make waves CASE=<directed_case>` runs one directed packet with Verilator VCD dumping enabled and writes `waves/<directed_case>.vcd`.
