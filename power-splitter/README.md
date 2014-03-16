# A GPS power splitter with optional LNA

This is a simple three way power splitter intented to be used with a
GPS receiver and an active antenna.

The splitter has a built in bias-T which can pass DC, allowing an
active antenna to be connected to the input to be powered from a GPS
receiver connected to output port 1.

The design also also has optional space for adding a Mini-Circuits
PSA-5451+ or PSA-5453+ low noise amplifier (LNA) which is powered from
the same bias-T via a MIC5365 LDO.  The LDO allows the splitter to be
powered from 3.3V to 5V.

Just about any through hole SMA or MCX connector with 5.08mm / 0.2"
spacing between the ground pins can be used.

This design has been manufactured using a 4 layer board from JLCPCB
using their recommended trace widths to get 50 Ohm traces with the
JLC7628 stackup.  The board can also use the JLCPCB assembly service
letting them place most components on the board.

# Resistive splitter theory

A good summary of the theory can be found on
[the Microwaves101 page on resistive power splitters](https://www.microwaves101.com/encyclopedias/resistive-power-splitters).

One of the simplest N-way resistive splitters consists of a junction
with N+1 identical branches with a series resistor on each branch
which matches the impedances of each branch.  For a N way splitter the
resistor should be:

> R = Z0 * (N-1) / (N+1) Ohm

The loss from the input to each output will be:

> 10 * log10((1 / N) ** 2) dB

For a three way 50 Ohm splitter like this one the series resistance
should then be:

> 50 * (3-1) / (3+1) = 25 Ohms

The theoretical loss from the input to each output will be:

> 10*log10((1/3)**2) = -9.54 dB

As a verification that the calculated resistance is correct, look from
the junction point at the three output branches.  Assume that each
output is terminated in 50 Ohm.  Add the 25 Ohm resistors in series
giving a total of 75 Ohm on each branch.  Seen from the junction point
there will be three 75 Ohm resistors in parallel to ground giving a
total resistance of:

> 1 / (1/75 + 1/75 + 1/75) = 75/3 = 25 Ohms

Add the 25 Ohm resistor on the input branch and the total impedance
seen from the input port will be 50 Ohm.

Since 25 Ohm is not a common resistance, the schematic uses two
resistors in series (10 Ohm + 15 Ohm) from the more common E12 series
of resistors to get the correct resistance.

# Optional LNA

The design for the optional LNA in the schematic is basically the
"recommended application circuit" from the
[Mini-Circuits PSA-5351+ data sheet](https://www.minicircuits.com/pdfs/PSA-5451+.pdf).
This LNA should be usable from 50 MHz up to 4 GHz and have gain from
about 22 dB at low frequencies to 10 dB at high frequencies.  With the
resistive splitter having about a 10 dB loss the combination of LNA
and splitter should have a gain from the input to an output of about
10 dB at the low frequencies to 0 dB at the high frequencies.

To make it possible to switch between using the LNA or not, the
footprints for capacitors C1 and C3 on the input and resistors R8 and
R11 on the output overlap.  To use the design as a passive splitter,
use C3 and R11.  To use the design with the LNA, mount the LNA and LDO
and their passives and use C1 and R8.

It should also be possible to use a
[Mini-Circuits PSA-5453+ LNA](https://www.minicircuits.com/pdfs/PSA-5453+.pdf)
which has slightly higher gain.  In that case change bias resistor R6
to 681 Ohm.

# Manufacturing using JLCPCB

This design has been manufactured using JLCPCB's assembly service
letting them place most components.  The schematic contains the JLCPCB
part numers for the components that JLCPCB keep in stock.  As
configured the splitter is built for the LNA variant but withouth the
PSA-5451+ LNA itself since JLCPCB does not have it in stock.

## Create the files needed to manufacture the PCBs

Open the PCB Editor and use the "File" menu, "Fabrication Outputs" and
then both "Gerbers" and "Drill Files".

This will create a bunch of ".gbr" files with the gerber files for the
PCB and ".drl" files with the drills.

Create a zip file all the fabrication outputs.

```bash
rm -f power-splitter.zip
zip power-splitter.zip power-splitter-*.{gbr,drl}
```

Upload the file "power-splitter.zip" when ordering the PCBs.  Make
sure to use the "JLC7628" stackup and to select "Impedance" and "Yes"
to get an impedance controlled board.

## Create the files needed to assemble the PCBs

Open the Schematic Editor and export the BOM file using any of the
choices found from the "Tools" menu and "Generate BOM".  For some
reason this gives an error message but it doesn't matter since it does
create the XML file which is needed by jlc-kicad-tools below.

Open the PCB Editor and use the "File" menu, "Fabrication Outputs" and
"Component Placement".

The BOM and placement files from KiCad are not directly compatible
with JLCPCBs assembly service, but there is a nice tool called
[jlc-kicad-tools](https://github.com/matthewlai/JLCKicadTools) which
can take the KiCad files and modify them so that they will work JLCCB.

Install jlc-kicad-tools:

```bash
pip3 install jlc-kicad-tools
```

Open a shell prompt in the directory and convert the files to JLCPCB
compatible files.

```bash
jlc-kicad-tools .
```

Upload the files "power-splitter_bom_jlc.csv" and
"power-splitter_cpl_jlc.csv" when ordering the assembly service.

# TODO

The PCB layout for the LNA in this design is different from the
recommended layout.  It also uses a different inductor L3 with higher
resistance than recommended just to keep costs down.  If I ever respin
this board I probably should try to use the recommended layout and
recommended inductor instead of the ones I'm using right now.  The
current design works decently, but it might be possible to improve it.

The layout could probably be improved to reduce the impedance
mismatches for the SMA connectors.

Can the input/output matching be improved.

Redo the design to fit in some existing enclosure, maybe something
like the Hammond 1455D601.  Or if it's possible to find some RF
shielded enclosure of similar size.

Add a small shield can over the LNA and splitter components on the
PCB.
