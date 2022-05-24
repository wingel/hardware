`timescale 1ns / 1ns
`default_nettype none

module spi_slave
  #(
    parameter ADDR_WIDTH = 18,
    parameter DATA_WIDTH = 8
    )
  (
   input cs_n,
   input sck,
   input sdi,
   output wire sdo,
   output reg sdoe,

   output reg [ADDR_WIDTH-1:0] addro,
   output reg addroe,

   output reg [DATA_WIDTH-1:0] datao,
   input wire [DATA_WIDTH-1:0] datai,
   output reg dataoe,

   output reg oe_n,
   output reg we_n,
   output wire ce_n
   );

  reg [DATA_WIDTH-2:0] shiftreg = 0;
  wire [DATA_WIDTH-1:0] curr = { shiftreg, sdi };

  reg [DATA_WIDTH-2:0] idx;

  reg rw = 0;

  reg [DATA_WIDTH-1:0] datahold;

  assign sdo = datahold[DATA_WIDTH-1];

  assign ce_n = oe_n && we_n;

  always @(posedge cs_n or posedge sck) begin
    if (cs_n) begin
      idx <= 0;
      rw <= 0;
      addro <= 0;
      addroe <= 0;
      datao <= 0;
      dataoe <= 0;
      shiftreg <= 0;
      sdoe <= 0;
      oe_n <= 1;

    end else begin
      addroe <= 0;
      dataoe <= 0;

      oe_n <= 1;
      sdoe <= 0;

      if (idx == 7) begin
        rw <= curr[7];
        addro[17:16] <= curr[1:0];
      end else if (idx == 15) begin
        addro[15:8] <= curr[7:0];
      end else if (idx == 23) begin
        addro[7:0] <= curr[7:0];
      end else if (idx == 31) begin
        if (rw)
          addro <= addro + 1;
      end else if (idx == 39) begin
        addro <= addro + 1;
      end

      if (rw) begin
        // Read cycle
        if (idx == 23 || idx == 31 || idx == 39) begin
          addroe <= 1;
          oe_n <= 0;
        end

        if (idx >= 24) begin
          sdoe <= 1;
        end
      end else begin
        // Write cycle
        if (idx == 31 || idx == 39) begin
          datao <= curr;
          addroe <= 1;
          dataoe <= 1;
        end
      end

      if (idx == 39) begin
        idx <= 32;
      end else begin
        idx <= idx + 1;
      end

      shiftreg <= curr[6:0];
    end
  end

  always @(posedge cs_n or negedge sck) begin
    if (cs_n) begin
      we_n <= 1;
      datahold <= 0;
    end else begin
      we_n <= 1;
      if (dataoe) begin
        we_n <= 0;
      end
      if (!oe_n) begin
        datahold <= datai;
      end else begin
        datahold <= { datahold[6:0], 1'b0 };
      end
    end
  end

endmodule

`default_nettype wire
