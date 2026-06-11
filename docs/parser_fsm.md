# Parser FSM

The parser exposes these debug states:

- `IDLE`: wait for a frame start.
- `PARSE_ETH`: capture destination MAC, source MAC, and EtherType.
- `PARSE_VLAN`: capture one 802.1Q tag and inner EtherType.
- `PARSE_IPV4`: capture a fixed 20-byte IPv4 header.
- `PARSE_UDP`: capture an 8-byte UDP header.
- `SKIP_PAYLOAD`: ignore remaining payload bytes until EOP.
- `EMIT`: hold metadata until `meta_ready`.

The implementation parses by absolute byte offset and performs final consistency checks at EOP. That keeps the state machine easy to inspect and keeps the C++ reference model aligned with RTL behavior.
