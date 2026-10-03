"""Physical breadboard layout of the TiltAlert Uno prototype.

The drawing is produced from a placement table (component leg -> breadboard
hole) and a jumper list.  `validate_layout` rebuilds the electrical nodes of
that physical layout (breadboard strips, rails, jumpers) and checks that they
match the reviewed netlist exactly before anything is drawn.
"""

import html

PX = 6.0          # drawing units per millimetre for the Uno outline
PITCH = 15.24     # 2.54 mm breadboard pitch at PX
BB_X, BB_Y = 690, 330
COLS = 30
ROWS = "abcdefghij"

# Uno R3 header positions in mm from the board's lower-left corner (indicative,
# from the common Uno R3 outline).  Board is 68.58 x 53.34 mm.
UNO_W, UNO_H = 68.58, 53.34
UNO_X, UNO_Y = 90, 340
DIGITAL = {f"D{n}": (63.5 - 2.54 * n, 50.8) for n in range(8)}
DIGITAL.update({f"D{n}": (41.656 - 2.54 * (n - 8), 50.8) for n in range(8, 14)})
DIGITAL.update({"GND_TOP": (26.416, 50.8), "AREF": (23.876, 50.8), "SDA": (21.336, 50.8), "SCL": (18.796, 50.8)})
POWER = {"IOREF": (30.48, 2.54), "RESET": (33.02, 2.54), "3V3": (35.56, 2.54), "5V": (38.1, 2.54),
         "GND": (40.64, 2.54), "GND2": (43.18, 2.54), "VIN": (45.72, 2.54)}
ANALOG = {f"A{n}": (50.8 + 2.54 * n, 2.54) for n in range(6)}

# Component legs placed in breadboard holes "<row><col>" or rails "+N" / "-N".
PLACEMENT = {
    "S1.1": "h4", "S1.2": "h7",
    "R1.1": "i7", "R1.2": "-7",
    "S2.1": "h11", "S2.2": "h14",
    "R2.1": "g18", "R2.2": "g22",
    "D1.A": "i22", "D1.K": "i23",
}
# Jumpers: (from, to, label).  Ends are holes, rails, Uno pins "U1.X" or "BZ1.X".
JUMPERS = [
    ("U1.5V", "+1", "+5V"), ("U1.GND", "-1", "GND"),
    ("U1.D2", "f7", "D2"), ("U1.D12", "f11", "D12"), ("U1.D13", "f18", "D13"), ("U1.D3", "f27", "D3"),
    ("j4", "+4", ""), ("j14", "-14", ""), ("j23", "-23", ""),
    ("BZ1.SIG", "j27", "SIG"), ("BZ1.VCC", "+29", "+5V"), ("BZ1.GND", "-30", "GND"),
]
BZ = {"x": 1060, "y": 720, "w": 170, "h": 110, "pins": ["SIG", "VCC", "GND"]}


def node_of(end):
    """Electrical node of a hole, rail position or named pin."""
    if end.startswith(("U1.", "BZ1.")):
        return ("pin", end)
    if end[0] in "+-":
        return ("rail", end[0])
    row, col = end[0], int(end[1:])
    assert row in ROWS and 1 <= col <= COLS, f"Hole {end} outside breadboard"
    return ("strip", col, "top" if row in "abcde" else "bottom")


def validate_layout(nets):
    parent = {}

    def find(n):
        parent.setdefault(n, n)
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def union(a, b):
        parent[find(a)] = find(b)

    for a, b, _ in JUMPERS:
        union(node_of(a), node_of(b))
    used_holes = list(PLACEMENT.values()) + [e for j in JUMPERS for e in j[:2] if not e.startswith(("U1.", "BZ1.", "+", "-"))]
    assert len(set(used_holes)) == len(used_holes), "Two legs or jumpers share one breadboard hole"

    def terminal_node(t):
        return find(node_of(PLACEMENT[t]) if t in PLACEMENT else node_of(t))

    roots = {}
    for name, terminals in nets.items():
        found = {terminal_node(t) for t in terminals}
        assert len(found) == 1, f"Net {name} is split on the breadboard: {sorted(terminals)}"
        roots[name] = found.pop()
    assert len(set(roots.values())) == len(roots), "Two nets are shorted on the breadboard"
    placed = set(PLACEMENT) | {e for j in JUMPERS for e in j[:2] if e.startswith(("U1.", "BZ1."))}
    assert placed == {t for ts in nets.values() for t in ts}, "Layout and netlist terminals differ"
    return roots


# ---------------------------------------------------------------- drawing

def esc(v):
    return html.escape(str(v), quote=True)


def text(x, y, value, cls="label", anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}"{a}>{esc(value)}</text>'


def uno_xy(mm):
    return UNO_X + mm[0] * PX, UNO_Y + (UNO_H - mm[1]) * PX


def hole_xy(end):
    if end[0] in "+-":
        col = int(end[1:])
        y = BB_Y + PITCH * (13.6 if end[0] == "+" else 14.6)
        return BB_X + PITCH * (col + 0.5), y
    row, col = ROWS.index(end[0]), int(end[1:])
    y = BB_Y + PITCH * (1.6 + row + (1 if row >= 5 else 0))
    return BB_X + PITCH * (col + 0.5), y


def pin_xy(name):
    if name.startswith("BZ1."):
        i = BZ["pins"].index(name[4:])
        return BZ["x"], BZ["y"] + 25 + i * 30
    pin = name[3:]
    if pin in POWER:
        return uno_xy(POWER[pin])
    return uno_xy(DIGITAL[pin])


def draw_uno():
    x0, y0 = UNO_X, UNO_Y
    w, h = UNO_W * PX, UNO_H * PX
    p = [f'<path class="symbol" d="M{x0} {y0} H{x0 + w - 12} L{x0 + w} {y0 + 12} V{y0 + h - 30} '
         f'L{x0 + w - 14} {y0 + h - 16} V{y0 + h} H{x0} Z"/>']
    p.append(f'<rect class="symbol" x="{x0 - 38}" y="{uno_xy((0, 43.9))[1]:.1f}" width="96" height="73"/>')
    p.append(text(x0 + 10, uno_xy((0, 37))[1], "USB-B", "tiny"))
    p.append(f'<rect class="symbol" x="{x0 - 11}" y="{uno_xy((0, 12.2))[1]:.1f}" width="80" height="54"/>')
    p.append(text(x0 + 10, uno_xy((0, 6))[1], "JACK DC", "tiny"))
    # ATmega328P DIP-28 and reset button.
    cx, cy = uno_xy((44, 26))
    p.append(f'<rect class="symbol" x="{cx - 108}" y="{cy - 26}" width="216" height="52"/>')
    p.append(f'<circle class="symbol" cx="{cx - 96}" cy="{cy}" r="5"/>')
    for i in range(14):
        for yy in (cy - 33, cy + 27):
            p.append(f'<rect class="thin" x="{cx - 99 + i * 15.24:.1f}" y="{yy}" width="6" height="6"/>')
    p.append(text(cx, cy + 6, "ATmega328P", "small", "middle"))
    p.append(f'<rect class="symbol" x="{x0 + 8}" y="{y0 + 10}" width="30" height="30"/><circle class="symbol" cx="{x0 + 23}" cy="{y0 + 25}" r="9"/>')
    p.append(text(x0 + 46, y0 + 30, "RESET", "tiny"))
    p.append(text(x0 + w / 2 - 20, y0 + h / 2 - 40, "U1  ARDUINO UNO R3", "ref", "middle"))
    # Headers with every pin; used pins are labelled bold.
    used = {j[0][3:] for j in JUMPERS if j[0].startswith("U1.")}
    for group, side in ((DIGITAL, "top"), (POWER, "bottom"), (ANALOG, "bottom")):
        xs = [uno_xy(v)[0] for v in group.values()]
        yy = uno_xy(next(iter(group.values())))[1]
        p.append(f'<rect class="thin" x="{min(xs) - 9:.1f}" y="{yy - 9:.1f}" width="{max(xs) - min(xs) + 18:.1f}" height="18"/>')
        for name, mm in group.items():
            x, y = uno_xy(mm)
            p.append(f'<rect class="{"accent" if name in used else "pad"}" x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8"/>')
            label = name.replace("GND_TOP", "GND").replace("GND2", "GND")
            ly = y + 24 if side == "top" else y - 16
            p.append(f'<text class="{"pinb" if name in used else "pins"}" x="{x:.1f}" y="{ly:.1f}" '
                     f'transform="rotate(-90 {x:.1f} {ly:.1f})" text-anchor="{"end" if side == "top" else "start"}">{esc(label)}</text>')
    return p


def draw_breadboard():
    w = PITCH * (COLS + 1)
    h = PITCH * 16
    p = [f'<rect class="symbol" x="{BB_X}" y="{BB_Y}" width="{w:.1f}" height="{h:.1f}" rx="6"/>',
         f'<rect class="dash" x="{BB_X + 8}" y="{BB_Y + PITCH * 6.65:.1f}" width="{w - 16:.1f}" height="{PITCH * 0.7:.1f}"/>']
    for c in range(1, COLS + 1):
        for r in ROWS:
            x, y = hole_xy(f"{r}{c}")
            p.append(f'<rect class="hole" x="{x - 2.5:.1f}" y="{y - 2.5:.1f}" width="5" height="5"/>')
        if c % 5 == 0 or c == 1:
            p.append(text(hole_xy(f"a{c}")[0], BB_Y + PITCH * 0.95, c, "tiny", "middle"))
        for rail in "+-":
            x, y = hole_xy(f"{rail}{c}")
            p.append(f'<rect class="hole" x="{x - 2.5:.1f}" y="{y - 2.5:.1f}" width="5" height="5"/>')
    for r in ROWS:
        x, y = hole_xy(f"{r}1")
        p.append(text(BB_X + 6, y + 4, r, "tiny"))
    for rail, label in (("+", "+5V"), ("-", "GND")):
        _, y = hole_xy(f"{rail}1")
        p.append(f'<path class="thin" d="M{BB_X + 12} {y + (-8 if rail == "+" else 8)} H{BB_X + w - 12}"/>')
        p.append(text(BB_X - 10, y + 5, f"{label} {rail}", "net", "end"))
    p.append(text(BB_X + w / 2, BB_Y - 12, "BREADBOARD 30 COLONNES — BANDES a–e / f–j, RAILS BAS", "small", "middle"))
    return p


def draw_parts(comp):
    p = []
    def leg(a, b):
        return hole_xy(PLACEMENT[a]), hole_xy(PLACEMENT[b])
    # S1 tilt contact: metal can between its two legs.
    (x1, y1), (x2, y2) = leg("S1.1", "S1.2")
    p += [f'<path class="symbol" d="M{x1} {y1} V{y1 - 30} M{x2} {y2} V{y2 - 30}"/>',
          f'<rect class="part" x="{x1 - 6:.1f}" y="{y1 - 64:.1f}" width="{x2 - x1 + 12:.1f}" height="34" rx="14"/>',
          text((x1 + x2) / 2, y1 - 42, "S1", "net", "middle")]
    (x1, y1), (x2, y2) = leg("R1.1", "R1.2")
    p += [f'<path class="symbol" d="M{x1} {y1} V{y2}"/>',
          f'<rect class="part" x="{x1 - 7:.1f}" y="{y1 + 4:.1f}" width="14" height="{y2 - y1 - 10:.1f}" rx="5"/>',
          text(x1 + 10, y2 + 24, "R1", "net")]
    (x1, y1), (x2, y2) = leg("S2.1", "S2.2")
    p += [f'<path class="symbol" d="M{x1} {y1} V{y1 - 26} M{x2} {y2} V{y2 - 26}"/>',
          f'<rect class="part" x="{x1 - 8:.1f}" y="{y1 - 62:.1f}" width="{x2 - x1 + 16:.1f}" height="36"/>',
          f'<circle class="symbol" cx="{(x1 + x2) / 2:.1f}" cy="{y1 - 44:.1f}" r="11"/>',
          text(x2 + 14, y1 - 40, "S2", "net")]
    (x1, y1), (x2, y2) = leg("R2.1", "R2.2")
    p += [f'<path class="symbol" d="M{x1} {y1} H{x2}"/>',
          f'<rect class="part" x="{x1 + 10:.1f}" y="{y1 - 7:.1f}" width="{x2 - x1 - 20:.1f}" height="14" rx="5"/>',
          text((x1 + x2) / 2, y1 + 26, "R2", "net", "middle")]
    (x1, y1), (x2, y2) = leg("D1.A", "D1.K")
    p += [f'<path class="symbol" d="M{x1} {y1} V{y1 - 22} M{x2} {y2} V{y2 - 22}"/>',
          f'<path class="part" d="M{x1 - 9:.1f} {y1 - 22:.1f} H{x2 + 9:.1f} V{y1 - 44:.1f} a{(x2 - x1) / 2 + 9:.1f} 12 0 0 0 {-(x2 - x1) - 18:.1f} 0 Z"/>',
          text(x2 + 12, y1 - 30, "D1", "net")]
    b = BZ
    p += [f'<rect class="part" x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}"/>',
          f'<circle class="symbol" cx="{b["x"] + 110}" cy="{b["y"] + 55}" r="30"/><circle class="symbol" cx="{b["x"] + 110}" cy="{b["y"] + 55}" r="6"/>',
          text(b["x"] + b["w"] / 2, b["y"] - 12, "BZ1 buzzer ACTIF", "net", "middle")]
    for i, pin in enumerate(b["pins"]):
        x, y = pin_xy(f"BZ1.{pin}")
        p += [f'<circle class="junction" cx="{x}" cy="{y}" r="4"/>', text(x + 10, y + 5, pin, "tiny")]
    return p


def route(a, b, k):
    """Orthogonal jumper path with its own lane so wires never overlap."""
    (x1, y1), (x2, y2) = (pin_xy(a) if a.startswith(("U1.", "BZ1.")) else hole_xy(a)), hole_xy(b)
    if a.startswith("U1.") and y1 < UNO_Y + 100:          # digital header: over the top
        lane = UNO_Y - 50 - k * 16
        return f"M{x1:.1f} {y1:.1f} V{lane} H{x2:.1f} V{y2:.1f}"
    if a.startswith("U1."):                               # power header: under the board
        lane = BB_Y + PITCH * 16 + 40 + k * 16
        return f"M{x1:.1f} {y1:.1f} V{lane} H{x2:.1f} V{y2:.1f}"
    if a.startswith("BZ1."):
        lane = x1 - 30 - k * 12
        return f"M{x1:.1f} {y1:.1f} H{lane} V{y2 + 30 + k * 8:.1f} H{x2:.1f} V{y2:.1f}"
    return f"M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}"


def draw_wires():
    p = []
    for k, (a, b, label) in enumerate(JUMPERS):
        lane_k = {"U1.D2": 3, "U1.D3": 0, "U1.D12": 2, "U1.D13": 1, "U1.5V": 0, "U1.GND": 1,
                  "BZ1.SIG": 0, "BZ1.VCC": 1, "BZ1.GND": 2}.get(a, 0)
        d = route(a, b, lane_k)
        p.append(f'<path class="jumper" d="{d}"/>')
        for end in (a, b):
            x, y = pin_xy(end) if end.startswith(("U1.", "BZ1.")) else hole_xy(end)
            p.append(f'<circle class="junction" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
        if label and a.startswith("U1."):
            x2, _ = hole_xy(b)
            y = (UNO_Y - 50 - lane_k * 16 - 5) if pin_xy(a)[1] < UNO_Y + 100 else (BB_Y + PITCH * 16 + 40 + lane_k * 16 - 5)
            p.append(text(x2 - 6, y, label, "netw", "end"))
    return p


def build_physical_svg(data, header, footer):
    comp = {c["ref"]: c for c in data["components"]}
    p = [header("TILTALERT / IMPLANTATION PHYSIQUE", "UNO · REV A", "Breadboard + jumpers — vue de dessus")]
    p += draw_uno() + draw_breadboard() + draw_parts(comp) + draw_wires()
    # Connection list keyed to the drawing.
    x, y = 1225, 190
    p.append(text(x, y, "LISTE DES LIAISONS", "section"))
    rows = [("U1 5V", "rail +", "+5V"), ("U1 GND", "rail −", "GND"), ("U1 D2", "f7 (S1, R1)", "TILT_D2"),
            ("U1 D12", "f11 (S2)", "RESET_D12"), ("U1 D13", "f18 (R2)", "ALARM_D13"), ("U1 D3", "f27 → BZ1", "BUZZ_D3"),
            ("R2 → D1", "g22 / i22", "LED_A"), ("j4 / j14 / j23", "rails", "S1 +, S2/D1 −")]
    for i, (a, b, n) in enumerate(rows):
        yy = y + 34 + i * 27
        p += [text(x, yy, a, "small"), text(x + 100, yy, b, "small"), text(x + 218, yy, n, "tiny")]
    for i, line_ in enumerate(["S1  contact d'inclinaison NO", "S2  bouton poussoir NO", "R1  10 kΩ (rappel D2)",
                               "R2  220 Ω (LED)", "D1  LED rouge", "BZ1 buzzer ACTIF 5 V"]):
        p.append(text(x, y + 290 + i * 24, line_, "small"))
    p.append(footer([
        "IMPLANTATION CONTRÔLÉE PAR SCRIPT : BANDES, RAILS ET JUMPERS REDONNENT EXACTEMENT LA NETLISTE (7 RÉSEAUX, AUCUN COURT-CIRCUIT)",
        "S1 = contact d'inclinaison nu. Module KY-020 : mesurer S–+V et S–GND ; si une résistance de rappel vers +V existe, retirer R1.",
    ], "TA-EL-002", "IMPLANTATION PHYSIQUE — PROTOTYPE ARDUINO UNO"))
    return "\n".join(p)
