`timescale 1ns/1ps

package eth_parser_pkg;

  typedef struct packed {
    logic [47:0] dst_mac;
    logic [47:0] src_mac;
    logic [15:0] ethertype;

    logic        vlan_present;
    logic [11:0] vlan_id;
    logic [2:0]  vlan_pcp;
    logic        vlan_dei;
    logic [15:0] inner_ethertype;

    logic        ipv4_present;
    logic [3:0]  ipv4_version;
    logic [3:0]  ipv4_ihl;
    logic [15:0] ipv4_total_length;
    logic [7:0]  ipv4_protocol;
    logic [7:0]  ipv4_ttl;
    logic [31:0] src_ip;
    logic [31:0] dst_ip;

    logic        udp_present;
    logic [15:0] udp_src_port;
    logic [15:0] udp_dst_port;
    logic [15:0] udp_length;

    logic [15:0] frame_length;
    logic [15:0] header_bytes;

    logic        unsupported_ethertype;
    logic        unsupported_inner_ethertype;
    logic        unsupported_l4_protocol;

    logic        error_short_frame;
    logic        error_ipv4_bad_version;
    logic        error_ipv4_options_unsupported;
    logic        error_ipv4_total_length;
    logic        error_udp_length;
    logic        error_unexpected_eop;
    logic        error_missing_eop;
  } parser_meta_t;

  localparam int META_FLAT_WIDTH = 341;

  localparam logic [15:0] ETHERTYPE_IPV4 = 16'h0800;
  localparam logic [15:0] ETHERTYPE_VLAN = 16'h8100;
  localparam logic [7:0]  IPPROTO_UDP    = 8'd17;

  function automatic logic [META_FLAT_WIDTH-1:0] pack_meta(input parser_meta_t m);
    logic [META_FLAT_WIDTH-1:0] f;
    int o;
    begin
      f = '0;
      o = 0;
      f[o +: 48] = m.dst_mac;                         o += 48;
      f[o +: 48] = m.src_mac;                         o += 48;
      f[o +: 16] = m.ethertype;                       o += 16;
      f[o +: 1]  = m.vlan_present;                    o += 1;
      f[o +: 12] = m.vlan_id;                         o += 12;
      f[o +: 3]  = m.vlan_pcp;                        o += 3;
      f[o +: 1]  = m.vlan_dei;                        o += 1;
      f[o +: 16] = m.inner_ethertype;                 o += 16;
      f[o +: 1]  = m.ipv4_present;                    o += 1;
      f[o +: 4]  = m.ipv4_version;                    o += 4;
      f[o +: 4]  = m.ipv4_ihl;                        o += 4;
      f[o +: 16] = m.ipv4_total_length;               o += 16;
      f[o +: 8]  = m.ipv4_protocol;                   o += 8;
      f[o +: 8]  = m.ipv4_ttl;                        o += 8;
      f[o +: 32] = m.src_ip;                          o += 32;
      f[o +: 32] = m.dst_ip;                          o += 32;
      f[o +: 1]  = m.udp_present;                     o += 1;
      f[o +: 16] = m.udp_src_port;                    o += 16;
      f[o +: 16] = m.udp_dst_port;                    o += 16;
      f[o +: 16] = m.udp_length;                      o += 16;
      f[o +: 16] = m.frame_length;                    o += 16;
      f[o +: 16] = m.header_bytes;                    o += 16;
      f[o +: 1]  = m.unsupported_ethertype;           o += 1;
      f[o +: 1]  = m.unsupported_inner_ethertype;     o += 1;
      f[o +: 1]  = m.unsupported_l4_protocol;         o += 1;
      f[o +: 1]  = m.error_short_frame;               o += 1;
      f[o +: 1]  = m.error_ipv4_bad_version;          o += 1;
      f[o +: 1]  = m.error_ipv4_options_unsupported;  o += 1;
      f[o +: 1]  = m.error_ipv4_total_length;         o += 1;
      f[o +: 1]  = m.error_udp_length;                o += 1;
      f[o +: 1]  = m.error_unexpected_eop;            o += 1;
      f[o +: 1]  = m.error_missing_eop;               o += 1;
      return f;
    end
  endfunction

endpackage
