# Coverage Plan

## Protocol Coverage

- IPv4 without VLAN
- VLAN with IPv4 inner EtherType
- ARP unsupported
- IPv6 unsupported
- Random unsupported EtherTypes
- TCP unsupported
- ICMP unsupported

## Error Coverage

- Short Ethernet frame
- Partial IPv4 header
- Partial UDP header
- IPv4 bad version
- IPv4 IHL/options unsupported
- IPv4 total length too small
- UDP length too small
- UDP length larger than IPv4 payload

## Backpressure Coverage

- `meta_ready` always high
- `meta_ready` stalls while metadata is valid
- Input valid gaps before bytes

## Frame Length Coverage

- Minimum UDP payload
- Payload sizes 1, 8, 32, 128, and 512 bytes
- Truncated frames
