#include "reference_parser.hpp"

#include <iomanip>
#include <sstream>

namespace {
constexpr uint16_t ETHERTYPE_IPV4 = 0x0800;
constexpr uint16_t ETHERTYPE_VLAN = 0x8100;
constexpr uint8_t IPPROTO_UDP = 17;

bool has(const std::vector<uint8_t>& frame, size_t index) {
    return index < frame.size();
}

uint16_t be16(const std::vector<uint8_t>& frame, size_t index) {
    uint16_t value = 0;
    if (has(frame, index)) {
        value |= static_cast<uint16_t>(frame[index]) << 8;
    }
    if (has(frame, index + 1)) {
        value |= frame[index + 1];
    }
    return value;
}

uint32_t be32(const std::vector<uint8_t>& frame, size_t index) {
    uint32_t value = 0;
    for (size_t i = 0; i < 4; ++i) {
        if (has(frame, index + i)) {
            value |= static_cast<uint32_t>(frame[index + i]) << (8 * (3 - i));
        }
    }
    return value;
}

uint64_t be48(const std::vector<uint8_t>& frame, size_t index) {
    uint64_t value = 0;
    for (size_t i = 0; i < 6; ++i) {
        if (has(frame, index + i)) {
            value |= static_cast<uint64_t>(frame[index + i]) << (8 * (5 - i));
        }
    }
    return value;
}

void finalize(ParsedMeta& meta) {
    const uint16_t ip_base = meta.vlan_present ? 18 : 14;
    const uint16_t udp_base = static_cast<uint16_t>(ip_base + 20);
    const uint16_t ipv4_payload_len =
        meta.ipv4_total_length >= 20 ? static_cast<uint16_t>(meta.ipv4_total_length - 20) : 0;

    if (meta.frame_length < 14) {
        meta.error_short_frame = true;
        meta.error_unexpected_eop = true;
    }

    meta.header_bytes = meta.vlan_present ? 18 : 14;
    if (meta.vlan_present && meta.frame_length < 18) {
        meta.error_unexpected_eop = true;
    }

    if (meta.ipv4_present) {
        meta.header_bytes = static_cast<uint16_t>(ip_base + 20);
        if (meta.frame_length < ip_base + 20) {
            meta.error_unexpected_eop = true;
        }
        if (meta.ipv4_version != 4) {
            meta.error_ipv4_bad_version = true;
        }
        if (meta.ipv4_ihl != 5) {
            meta.error_ipv4_options_unsupported = true;
        }
        if (meta.ipv4_total_length < 20 ||
            meta.frame_length < ip_base + meta.ipv4_total_length) {
            meta.error_ipv4_total_length = true;
        }
    }

    if (meta.udp_present) {
        meta.header_bytes = static_cast<uint16_t>(udp_base + 8);
        if (meta.frame_length < udp_base + 8) {
            meta.error_unexpected_eop = true;
        }
        if (meta.udp_length < 8 || meta.udp_length > ipv4_payload_len) {
            meta.error_udp_length = true;
        }
    }
}
}  // namespace

ParsedMeta parse_reference(const std::vector<uint8_t>& frame) {
    ParsedMeta meta;
    meta.frame_length = static_cast<uint16_t>(frame.size());

    meta.dst_mac = be48(frame, 0);
    meta.src_mac = be48(frame, 6);
    meta.ethertype = be16(frame, 12);

    if (frame.size() >= 14) {
        if (meta.ethertype == ETHERTYPE_VLAN) {
            meta.vlan_present = true;
            if (has(frame, 14)) {
                meta.vlan_pcp = static_cast<uint8_t>(frame[14] >> 5);
                meta.vlan_dei = (frame[14] & 0x10) != 0;
                meta.vlan_id = static_cast<uint16_t>((frame[14] & 0x0f) << 8);
            }
            if (has(frame, 15)) {
                meta.vlan_id |= frame[15];
            }
            meta.inner_ethertype = be16(frame, 16);
            if (frame.size() >= 18) {
                if (meta.inner_ethertype == ETHERTYPE_IPV4) {
                    meta.ipv4_present = true;
                } else {
                    meta.unsupported_inner_ethertype = true;
                }
            }
        } else if (meta.ethertype == ETHERTYPE_IPV4) {
            meta.ipv4_present = true;
        } else {
            meta.unsupported_ethertype = true;
        }
    }

    if (meta.ipv4_present) {
        const size_t ip_base = meta.vlan_present ? 18 : 14;
        if (has(frame, ip_base)) {
            meta.ipv4_version = static_cast<uint8_t>(frame[ip_base] >> 4);
            meta.ipv4_ihl = static_cast<uint8_t>(frame[ip_base] & 0x0f);
        }
        meta.ipv4_total_length = be16(frame, ip_base + 2);
        if (has(frame, ip_base + 8)) {
            meta.ipv4_ttl = frame[ip_base + 8];
        }
        if (has(frame, ip_base + 9)) {
            meta.ipv4_protocol = frame[ip_base + 9];
        }
        meta.src_ip = be32(frame, ip_base + 12);
        meta.dst_ip = be32(frame, ip_base + 16);

        if (frame.size() >= ip_base + 20) {
            if (meta.ipv4_protocol == IPPROTO_UDP) {
                const size_t udp_base = ip_base + 20;
                meta.udp_present = true;
                meta.udp_src_port = be16(frame, udp_base);
                meta.udp_dst_port = be16(frame, udp_base + 2);
                meta.udp_length = be16(frame, udp_base + 4);
            } else {
                meta.unsupported_l4_protocol = true;
            }
        }
    }

    finalize(meta);
    return meta;
}

std::string bytes_to_hex(const std::vector<uint8_t>& bytes) {
    std::ostringstream oss;
    oss << std::hex << std::setfill('0');
    for (uint8_t byte : bytes) {
        oss << std::setw(2) << static_cast<unsigned>(byte);
    }
    return oss.str();
}

std::string meta_to_string(const ParsedMeta& meta) {
    std::ostringstream oss;
    oss << std::hex << std::setfill('0')
        << "dst_mac=0x" << std::setw(12) << meta.dst_mac
        << " src_mac=0x" << std::setw(12) << meta.src_mac
        << " ethertype=0x" << std::setw(4) << meta.ethertype
        << " vlan=" << std::dec << meta.vlan_present
        << " ipv4=" << meta.ipv4_present
        << " udp=" << meta.udp_present
        << std::hex << std::setfill('0')
        << " src_ip=0x" << std::setw(8) << meta.src_ip
        << " dst_ip=0x" << std::setw(8) << meta.dst_ip
        << " udp_src=0x" << std::setw(4) << meta.udp_src_port
        << " udp_dst=0x" << std::setw(4) << meta.udp_dst_port
        << " udp_len=0x" << std::setw(4) << meta.udp_length
        << std::dec
        << " frame_len=" << meta.frame_length
        << " header_bytes=" << meta.header_bytes;
    return oss.str();
}
