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

## Trace Summary

- Bytes driven: 81,911
- Minimum frame length: 6 bytes
- Maximum frame length: 558 bytes
- Observed metadata stall cycles: 133

## Error Flags Observed

- `error_short_frame`: 1
- `error_ipv4_bad_version`: 12
- `error_ipv4_options_unsupported`: 9
- `error_ipv4_total_length`: 27
- `error_udp_length`: 24
- `error_unexpected_eop`: 19
- `error_missing_eop`: 0

Known limitations are documented in the README and tracked as future work.
