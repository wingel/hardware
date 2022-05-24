`timescale 1ns / 1ns
`default_nettype none

module wrap_spi_slave
  #(
    parameter ADDR_WIDTH = 18,
    parameter DATA_WIDTH = 8
    )
  (
   );

  // SPI bus
  wire sck;
  wire cs_n;
  wire sdi;
  wire sdo;
  wire sdoe;

  // EEPROM bus
  wire [ADDR_WIDTH-1:0] addr;
  wire [DATA_WIDTH-1:0] data;

  wire [ADDR_WIDTH-1:0] addro;
  wire addroe;

  wire [DATA_WIDTH-1:0] datao;
  wire dataoe;

  wire oe_n;
  wire we_n;

  // Nice buses that can be viewed in gtkwave

  wire sd = sdoe ? sdo : sdi;

  assign addr = addroe ? addro : 18'hxxxxx;
  assign data = dataoe ? datao : oe_n ? 8'hxx : addr[7:0];

  // DUT
  spi_slave
    #(
      .ADDR_WIDTH(ADDR_WIDTH),
      .DATA_WIDTH(DATA_WIDTH)
      )
  u
    (
     .sck(sck),
     .cs_n(cs_n),
     .sdi(sd),
     .sdo(sdo),
     .sdoe(sdoe),

     .addro(addro),
     .addroe(addroe),
     .datao(datao),
     .dataoe(dataoe),
     .datai(data),

     .we_n(we_n),
     .oe_n(oe_n)
     );

`ifdef COCOTB_SIM
initial begin
  $dumpfile ("dump.vcd");
  $dumpvars(0);
  #1;
end

always @(negedge we_n) begin
  $displayh("EPROM WRITE ", addr, ": ", data);
end

always @(negedge oe_n) begin
  $displayh("EPROM READ ", addr);
end

`endif

endmodule

`default_nettype wire
