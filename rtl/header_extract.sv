`timescale 1ns/1ps

module header_extract #(
    parameter int WIDTH = 16
) (
    input  logic [WIDTH-1:0] current_value,
    input  logic [7:0]       byte_value,
    input  logic [$clog2(WIDTH/8)-1:0] byte_lane,
    output logic [WIDTH-1:0] next_value
);

  always_comb begin
    next_value = current_value;
    next_value[WIDTH - 1 - (byte_lane * 8) -: 8] = byte_value;
  end

endmodule
