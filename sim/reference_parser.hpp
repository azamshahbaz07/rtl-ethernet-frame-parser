#pragma once

#include <cstdint>
#include <string>
#include <vector>

struct ParsedMeta {
    uint64_t dst_mac = 0;
    uint64_t src_mac = 0;
    uint16_t ethertype = 0;

    bool vlan_present = false;
    uint16_t vlan_id = 0;
    uint8_t vlan_pcp = 0;
    bool vlan_dei = false;
    uint16_t inner_ethertype = 0;

    bool ipv4_present = false;
    uint8_t ipv4_version = 0;
    uint8_t ipv4_ihl = 0;
    uint16_t ipv4_total_length = 0;
    uint8_t ipv4_protocol = 0;
    uint8_t ipv4_ttl = 0;
    uint32_t src_ip = 0;
    uint32_t dst_ip = 0;

    bool udp_present = false;
    uint16_t udp_src_port = 0;
    uint16_t udp_dst_port = 0;
    uint16_t udp_length = 0;

    uint16_t frame_length = 0;
    uint16_t header_bytes = 0;

    bool unsupported_ethertype = false;
    bool unsupported_inner_ethertype = false;
    bool unsupported_l4_protocol = false;

    bool error_short_frame = false;
    bool error_ipv4_bad_version = false;
    bool error_ipv4_options_unsupported = false;
    bool error_ipv4_total_length = false;
    bool error_udp_length = false;
    bool error_unexpected_eop = false;
    bool error_missing_eop = false;
};

ParsedMeta parse_reference(const std::vector<uint8_t>& frame);
std::string meta_to_string(const ParsedMeta& meta);
std::string bytes_to_hex(const std::vector<uint8_t>& bytes);
