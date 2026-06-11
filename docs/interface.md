# Interface

## Input Byte Stream

`in_data` carries one byte. A byte is accepted when `in_valid && in_ready`. `in_sop` marks the first byte of a frame and `in_eop` marks the last byte.

## Metadata Output

`meta_valid` asserts after EOP when metadata is ready. If `meta_ready` is low, the RTL holds metadata stable and deasserts `in_ready` until the metadata is accepted.

The primary metadata type is `eth_parser_pkg::parser_meta_t`. It contains MAC addresses, EtherType fields, VLAN fields, IPv4 fields, UDP fields, frame/header lengths, unsupported-protocol flags, and error flags.

`meta_flat` is a verification-oriented packed view of the same fields with a stable LSB-first layout defined by `pack_meta()` in `rtl/eth_parser_pkg.sv`.
