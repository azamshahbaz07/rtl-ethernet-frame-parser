`timescale 1ns/1ps

import eth_parser_pkg::ETHERTYPE_IPV4;
import eth_parser_pkg::ETHERTYPE_VLAN;
import eth_parser_pkg::IPPROTO_UDP;
import eth_parser_pkg::META_FLAT_WIDTH;
import eth_parser_pkg::pack_meta;
import eth_parser_pkg::parser_meta_t;

module eth_frame_parser (
    input  logic clk,
    input  logic rst_n,

    input  logic [7:0] in_data,
    input  logic       in_valid,
    output logic       in_ready,
    input  logic       in_sop,
    input  logic       in_eop,

    output logic       meta_valid,
    input  logic       meta_ready,
    output eth_parser_pkg::parser_meta_t meta,

    output logic [META_FLAT_WIDTH-1:0] meta_flat,
    output logic [2:0]  state_dbg,
    output logic [15:0] byte_idx_dbg
);

  typedef enum logic [2:0] {
    IDLE         = 3'd0,
    PARSE_ETH    = 3'd1,
    PARSE_VLAN   = 3'd2,
    PARSE_IPV4   = 3'd3,
    PARSE_UDP    = 3'd4,
    SKIP_PAYLOAD = 3'd5,
    EMIT         = 3'd6
  } state_t;

  state_t state_r, state_n;
  parser_meta_t meta_r, meta_n;
  logic [15:0] byte_idx_r, byte_idx_n;
  logic meta_valid_r, meta_valid_n;

  logic accept;

  assign in_ready = !meta_valid_r;
  assign accept = in_valid && in_ready;
  assign meta_valid = meta_valid_r;
  assign meta = meta_r;
  assign meta_flat = pack_meta(meta_r);
  assign state_dbg = state_r;
  assign byte_idx_dbg = byte_idx_r;

  function automatic parser_meta_t finalize_meta(
      input parser_meta_t cur,
      input logic [15:0] frame_len
  );
    parser_meta_t m;
    logic [15:0] ip_base;
    logic [15:0] udp_base;
    logic [15:0] ipv4_payload_len;
    begin
      m = cur;
      m.frame_length = frame_len;

      ip_base = m.vlan_present ? 16'd18 : 16'd14;
      udp_base = ip_base + 16'd20;
      ipv4_payload_len = 16'd0;
      if (m.ipv4_total_length >= 16'd20) begin
        ipv4_payload_len = m.ipv4_total_length - 16'd20;
      end

      if (frame_len < 16'd14) begin
        m.error_short_frame = 1'b1;
        m.error_unexpected_eop = 1'b1;
      end

      if (m.vlan_present) begin
        m.header_bytes = 16'd18;
        if (frame_len < 16'd18) begin
          m.error_unexpected_eop = 1'b1;
        end
      end else begin
        m.header_bytes = 16'd14;
      end

      if (m.ipv4_present) begin
        m.header_bytes = ip_base + 16'd20;
        if (frame_len < (ip_base + 16'd20)) begin
          m.error_unexpected_eop = 1'b1;
        end
        if (m.ipv4_version != 4'd4) begin
          m.error_ipv4_bad_version = 1'b1;
        end
        if (m.ipv4_ihl != 4'd5) begin
          m.error_ipv4_options_unsupported = 1'b1;
        end
        if ((m.ipv4_total_length < 16'd20) ||
            (frame_len < (ip_base + m.ipv4_total_length))) begin
          m.error_ipv4_total_length = 1'b1;
        end
      end

      if (m.udp_present) begin
        m.header_bytes = udp_base + 16'd8;
        if (frame_len < (udp_base + 16'd8)) begin
          m.error_unexpected_eop = 1'b1;
        end
        if ((m.udp_length < 16'd8) || (m.udp_length > ipv4_payload_len)) begin
          m.error_udp_length = 1'b1;
        end
      end

      return m;
    end
  endfunction

  always_comb begin
    state_n = state_r;
    meta_n = meta_r;
    byte_idx_n = byte_idx_r;
    meta_valid_n = meta_valid_r;

    if (meta_valid_r) begin
      state_n = EMIT;
      if (meta_ready) begin
        meta_valid_n = 1'b0;
        state_n = IDLE;
        byte_idx_n = 16'd0;
      end
    end else if (accept) begin
      if ((state_r == IDLE) && !in_sop) begin
        state_n = IDLE;
        byte_idx_n = 16'd0;
      end else begin
        if (in_sop) begin
          meta_n = '0;
          byte_idx_n = 16'd1;
          state_n = PARSE_ETH;
          if (state_r != IDLE) begin
            meta_n.error_missing_eop = 1'b1;
          end
        end else begin
          byte_idx_n = byte_idx_r + 16'd1;
        end

        unique case (in_sop ? 16'd0 : byte_idx_r)
          16'd0:  meta_n.dst_mac[47:40] = in_data;
          16'd1:  meta_n.dst_mac[39:32] = in_data;
          16'd2:  meta_n.dst_mac[31:24] = in_data;
          16'd3:  meta_n.dst_mac[23:16] = in_data;
          16'd4:  meta_n.dst_mac[15:8]  = in_data;
          16'd5:  meta_n.dst_mac[7:0]   = in_data;
          16'd6:  meta_n.src_mac[47:40] = in_data;
          16'd7:  meta_n.src_mac[39:32] = in_data;
          16'd8:  meta_n.src_mac[31:24] = in_data;
          16'd9:  meta_n.src_mac[23:16] = in_data;
          16'd10: meta_n.src_mac[15:8]  = in_data;
          16'd11: meta_n.src_mac[7:0]   = in_data;
          16'd12: meta_n.ethertype[15:8] = in_data;
          16'd13: begin
            meta_n.ethertype[7:0] = in_data;
            if ({meta_r.ethertype[15:8], in_data} == ETHERTYPE_IPV4) begin
              meta_n.ipv4_present = 1'b1;
              state_n = PARSE_IPV4;
            end else if ({meta_r.ethertype[15:8], in_data} == ETHERTYPE_VLAN) begin
              meta_n.vlan_present = 1'b1;
              state_n = PARSE_VLAN;
            end else begin
              meta_n.unsupported_ethertype = 1'b1;
              state_n = SKIP_PAYLOAD;
            end
          end
          16'd14: begin
            if (meta_r.vlan_present) begin
              meta_n.vlan_pcp = in_data[7:5];
              meta_n.vlan_dei = in_data[4];
              meta_n.vlan_id[11:8] = in_data[3:0];
            end else if (meta_r.ipv4_present) begin
              meta_n.ipv4_version = in_data[7:4];
              meta_n.ipv4_ihl = in_data[3:0];
            end
          end
          16'd15: begin
            if (meta_r.vlan_present) begin
              meta_n.vlan_id[7:0] = in_data;
            end else if (meta_r.ipv4_present) begin
              // DSCP/ECN is intentionally not part of the base metadata.
            end
          end
          16'd16: begin
            if (meta_r.vlan_present) begin
              meta_n.inner_ethertype[15:8] = in_data;
            end else if (meta_r.ipv4_present) begin
              meta_n.ipv4_total_length[15:8] = in_data;
            end
          end
          16'd17: begin
            if (meta_r.vlan_present) begin
              meta_n.inner_ethertype[7:0] = in_data;
              if ({meta_r.inner_ethertype[15:8], in_data} == ETHERTYPE_IPV4) begin
                meta_n.ipv4_present = 1'b1;
                state_n = PARSE_IPV4;
              end else begin
                meta_n.unsupported_inner_ethertype = 1'b1;
                state_n = SKIP_PAYLOAD;
              end
            end else if (meta_r.ipv4_present) begin
              meta_n.ipv4_total_length[7:0] = in_data;
            end
          end
          16'd18: begin
            if (meta_r.vlan_present && meta_r.ipv4_present) begin
              meta_n.ipv4_version = in_data[7:4];
              meta_n.ipv4_ihl = in_data[3:0];
            end
          end
          16'd20: begin
            if (meta_r.vlan_present && meta_r.ipv4_present) begin
              meta_n.ipv4_total_length[15:8] = in_data;
            end
          end
          16'd21: begin
            if (meta_r.vlan_present && meta_r.ipv4_present) begin
              meta_n.ipv4_total_length[7:0] = in_data;
            end
          end
          default: begin
          end
        endcase

        if (meta_n.ipv4_present) begin
          if ((!meta_n.vlan_present && ((in_sop ? 16'd0 : byte_idx_r) >= 16'd14)) ||
              ( meta_n.vlan_present && ((in_sop ? 16'd0 : byte_idx_r) >= 16'd18))) begin
            unique case ((in_sop ? 16'd0 : byte_idx_r) - (meta_n.vlan_present ? 16'd18 : 16'd14))
              16'd0: begin
                meta_n.ipv4_version = in_data[7:4];
                meta_n.ipv4_ihl = in_data[3:0];
              end
              16'd2: meta_n.ipv4_total_length[15:8] = in_data;
              16'd3: meta_n.ipv4_total_length[7:0] = in_data;
              16'd8: meta_n.ipv4_ttl = in_data;
              16'd9: meta_n.ipv4_protocol = in_data;
              16'd12: meta_n.src_ip[31:24] = in_data;
              16'd13: meta_n.src_ip[23:16] = in_data;
              16'd14: meta_n.src_ip[15:8] = in_data;
              16'd15: meta_n.src_ip[7:0] = in_data;
              16'd16: meta_n.dst_ip[31:24] = in_data;
              16'd17: meta_n.dst_ip[23:16] = in_data;
              16'd18: meta_n.dst_ip[15:8] = in_data;
              16'd19: begin
                meta_n.dst_ip[7:0] = in_data;
                if (meta_n.ipv4_protocol == IPPROTO_UDP) begin
                  meta_n.udp_present = 1'b1;
                  state_n = PARSE_UDP;
                end else begin
                  meta_n.unsupported_l4_protocol = 1'b1;
                  state_n = SKIP_PAYLOAD;
                end
              end
              default: begin
              end
            endcase
          end
        end

        if (meta_n.udp_present) begin
          if ((!meta_n.vlan_present && ((in_sop ? 16'd0 : byte_idx_r) >= 16'd34)) ||
              ( meta_n.vlan_present && ((in_sop ? 16'd0 : byte_idx_r) >= 16'd38))) begin
            unique case ((in_sop ? 16'd0 : byte_idx_r) - (meta_n.vlan_present ? 16'd38 : 16'd34))
              16'd0: meta_n.udp_src_port[15:8] = in_data;
              16'd1: meta_n.udp_src_port[7:0] = in_data;
              16'd2: meta_n.udp_dst_port[15:8] = in_data;
              16'd3: meta_n.udp_dst_port[7:0] = in_data;
              16'd4: meta_n.udp_length[15:8] = in_data;
              16'd5: meta_n.udp_length[7:0] = in_data;
              16'd7: state_n = SKIP_PAYLOAD;
              default: begin
              end
            endcase
          end
        end

        if (in_eop) begin
          meta_n = finalize_meta(meta_n, (in_sop ? 16'd1 : (byte_idx_r + 16'd1)));
          meta_valid_n = 1'b1;
          state_n = EMIT;
        end
      end
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state_r <= IDLE;
      meta_r <= '0;
      byte_idx_r <= 16'd0;
      meta_valid_r <= 1'b0;
    end else begin
      state_r <= state_n;
      meta_r <= meta_n;
      byte_idx_r <= byte_idx_n;
      meta_valid_r <= meta_valid_n;
    end
  end

endmodule
