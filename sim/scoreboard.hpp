#pragma once

#include "reference_parser.hpp"

#include <cstdint>
#include <string>
#include <vector>

struct CompareResult {
    bool pass = true;
    std::vector<std::string> messages;
};

template <typename WideT>
uint64_t read_packed_bits(const WideT& words, int offset, int width) {
    uint64_t value = 0;
    for (int i = 0; i < width; ++i) {
        const int bit = offset + i;
        const uint32_t word = words[bit / 32];
        if ((word & (uint32_t{1} << (bit % 32))) != 0) {
            value |= uint64_t{1} << i;
        }
    }
    return value;
}

template <typename WideT>
ParsedMeta unpack_dut_meta(const WideT& words) {
    ParsedMeta meta;
    int o = 0;
    meta.dst_mac = read_packed_bits(words, o, 48); o += 48;
    meta.src_mac = read_packed_bits(words, o, 48); o += 48;
    meta.ethertype = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.vlan_present = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.vlan_id = static_cast<uint16_t>(read_packed_bits(words, o, 12)); o += 12;
    meta.vlan_pcp = static_cast<uint8_t>(read_packed_bits(words, o, 3)); o += 3;
    meta.vlan_dei = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.inner_ethertype = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.ipv4_present = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.ipv4_version = static_cast<uint8_t>(read_packed_bits(words, o, 4)); o += 4;
    meta.ipv4_ihl = static_cast<uint8_t>(read_packed_bits(words, o, 4)); o += 4;
    meta.ipv4_total_length = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.ipv4_protocol = static_cast<uint8_t>(read_packed_bits(words, o, 8)); o += 8;
    meta.ipv4_ttl = static_cast<uint8_t>(read_packed_bits(words, o, 8)); o += 8;
    meta.src_ip = static_cast<uint32_t>(read_packed_bits(words, o, 32)); o += 32;
    meta.dst_ip = static_cast<uint32_t>(read_packed_bits(words, o, 32)); o += 32;
    meta.udp_present = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.udp_src_port = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.udp_dst_port = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.udp_length = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.frame_length = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.header_bytes = static_cast<uint16_t>(read_packed_bits(words, o, 16)); o += 16;
    meta.unsupported_ethertype = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.unsupported_inner_ethertype = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.unsupported_l4_protocol = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.error_short_frame = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.error_ipv4_bad_version = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.error_ipv4_options_unsupported = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.error_ipv4_total_length = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.error_udp_length = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.error_unexpected_eop = read_packed_bits(words, o, 1) != 0; o += 1;
    meta.error_missing_eop = read_packed_bits(words, o, 1) != 0; o += 1;
    return meta;
}

CompareResult compare_meta(const ParsedMeta& expected, const ParsedMeta& got);
