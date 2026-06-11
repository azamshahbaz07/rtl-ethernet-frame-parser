`timescale 1ns/1ps

module byte_counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       clear,
    input  logic       increment,
    output logic [15:0] count
);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 16'd0;
    end else if (clear) begin
      count <= 16'd0;
    end else if (increment) begin
      count <= count + 16'd1;
    end
  end

endmodule
