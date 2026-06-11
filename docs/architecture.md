# Architecture

The project has four cooperating layers.

1. Python creates directed and randomized packet corpora as JSON.
2. The Verilator C++ harness drives packet bytes into the RTL valid/ready stream.
3. The SystemVerilog parser extracts Ethernet, optional VLAN, IPv4, and UDP metadata.
4. A C++ reference parser computes expected metadata and the scoreboard compares every field.

The parser uses absolute frame byte offsets. Ethernet bytes are always at offsets `0..13`; IPv4 starts at offset `14` without VLAN and `18` with VLAN; UDP starts twenty bytes after the IPv4 base. Metadata is finalized when `in_eop` is accepted.
