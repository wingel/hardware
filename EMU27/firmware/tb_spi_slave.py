#! /usr/bin/python3
import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

if __name__ == '__main__':
    import os
    import sys
    ec = os.system('make')
    sys.exit(ec)

class SPITest(object):
    def __init__(self, dut):
        self.dut = dut

    def dump(self):
        if 0:
            self.dut._log.info("cs %s, sck %s, sdi %s, sdo %s, sdoe %s" % (
                self.dut.cs_n.value,
                self.dut.sck.value,
                self.dut.sdi.value,
                self.dut.sdo.value,
                self.dut.sdoe.value,
            ))

    async def step(self):
        await Timer(2, units = 'ns')
        self.dump()

    async def spi_start(self):
        self.dut._log.info("stop")
        self.dut.scl.value = 0
        await self.step()
        self.dut.sda_in.value = 1
        await self.step()
        self.dut._log.info("start")
        self.dut.scl.value = 1
        await self.step()
        self.dut.sda_in.value = 0
        await self.step()

    async def spi_stop(self):
        self.dut._log.info("stop")
        self.dut.scl.value = 0
        await self.step()
        self.dut.sda_in.value = 0
        await self.step()
        self.dut.scl.value = 1
        await self.step()
        self.dut.sda_in.value = 1
        await self.step()

    async def spi_clock(self, sd = None):
        if sd is None:
            sd = 0
        self.dut.sdi.value = sd
        await self.step()
        self.dut.sck.value = 1
        v = str(self.dut.sdo.value) != '0'
        await self.step()
        self.dut.sck.value = 0
        return v

    async def spi_shift(self, n, sd = None):
        v = 0
        for i in range(n):
            if sd is None:
                b = None
            else:
                b = (sd >> (n-1)) & 1
                sd <<= 1
            v <<= 1
            v |= await self.spi_clock(b)
        return v

    async def spi_byte(self, v = None):
        return await self.spi_shift(8, v)

    async def run(self):
        await self.step()

        self.dut.cs_n.value = 1
        self.dut.sck.value = 1
        self.dut.sdi.value = 0

        await self.step()

        for i in range(3):
            await self.spi_clock()

        await self.step()

        if 1:
            self.dut.cs_n.value = 0

            # Write 3 bytes
            await self.spi_byte(0x01)
            await self.spi_byte(0x23)
            await self.spi_byte(0x45)
            await self.spi_byte(0x67)
            await self.spi_byte(0x89)
            await self.spi_byte(0xab)

            await self.step()
            self.dut.cs_n.value = 1

            await self.step()
            await self.step()
            await self.step()

        if 1:
            self.dut.cs_n.value = 0

            # Read 3 bytes
            await self.spi_byte(0x81)
            await self.spi_byte(0x23)
            await self.spi_byte(0x45)
            print("READ %02x" % await self.spi_byte(None))
            print("READ %02x" % await self.spi_byte(None))
            print("READ %02x" % await self.spi_byte(None))

            await self.step()
            self.dut.cs_n.value = 1

            await self.step()
            await self.step()
            await self.step()

        if 0:
            v = 0
            for i in range(32):
                v <<= 1
                v |= await self.spi_clock()
                print("0x%08x" % v)

        for i in range(5):
            await self.step()

@cocotb.test()
async def test_start(dut):
    t = SPITest(dut)
    await t.run()
