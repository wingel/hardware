#! /usr/bin/python3
import sys
import os
import socket
import time
import json
from pprint import pprint

import bsdl

if __name__ == '__main__':
    if not sys.argv[0]:
        print()

class lazy_value(object):
    """Convert a function into a lazy value.

    The method is called the first time to retreive the result.  The
    method is then replaced with the result so that subsequent
    accesses do not have to go via the function.

        class Foo(object):
            @cached_property
            def foo(self):
                return 42
    """

    # implementation detail: this property is implemented as non-data
    # descriptor.  non-data descriptors are only invoked if there is
    # no entry with the same name in the instance's __dict__.
    # this allows us to completely get rid of the access function call
    # overhead.  If one choses to invoke __get__ by hand the property
    # will still work as expected because the lookup logic is replicated
    # in __get__ for manual invocation.

    def __init__(self, func):
        self.name = func.__name__
        self.func = func

    def __get__(self, obj, type):
        value = self.func(obj)
        obj.__dict__[self.name] = value
        return value

class OpenOCD(object):
    EOM = b'\x1a'

    def __init__(self, host = '127.0.0.1', port = 6666, verbose = 1):
        self.host = host
        self.port = port
        self.bufsize = 3276
        self.timeout = 30
        self.verbose = verbose

        if self.verbose:
            print("connecting to %s:%s" % (port, host))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def cmd(self, s, timeout = None):
        self.send(s, timeout = timeout)
        return self.recv(timeout = timeout)

    def send(self, s, timeout = None):
        if self.verbose:
            print("> %s" % s)
        if not isinstance(s, bytes):
            s = s.encode('ascii')
        if timeout is None:
            timeout = self.timeout
        self.sock.settimeout(timeout)
        self.sock.send(s + self.EOM)

    def recv(self, timeout = None):
        if timeout is None:
            timeout = self.timeout
        self.sock.settimeout(timeout)
        buf = bytearray()
        while True:
            buf += self.sock.recv(self.bufsize)
            i = buf.find(self.EOM)
            if i != -1:
                break

        if i != len(buf) - 1:
            print("warning, garbage at end of command: %s" % repr(buf[i:]))

        s = buf[:i].decode('ascii')

        if self.verbose:
            print("< %s" % s)

        return s

class BsdlSemantics:
    def map_string(self, ast):
        parser = bsdl.bsdlParser()
        ast = parser.parse(''.join(ast), "port_map")
        return ast

    def grouped_port_identification(self, ast):
        parser = bsdl.bsdlParser()
        ast = parser.parse(''.join(ast), "group_table")
        return ast

class ParsedBsdl(object):
    def __init__(self, fn):
        with open(fn) as f:
            text = f.read()

        parser = bsdl.bsdlParser()
        ast = parser.parse(text, 'bsdl_description',
                           semantics = BsdlSemantics(),
                           parseinfo = False)

        self.ast = ast
        self.json = ast.asjson()

    @lazy_value
    def name(self):
        return self.json['component_name']

    def get_register_description(self, name):
        for d in self.json['optional_register_description']:
            pprint(d)
            for k, v in d.items():
                if k == name:
                    return v
        return None

    @lazy_value
    def idcode_idmask(self):
        s = ''.join(self.get_register_description('idcode_register'))
        idlen = len(s)
        assert idlen == 32
        idcode = 0
        idmask = 0
        for i in range(idlen):
            idcode <<= 1
            idmask <<= 1
            if s[i].upper() != 'X':
                idmask |= 1
                idcode |= int(s[i], 2)
        return idcode, idmask

    @lazy_value
    def idcode(self):
        return self.idcode_idmask[0]

    @lazy_value
    def idmask(self):
        return self.idcode_idmask[1]

    @lazy_value
    def oplen(self):
        return int(self.json['instruction_register_description']['instruction_length'], 10)

    @lazy_value
    def opcodes(self):
        opcodes = {}
        for op in self.json['instruction_register_description']['instruction_opcodes']:
            name = op['instruction_name']
            value = op['opcode_list']
            assert len(value) == 1
            assert len(value[0]) == self.oplen
            opcodes[name] = int(value[0], 2)
        return opcodes

    @lazy_value
    def chainlen(self):
        return int(self.json['boundary_scan_register_description']['fixed_boundary_stmts']['boundary_length'], 10)

    @lazy_value
    def cells(self):
        cells = {}
        for d in self.json['boundary_scan_register_description']['fixed_boundary_stmts']['boundary_register']:
            name = d['cell_info']['cell_spec']['port_id']
            if name == '*':
                continue

            cell = cells.get(name, {})

            cell['name'] = name
            function = d['cell_info']['cell_spec']['function'].lower()

            if function == 'input':
                assert 'input' not in cell
                assert 'io' not in cell

                cell['input'] = int(d['cell_number'], 10)
                cell['input_safe_bit'] = d['cell_info']['cell_spec']['safe_bit']

            elif function == 'output3':
                assert 'output' not in cell
                assert 'io' not in cell

                cell['output'] = int(d['cell_number'], 10)
                cell['output_safe_bit'] = d['cell_info']['cell_spec']['safe_bit']

                cell['oe'] = int(d['cell_info']['input_or_disable_spec']['control_cell'], 10)
                cell['oe_disable_value'] = int(d['cell_info']['input_or_disable_spec']['disable_value'], 2)
                cell['oe_disable_result'] = d['cell_info']['input_or_disable_spec']['disable_result']

            elif function == 'bidir':
                assert 'input' not in cell
                assert 'output' not in cell
                assert 'io' not in cell

                cell['io'] = int(d['cell_number'], 10)
                cell['output_safe_bit'] = d['cell_info']['cell_spec']['safe_bit']

                cell['dir'] = int(d['cell_info']['input_or_disable_spec']['control_cell'], 10)
                cell['dir_disable_value'] = int(d['cell_info']['input_or_disable_spec']['disable_value'], 2)
                cell['dir_disable_aresult'] = d['cell_info']['input_or_disable_spec']['disable_result']

            else:
                print("warning: %s, unknown cell function %s" % (repr(name), repr(function)))
                continue

            cells[name] = cell

        return cells

    @lazy_value
    def portmaps(self):
        portmaps = {}
        for m in self.json['device_package_pin_mappings']:
            name = m['pin_mapping_name']
            portmap = {}
            for d in m['pin_map']:
                port = d['port_name']
                assert port not in portmap
                portmap[port] = list(d['pin_list'])
            portmaps[name] = portmap
        return portmaps

    @lazy_value
    def pinmaps(self):
        pinmaps = {}
        for name, portmap in self.portmaps.items():
            pinmap = {}
            for port, pins in portmap.items():
                for pin in pins:
                    assert pin not in pinmap
                    pinmap[pin] = port
            pinmaps[name] = pinmap
        return pinmaps

class BS(object):
    def __init__(self, ocd, tap, fn, verbose = 1):
        self.ocd = ocd
        self.tap = tap
        self.verbose = verbose
        self.flushcount = 1024

        self.bsdl = ParsedBsdl(fn)

        if 0:
            print(json.dumps(self.bsdl.json, indent = 4))
            print()

        if self.verbose:
            print("name", self.bsdl.name)

        self.flush()

        self.oplen = self.bsdl.oplen
        if self.verbose:
            print("opcode length", self.oplen)

        self.op_idcode = self.bsdl.opcodes['IDCODE']
        if self.verbose:
            print("IDCODE {1:0{0}b}".format(self.oplen, self.op_idcode))

        self.op_usercode = self.bsdl.opcodes['USERCODE']
        if self.verbose:
            print("USERCODE {1:0{0}b}".format(self.oplen, self.op_usercode))

        self.op_bypass = self.bsdl.opcodes['BYPASS']
        if self.verbose:
            print("BYPASS {1:0{0}b}".format(self.oplen, self.op_bypass))

        self.op_highz = self.bsdl.opcodes['HIGHZ']
        if self.verbose:
            print("HIGHZ {1:0{0}b}".format(self.oplen, self.op_highz))

        self.op_sample = self.bsdl.opcodes['SAMPLE']
        if self.verbose:
            print("SAMPLE {1:0{0}b}".format(self.oplen, self.op_sample))

        self.op_extest = self.bsdl.opcodes['EXTEST']
        if self.verbose:
            print("EXTEST {1:0{0}b}".format(self.oplen, self.op_extest))

        self.chainlen = self.bsdl.chainlen
        if self.verbose:
            print('chainlen', self.chainlen)

        self.idcode, self.idmask = self.bsdl.idcode_idmask
        if self.verbose:
            print("idcode {0:08x} {0:032b}".format(self.idcode))
            print("idmask {0:08x} {0:032b}".format(self.idmask))

    def check_idcode(self):
        self.ocd.cmd('irscan %s 0x%x' % (self.tap, self.op_idcode))
        t = int(self.ocd.cmd('drscan %s 32 0' % self.tap), 16)

        assert t & self.idmask == self.idcode & self.idmask

    def check_usercode(self):
        self.ocd.cmd('irscan %s 0x%x' % (self.tap, self.op_usercode))
        t = int(self.ocd.cmd('drscan %s 32 0' % self.tap), 16)

        print("usercode 0x%08x" % t)

    def bypass(self):
        self.ocd.cmd('irscan %s 0x%x' % (self.tap, self.op_bypass))

    def highz(self):
        self.ocd.cmd('irscan %s 0x%x' % (self.tap, self.op_highz))

    def flush(self, count = None):
        if count is None:
            count = self.flushcount

        data = (1 << self.flushcount) - 1

        self.ocd.cmd('irscan %s 0x%x' % (self.tap, data))

    def extest(self, data = 0):
        self.ocd.cmd('irscan %s 0x%x' % (self.tap, self.op_extest))
        t = int(self.ocd.cmd('drscan %s %u 0x%x' % (self.tap, self.chainlen, data)), 16)
        return t

    def sample(self, data = 0):
        self.ocd.cmd('irscan %s 0x%x' % (self.tap, self.op_sample))
        t = int(self.ocd.cmd('drscan %s %u 0x%x' % (self.tap, self.chainlen, data)), 16)
        return t

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

    bs.check_idcode()

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
                wdata |= 1 << rx_cell['oe']
                wdata ^= 1 << rx_cell['output']

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
