# Results

These results were generated with:

```bash
make regression
```

## Regression

- Seed: 123
- Directed: 18/18 pass
- Random: 500/500 pass
- Total accepted packet metadata emissions: 518
- Required functional coverage matrix bins: 21/21 hit
- Observed functional coverage matrix bins: 43
- Negative tests generated: 130

## Trace Summary

- Bytes driven: 82,978
- Minimum frame length: 6 bytes
- Maximum frame length: 558 bytes
- Observed metadata stall cycles: 1,005

## Error Flags Observed

- `error_short_frame`: 2
- `error_ipv4_bad_version`: 13
- `error_ipv4_options_unsupported`: 20
- `error_ipv4_total_length`: 84
- `error_udp_length`: 83
- `error_unexpected_eop`: 67
- `error_missing_eop`: 0

Known limitations are documented in the README and tracked as future work.
