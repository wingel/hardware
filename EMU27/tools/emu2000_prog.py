#! /usr/bin/python3
from emu2000_lib import *

if __name__ == '__main__':
    if not sys.argv[0]:
        print()

class Prog(object):
    pinmap = {
        'CE'  : '35',
        'OE'  : '33',
        'WE'  :  '9',

        'A0'  : '46',
        'A1'  : '47',
        'A2'  : '48',
        'A3'  : '49',
        'A4'  : '64',
        'A5'  :  '1',
        'A6'  :  '2',
        'A7'  :  '4',
        'A8'  : '13',
        'A9'  : '15',
        'A10' : '34',
        'A11' : '16',
        'A12' :  '5',
        'A13' : '12',
        'A14' : '11',
        'A15' :  '6',
        'A16' :  '8',
        'A17' : '10',
        'A18' :  '7',

        'D0'  : '45',
        'D1'  : '44',
        'D2'  : '43',
        'D3'  : '42',
        'D4'  : '40',
        'D5'  : '39',
        'D6'  : '38',
        'D7'  : '36',

        'RX'  : '18',
        'TX'  : '19',
    }

    def __init__(self, bs):
        self.bs = bs

        assert len(self.bs.bsdl.pinmaps) == 1
        package = list(self.bs.bsdl.pinmaps.keys())[0]
        pinmap = self.bs.bsdl.pinmaps[package]
        portmap = self.bs.bsdl.portmaps[package]

        self.portmap = {}
        for k, v in self.pinmap.items():
            print(k, v, pinmap[v])
            self.portmap[k] = bs.bsdl.cells[pinmap[v]]

        self.ichain = self.ochain = self.bs.sample()
        self.bs.sample(self.ochain)

        self.prog_unsafe = False

    def update(self):
        self.ichain = self.bs.extest(self.ochain)

    def set_pin(self, name, value):
        port = self.portmap[name]
        if value == None:
            self.ochain &= ~(1<<port['oe'])

        else:
            self.ochain |= (1<<port['oe'])

            if value:
                self.ochain |= (1<<port['output'])
            else:
                self.ochain &= ~(1<<port['output'])

    def get_pin(self, name):
        port = self.portmap[name]
        return (self.ichain >> port['input']) & 1

    def set_addr(self, addr):
        for i in range(19):
            self.set_pin('A%u' % i, (addr >> i) & 1)

    def set_data(self, data):
        for i in range(8):
            if data is None:
                self.set_pin('D%u' % i, None)
            else:
                self.set_pin('D%u' % i, (data >> i) & 1)

    def get_data(self):
        data = 0
        for i in range(8):
            if self.get_pin('D%u' % i):
                data |= 1 << i
        return data

    def set_ce(self, value):
        self.set_pin('CE', value)

    def set_oe(self, value):
        self.set_pin('OE', value)

    def set_we(self, value):
        self.set_pin('WE', value)

    def write(self, addr, data):
        self.set_addr(addr)
        self.set_data(data)
        self.update()

        self.set_ce(0)
        self.set_oe(1)
        self.set_we(0)
        self.update()

        self.set_ce(1)
        self.set_we(1)
        self.update()

        if 0:
            self.set_data(None)
            self.update()

    def read(self, addr):
        self.set_addr(addr)
        self.set_data(None)
        self.update()
        self.set_ce(0)
        self.set_oe(0)
        self.set_we(1)
        self.update()
        self.update()

        data = self.get_data()

        self.set_ce(1)
        self.set_oe(1)
        self.update()

        return data

    def dump(self):
        s = ''
        for name, port in self.portmap.items():
            s += "%-10s " % name
            for f in [ 'input', 'output', 'oe', 'oe_disable' ]:
                if f in port:
                    num = port[f]
                    s += "  %s %4s %4s" % (f, num, (self.ochain >> num) & 1)
            s += '\n'
        return s

    def software_id(self):
        self.write(0x5555, 0xaa)
        self.write(0x2aaa, 0x55)
        self.write(0x5555, 0x90)

        vendor = self.read(0)
        device = self.read(1)

        self.write(0x0000, 0xf0)

        return (vendor << 8) | device

    def prog_byte(self, addr, data):
        self.write(0x5555, 0xaa)
        self.write(0x2aaa, 0x55)
        self.write(0x5555, 0xa0)
        self.write(  addr, data)

        if self.prog_unsafe:
            return

        while True:
            v = self.read(addr)
            if v == data:
                break

    def chip_erase(self):
        self.write(0x5555, 0xaa)
        self.write(0x2aaa, 0x55)
        self.write(0x5555, 0x80)
        self.write(0x5555, 0xaa)
        self.write(0x2aaa, 0x55)
        self.write(0x5555, 0x10)

        while True:
            v = self.read(0x0000)
            if v & 0x80:
                break

    def sector_erase(self, addr):
        self.write(0x5555, 0xaa)
        self.write(0x2aaa, 0x55)
        self.write(0x5555, 0x80)
        self.write(0x5555, 0xaa)
        self.write(0x2aaa, 0x55)
        self.write(  addr, 0x30)

        while True:
            v = self.read(0x0000)
            if v & 0x80:
                break

def main():
    fn = '/opt/Xilinx/14.7/ISE_DS/ISE/xc9500xl/data/xc9572xl_vq64.bsd'

    ocd = OpenOCD()
    ocd.cmd('adapter speed 1000')
    bs = BS(ocd, 'xc.tap', fn)

    prog = Prog(bs)

    bs.check_idcode()
    bs.check_usercode()

    bs.ocd.verbose = 0

    prog.set_ce(1)
    prog.set_oe(1)
    prog.set_we(1)

    print("flash id: %04x" % prog.software_id())

    prog.prog_unsafe = 1

    if 1:
        print("chip erase")
        prog.chip_erase()
        # prog.sector_erase(0)

        # prog.prog_byte(0x0007, 0x42)

        n = 256

        if 0:
            data = bytearray(range(0, n))
        else:
            data = bytearray(range(n-1, -1, -1))

            if 1:
                hello = 'Hello World!\r\n'.encode('ascii')
                data = hello + data[len(hello):]

        if 1:
            t0 = time.time()
            for i in range(n):
                v = prog.read(i)
                assert v == 0xff
            t = time.time()
            print("Elapsed for empty check of %u bytes: %.3f" % (n, t-t0))

        if 1:
            t0 = time.time()
            for i in range(n):
                prog.prog_byte(i, data[i])
            t = time.time()
            print("Elapsed for write of %u bytes: %.3f" % (n, t-t0))

        if 1:
            t0 = time.time()
            for i in range(n):
                v = prog.read(i)
                assert v == data[i]
            t = time.time()
            print("Elapsed for verify of %u bytes: %.3f" % (n, t-t0))

    print()
    for i in range(10):
        print("%08x %02x" % (i, prog.read(i)))

    # print(prog.dump())

    # Back to normal mode
    bs.sample()

    bs.bypass()

    if 0:
        t0 = 0
        t = 0
        while True:
            t = time.time()
            if t - t0 >= 1:
                sys.stdout.write("\x1b[H\x1b[2J")
                t0 = t
                v = prog.get_pin('RX')
                prog.set_pin('RX', not v)

                if v:
                    prog.set_addr(0x555555)
                    prog.set_data(0x55)
                else:
                    prog.set_addr(0xaaaaaa)
                    prog.set_data(0xaa)


            sys.stdout.write("\x1b[H")

            prog.update()
            prog.update()
            for name in prog.portmap.keys():
                print("%-4s %u" % (name, prog.get_pin(name)))

            print(v)

if __name__ == '__main__':
    main()
