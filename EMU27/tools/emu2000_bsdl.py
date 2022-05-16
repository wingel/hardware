#! /usr/bin/python3
from emu2000_lib import *

if __name__ == '__main__':
    if not sys.argv[0]:
        print()

def main():
    fn = '/opt/Xilinx/14.7/ISE_DS/ISE/xc9500xl/data/xc9572xl_vq64.bsd'

    ocd = OpenOCD()
    bs = BS(ocd, 'xc.tap', fn)

    if 0:
        pprint(bs.bsdl.cells)
        pprint(bs.bsdl.portmaps)
        pprint(bs.bsdl.pinmaps)

    assert len(bs.bsdl.pinmaps) == 1
    package = list(bs.bsdl.pinmaps.keys())[0]
    pinmap = bs.bsdl.pinmaps[package]
    portmap = bs.bsdl.portmaps[package]

    rx_cell = bs.bsdl.cells[pinmap['18']]
    tx_cell = bs.bsdl.cells[pinmap['19']]

    pprint(rx_cell)
    pprint(tx_cell)

    if 1:
        t0 = 0
        wdata = bs.sample(0)
        bs.sample(wdata)
        t = 0
        while True:
            if t - t0 >= 1:
                sys.stdout.write("\x1b[H\x1b[2J")
                t0 = t
                # the OE bit is cleared when sampling, strange
                wdata |= 1 << tx_cell['oe']
                wdata ^= 1 << tx_cell['output']

            sys.stdout.write("\x1b[H")

            rdata = bs.extest(wdata)
            for k, v in sorted(bs.bsdl.cells.items()):
                s = "%-10s %4s" % (k, ','.join(portmap[k]))
                for f in [ 'input', 'output', 'oe', 'oe_disable' ]:
                    if f in v:
                        num = v[f]
                        s += "  %s %4s %4s" % (f, num, (rdata >> num) & 1)
                print(s)
            t = time.time()

    # print(json.dumps(bs.bsdl.bsdl, indent = 4))

if __name__ == '__main__':
    main()
