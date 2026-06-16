# Coverage Plan

The main functional coverage matrix is:

```text
VLAN x EtherType x IPv4-validity x UDP-validity x frame-length bucket
```

The report classifies every generated packet into that cross, records observed bins, and checks a curated set of meaningful required bins. Impossible combinations are not treated as coverage goals.

`make report` writes `results/coverage.md`, including required-bin HIT/MISS status, examples for each hit bin, per-dimension counts, backpressure stimulus bins, and trace-derived error counts.

## Matrix Dimensions

### VLAN

- `no_vlan`
- `vlan`
- `short_unknown`

### EtherType

- `ipv4`
- `vlan_ipv4`
- `arp`
- `ipv6`
- `other_unsupported`
- `vlan_unsupported_inner`
- `vlan_truncated`
- `short_eth`

### IPv4 Validity

- `no_ipv4`
- `valid_ipv4`
- `bad_version`
- `options_unsupported`
- `total_length_error`
- `unsupported_l4`
- `truncated_ipv4`

### UDP Validity

- `no_udp`
- `valid_udp`
- `length_too_small`
- `length_too_large`
- `truncated_udp`

### Frame-Length Bucket

- `short_eth`
- `partial_headers`
- `min_udp`
- `small`
- `medium`
- `large`

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
- Combined input valid gaps and `meta_ready` stalls

## Randomization Strategy

- Directed tests cover named protocol and malformed-frame scenarios.
- Random tests begin with coverage-closure seed cases for required bins.
- Remaining random tests are weighted toward meaningful traffic:
  - valid IPv4/UDP without VLAN
  - valid VLAN IPv4/UDP
  - unsupported EtherTypes
  - malformed IPv4/UDP and truncation cases
- Random backpressure is applied across valid and negative packets through `input_gap_prob` and `meta_stall_cycles`.

## Frame Length Coverage

- Minimum UDP payload
- Payload sizes 1, 8, 32, 128, and 512 bytes
- Truncated frames
