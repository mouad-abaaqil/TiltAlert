"""TiltAlert V2 electronics (board TA-MB-01, nRF9151) as simplified solids.

Outline sizes come from hardware/trace-v2/netlist.json, which cites a source
or marks the value as an indicative envelope.  Positions on the board are a
proposed floorplan: they exist to check clearances and to draw the plans, not
to replace PCB routing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from build123d import Align, Box, Compound, Cylinder, Pos, Vector

NETLIST = Path(__file__).resolve().parents[1] / "hardware" / "trace-v2" / "netlist.json"
MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# Board-top floorplan, millimetres from the board centre (x along the length).
FLOORPLAN = {
    "U1": (-6, 2), "U4": (-22, -6), "U5": (-6, -13), "U2": (8, -10), "U3": (8, -16),
    "U6": (10, 8), "ANT2": (24, 8), "ANT1": (24, -22.5), "J1": (-34.65, 6), "SW1": (-36, -8),
    "J2": (-6, 16), "BZ1": (-22, 14), "D1": (-22, 2), "J3": (-26, -19), "Q1": (-13, 13),
    "D2": (-13, 18), "J4": (8, 20),
}
# LTE antenna ground clearance on the board: no part may enter it.
ANT1_KEEPOUT = (14, 34, -25, -15)


def load_netlist():
    return json.loads(NETLIST.read_text(encoding="utf-8"))


@dataclass
class Part:
    ref: str
    find: int
    name: str
    solid: object               # placed in assembly coordinates
    mount: str                  # "pcb", "base" or "lid": which group carries the part
    ports: dict = field(default_factory=dict)
    in_cavity: bool = True      # False for parts that pass through a wall (light pipe)
    on_board: bool = False      # sits on PCB1, so it touches the board by design


def box_at(x, y, z, l, w, h):
    return Pos(x, y, z) * Box(l, w, h, align=MIN)


def board_outline(d):
    """PCB with notches around the four lid-screw bosses."""
    pcb = Box(d.pcb_length, d.pcb_width, d.pcb_thickness, align=MIN)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pcb -= Pos(sx * d.screw_x, sy * d.screw_y, -1) * Cylinder(
                d.boss_radius + d.pcb_notch_gap, d.pcb_thickness + 2, align=MIN)
    return pcb


def build_parts(d):
    comps = {c["ref"]: c for c in load_netlist()["components"]}
    parts = []
    top = d.pcb_z + d.pcb_thickness

    def add(ref, solid, mount, ports=None, **kw):
        c = comps[ref]
        parts.append(Part(ref, c["find"], c["name"], solid, mount,
                          {k: Vector(*v) for k, v in (ports or {}).items()}, **kw))

    add("PCB1", Pos(0, 0, d.pcb_z) * board_outline(d), "pcb")
    for ref, (x, y) in FLOORPLAN.items():
        l, w, h = comps[ref]["size_mm"]
        solid = box_at(x, y, top, l, w, h)
        if ref == "ANT2":   # ceramic patch with its centre feed pin
            solid = Compound(children=[solid, Pos(x + 2, y, top + h) * Cylinder(0.8, 0.2, align=MIN)])
        add(ref, solid, "pcb", {"C": (x, y, top + h)}, on_board=True)

    bl, bw, bh = comps["BT1"]["size_mm"]
    add("BT1", box_at(d.battery_x, 0, d.floor + d.foam, bl, bw, bh), "base",
        {"LEAD": (d.battery_x - bl / 2, -bw / 2 + 4, d.floor + d.foam + bh / 2)})
    lx, ly = FLOORPLAN["D1"]
    add("LP1", Pos(lx, ly, top + 0.8) * Cylinder(d.light_pipe_d / 2, d.height - top - 0.8, align=MIN),
        "lid", in_cavity=False)
    return parts


def wire_routes(parts):
    """The only cable: battery lead to J3 (everything else is a PCB trace)."""
    p = {part.ref: part.ports for part in parts}
    return {"W1": [p["BT1"]["LEAD"], p["J3"]["C"]]}


def validate_netlist(data):
    comps = {c["ref"]: c for c in data["components"]}
    assert len(comps) == len(data["components"]), "Duplicate component reference"
    finds = [c["find"] for c in data["components"]]
    assert len(finds) == len(set(finds)), "Duplicate find number"
    terminals = [t for n in data["nets"] for t in n["terminals"]]
    assert len(terminals) == len(set(terminals)), "Terminal assigned to two nets"
    assert all(t.split(".")[0] in comps for t in terminals), "Unknown reference in nets"
    nets = {n["name"]: set(n["terminals"]) for n in data["nets"]}
    # Every supply pin sits on its declared rail and that rail fits the part's range.
    for pin, rail in data["supply_pins"].items():
        assert pin in nets[rail], f"{pin} is not on {rail}"
        ref, name = pin.split(".")
        lo, hi = comps[ref]["supply"][name]
        r = data["rails"][rail]
        assert lo <= r["min_v"] and r["max_v"] <= hi, f"{rail} {r['min_v']}–{r['max_v']} V outside {pin} {lo}–{hi} V"
    for ref, c in comps.items():
        for name in c.get("supply", {}):
            assert f"{ref}.{name}" in data["supply_pins"], f"{ref}.{name} supply not checked"
    # Every IC that has a ground reaches GND.
    for ref in ("U1", "U2", "U3", "U4", "U5", "U6"):
        assert f"{ref}.GND" in nets["GND"], f"{ref} has no ground"
    assert not nets["VSYS"] & nets["V1V8"], "Rails shorted"
    # Shared buses: distinct chip selects / addresses, every member on the bus lines.
    spi = data["buses"]["SPI"]
    assert len(set(spi["chip_selects"].values())) == len(spi["chip_selects"])
    for ref in spi["members"]:
        assert any(t.startswith(ref + ".") for t in nets["SPI_SCK"]), f"{ref} off SPI"
        assert any(t.startswith(ref + ".") for t in nets[spi["chip_selects"][ref]])
    i2c = data["buses"]["I2C"]
    assert len(set(i2c["addresses"].values())) == len(i2c["addresses"]), "I²C address conflict"
    for ref in i2c["members"]:
        assert f"{ref}.SDA" in nets["I2C_SDA"] and f"{ref}.SCL" in nets["I2C_SCL"], f"{ref} off I²C"
    for w in data["wires"]:
        for s in w["signals"]:
            owners = {t.split(".")[0] for t in nets[s]}
            assert {w["from"], w["to"]} <= owners, f"{w['id']} carries {s} to a part not on that net"
    return nets
