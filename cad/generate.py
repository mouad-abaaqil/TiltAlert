#!/usr/bin/env python3
"""Parametric enclosure, V2 electronics layout and A3 drawing set for TiltAlert.

All dimensions are millimetres.  Run with Python 3.12 and build123d 0.13.0.
The enclosure is a design study, not a measured or production-ready part.
Component outlines come from hardware/trace-v2/netlist.json; heights marked
"gabarit" there are indicative envelopes used for clearance checks.
"""

from __future__ import annotations

import argparse
import math
import shutil
from dataclasses import dataclass
from html import escape
from pathlib import Path
import subprocess

from build123d import (
    Align, Box, Cylinder, Compound, Plane, Pos, Rot, Shape,
    export_step, export_stl, fillet, section,
)

from drafting import balloon, dim_h, dim_v, line, rect, sheet_start, table, txt
from components import ANT1_KEEPOUT, build_parts, load_netlist, validate_netlist, wire_routes

MIN = (Align.CENTER, Align.CENTER, Align.MIN)


@dataclass(frozen=True)
class Dimensions:
    length: float = 86
    width: float = 58
    height: float = 20
    base_height: float = 15
    wall: float = 2.5
    floor: float = 2
    roof: float = 2
    corner_radius: float = 6
    screw_x: float = 36.5
    screw_y: float = 23
    boss_radius: float = 3.5
    screw_diameter: float = 2.7
    # External strap ears at both ends, so the strap never crosses the cavity.
    ear_length: float = 10
    ear_thickness: float = 5
    strap_slot_width: float = 4
    strap_slot_length: float = 30
    # Main board TA-MB-01, held above the battery.
    pcb_length: float = 76
    pcb_width: float = 50
    pcb_thickness: float = 1.0
    pcb_z: float = 9.0
    pcb_notch_gap: float = 0.7
    foam: float = 0.5
    battery_x: float = 0
    # Openings: USB-C and side button in the -X wall, light pipe and buzzer vents in the lid.
    usb_y: float = 6
    usb_width: float = 10
    usb_height: float = 4.6
    button_y: float = -8
    button_d: float = 4
    light_pipe_d: float = 3
    light_hole_d: float = 3.4
    vent_d: float = 1.5
    min_clearance: float = 0.2


D = Dimensions()
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = ROOT / "output"
DATE = "2026-10-03"
SHEETS = 4


def rounded_box(length: float, width: float, height: float, z0: float, radius: float):
    solid = Pos(0, 0, z0) * Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    vertical = [e for e in solid.edges() if abs((e.end_point() - e.start_point()).Z) > height - 0.01]
    return fillet(vertical, radius)


def screw_centers(d: Dimensions):
    return [(x, y) for x in (-d.screw_x, d.screw_x) for y in (-d.screw_y, d.screw_y)]


def board_top(d: Dimensions):
    return d.pcb_z + d.pcb_thickness


def make_parts(d: Dimensions = D):
    from components import FLOORPLAN
    # Open topped base.  The cut extends through the top face.
    base = rounded_box(d.length, d.width, d.base_height, 0, d.corner_radius)
    cavity = rounded_box(d.length - 2*d.wall, d.width - 2*d.wall,
                         d.base_height - d.floor + 1, d.floor,
                         d.corner_radius - d.wall)
    base = base - cavity
    # Four coaxial pillars and through bores.  The same centers drive the lid.
    for x, y in screw_centers(d):
        base += Pos(x, y, d.floor) * Cylinder(d.boss_radius, d.base_height-d.floor, align=MIN)
    for x, y in screw_centers(d):
        base -= Pos(x, y, -1) * Cylinder(d.screw_diameter/2, d.base_height+2, align=MIN)
    # Two end ears carry the strap outside the electronics volume.
    for sx in (-1, 1):
        ear_x = sx * (d.length/2 + d.ear_length/2 - 1)
        ear = Pos(ear_x, 0, 0) * Box(d.ear_length + 2, d.strap_slot_length + 10, d.ear_thickness, align=MIN)
        ear -= Pos(ear_x + sx, 0, -1) * Box(d.strap_slot_width, d.strap_slot_length, d.ear_thickness + 2, align=MIN)
        base += ear
    # USB-C and button openings, aligned with J1 and SW1 on the board.
    top = board_top(d)
    base -= Pos(-d.length/2, d.usb_y, top + 1.6 - d.usb_height/2) * Box(
        3*d.wall, d.usb_width, d.usb_height, align=MIN)
    base -= Pos(-d.length/2, d.button_y, top + 1.75) * Rot(0, 90, 0) * Cylinder(d.button_d/2, 3*d.wall)

    # Cap is a separate hollow part.  Its four sleeves meet the base pillars.
    lid_height = d.height - d.base_height
    lid = rounded_box(d.length, d.width, lid_height, d.base_height, d.corner_radius)
    lid -= rounded_box(d.length - 2*d.wall, d.width - 2*d.wall,
                       lid_height-d.roof+0.1, d.base_height-0.1,
                       d.corner_radius-d.wall)
    for x, y in screw_centers(d):
        lid += Pos(x, y, d.base_height) * Cylinder(d.boss_radius, lid_height-d.roof, align=MIN)
    for x, y in screw_centers(d):
        lid -= Pos(x, y, d.base_height-1) * Cylinder(d.screw_diameter/2, lid_height+2, align=MIN)
    lx, ly = FLOORPLAN["D1"]
    lid -= Pos(lx, ly, d.base_height) * Cylinder(d.light_hole_d/2, lid_height + 1, align=MIN)
    bx, by = FLOORPLAN["BZ1"]
    for dx in (-3, 0, 3):
        lid -= Pos(bx + dx, by, d.base_height) * Cylinder(d.vent_d/2, lid_height + 1, align=MIN)
    return base, lid, build_parts(d)


def check(parts, d: Dimensions = D):
    base, lid, electronics = parts
    validate_netlist(load_netlist())
    assert d.height > d.base_height
    assert d.screw_x + d.boss_radius < d.length/2-d.wall
    assert d.screw_y + d.boss_radius <= d.width/2-d.wall + 1e-6
    for part, z0, z1 in ((base, 0, d.base_height), (lid, d.base_height, d.height)):
        bb = part.bounding_box()
        assert abs(bb.size.Y-d.width) < 1e-5
        assert abs(bb.min.Z-z0) < 1e-5 and abs(bb.max.Z-z1) < 1e-5
        assert part.volume > 0
    assert abs(base.bounding_box().size.X - (d.length + 2*d.ear_length)) < 1e-5
    assert abs(lid.bounding_box().size.X - d.length) < 1e-5
    for x, y in screw_centers(d):
        probe = Pos(x, y, 0) * Cylinder(d.screw_diameter/2-0.1, d.height)
        assert base.intersect(probe) is None and lid.intersect(probe) is None
    # The USB-C and button openings really cross the wall in front of J1/SW1.
    top = board_top(d)
    for y, z in ((d.usb_y, top + 1.6), (d.button_y, top + 1.75)):
        probe = Pos(-d.length/2 - 1, y, z) * Box(2*d.wall + 2, 0.5, 0.5)
        assert base.intersect(probe) is None, f"Wall opening at y={y} is blocked"
    # Every part lies inside the cavity and keeps clear of walls, bosses and
    # every other part.  Parts on PCB1 touch the board by design only.
    inner_x, inner_y = d.length/2 - d.wall, d.width/2 - d.wall
    board = next(p for p in electronics if p.ref == "PCB1")
    for p in electronics:
        bb = p.solid.bounding_box()
        assert bb.min.X >= -inner_x and bb.max.X <= inner_x, f"{p.ref} outside cavity in X"
        assert bb.min.Y >= -inner_y and bb.max.Y <= inner_y, f"{p.ref} outside cavity in Y"
        if p.in_cavity:
            assert bb.min.Z >= d.floor and bb.max.Z <= d.height - d.roof, f"{p.ref} outside cavity in Z"
        if p.on_board:
            assert abs(bb.min.Z - top) < 1e-6, f"{p.ref} not seated on PCB1"
            assert abs(bb.min.X) <= d.pcb_length/2 + 1 and abs(bb.max.X) <= d.pcb_length/2 + 1, f"{p.ref} off board"
            assert abs(bb.min.Y) <= d.pcb_width/2 and abs(bb.max.Y) <= d.pcb_width/2, f"{p.ref} off board"
            kx0, kx1, ky0, ky1 = ANT1_KEEPOUT
            if p.ref != "ANT1":
                assert bb.max.X <= kx0 or bb.min.X >= kx1 or bb.max.Y <= ky0 or bb.min.Y >= ky1, \
                    f"{p.ref} inside the LTE antenna keep-out"
        for shell, label in ((base, "base"), (lid, "capot")):
            gap = p.solid.distance_to(shell)
            assert gap >= d.min_clearance - 1e-6, f"{p.ref} touches {label} ({gap:.2f} mm)"
    for i, a in enumerate(electronics):
        for b in electronics[i+1:]:
            if {a.ref, b.ref} & {"PCB1"} and (a.on_board or b.on_board):
                continue
            gap = a.solid.distance_to(b.solid)
            assert gap >= d.min_clearance - 1e-6, f"{a.ref} touches {b.ref} ({gap:.2f} mm)"
    refs = {c["ref"] for c in load_netlist()["components"]}
    assert refs == {p.ref for p in electronics}, "Netlist and CAD part list differ"
    assert board.solid.distance_to(base) >= d.min_clearance


# ---------------------------------------------------------------- projection

def polyline(edge, n=18):
    # Topological edges are projected by OpenCascade; sample curved edges for SVG.
    if edge.geom_type.name == "LINE":
        pts = [edge.start_point(), edge.end_point()]
    else:
        pts = [edge.position_at(i/n) for i in range(n+1)]
    return [(p.X, p.Y) for p in pts]


class View:
    """One orthographic projection; maps both edges and 3D points to the sheet."""

    def __init__(self, shape: Shape, camera, up, cx, cy, scale=1, look_at=(0, 0, 18)):
        self.camera, self.up, self.look_at = camera, up, look_at
        self.cx, self.cy, self.scale = cx, cy, scale
        self.vis, self.hid = shape.project_to_viewport(camera, up, look_at=look_at)
        pts = [p for e in self.vis for p in polyline(e)]
        self.midx = (min(p[0] for p in pts)+max(p[0] for p in pts))/2
        self.midy = (min(p[1] for p in pts)+max(p[1] for p in pts))/2

    def xy(self, x, y):
        return self.cx+(x-self.midx)*self.scale, self.cy-(y-self.midy)*self.scale

    def point(self, v):
        marker = Pos(v.X, v.Y, v.Z) * Box(.02, .02, .02)
        vis, hid = marker.project_to_viewport(self.camera, self.up, look_at=self.look_at)
        p = (vis + hid)[0].start_point()
        return self.xy(p.X, p.Y)

    def svg(self, hidden=True):
        def path_for(edges, cls):
            out = []
            for e in edges:
                coords = " ".join("%.3f,%.3f" % self.xy(x, y) for x, y in polyline(e))
                out.append(f'<polyline class="{cls}" points="{coords}"/>')
            return "".join(out)
        return (path_for(self.hid, "hidden") if hidden else "") + path_for(self.vis, "object")


def section_svg(sections, cx, cy, d: Dimensions, cls="hatch", scale=1.0):
    """Draw the real planar section faces with hatch fill and their boundary edges."""
    markup=[]
    def xy(point):
        return (cx + point.X*scale, cy + (d.height/2 - point.Z)*scale)
    def close(a,b):
        return abs(a.X-b.X)+abs(a.Z-b.Z)<1e-5
    for sk in sections:
        for face in sk.faces():
            edges=list(face.outer_wire().edges())
            if not edges:
                continue
            chain=[edges.pop(0)]
            while edges:
                tip=chain[-1].end_point()
                match=next(((i,e,False) for i,e in enumerate(edges) if close(e.start_point(),tip)),None)
                if match is None:
                    match=next(((i,e,True) for i,e in enumerate(edges) if close(e.end_point(),tip)),None)
                if match is None:
                    raise ValueError('Section perimeter not closed')
                i,e,reverse=match
                chain.append(e.reversed() if reverse else e)
                edges.pop(i)
            points=[]
            for edge in chain:
                samples=[edge.start_point(),edge.end_point()] if edge.geom_type.name=='LINE' else [edge.position_at(i/24) for i in range(25)]
                points.extend(samples[:-1])
            path=' '.join(f'{x:.3f},{y:.3f}' for x,y in map(xy,points))
            markup.append(f'<polygon points="{path}" style="fill:url(#{cls})" class="object"/>')
    return ''.join(markup)


# ------------------------------------------------------------------- sheets

def assembly(parts):
    base, lid, electronics = parts
    return Compound(children=[base, lid] + [p.solid for p in electronics])


def P(x, y, z):
    return Pos(x, y, z).position


def sheet_one(parts, d: Dimensions):
    base, lid, electronics = parts
    full = assembly(parts)
    top_z = board_top(d)
    s = sheet_start(1, "ASSEMBLAGE GÉNÉRAL", "TA-TR-GA-01", "1,4:1 sauf indication")
    k = 1.4
    top = View(full, (0, 0, 200), (0, 1, 0), 106, 92, k)
    s.append(top.svg())
    s.append(txt(106, 146, "PLAN / DESSUS (CAPOT EN TRANSPARENCE) / 1,4:1", 3, "label", "middle"))
    x0, x1 = top.point(P(-d.length/2, 0, d.height))[0], top.point(P(d.length/2, 0, d.height))[0]
    y0, y1 = top.point(P(0, d.width/2, d.height))[1], top.point(P(0, -d.width/2, d.height))[1]
    ex0, ex1 = top.point(P(-d.length/2-d.ear_length, 0, 0))[0], top.point(P(d.length/2+d.ear_length, 0, 0))[0]
    s.append(dim_h(x0, x1, y0-8, y0-1, f"{d.length:g}"))
    s.append(dim_h(ex0, ex1, y0-15, y0-1, f"{d.length+2*d.ear_length:g} HORS TOUT"))
    s.append(dim_v(y0, y1, ex0-6, x0-1, f"{d.width:g}"))
    sy0, sy1 = top.point(P(0, d.screw_y, d.height))[1], top.point(P(0, -d.screw_y, d.height))[1]
    sx1 = top.point(P(d.screw_x, 0, d.height))[0]
    s.append(dim_v(sy0, sy1, ex1+8, sx1, f"{2*d.screw_y:g} C-C"))
    cy = top.point(P(0, d.usb_y, 0))[1]
    s.append(line(ex0-4, cy, ex1+4, cy, "cut"))
    s.append(txt(ex0-6, cy-1.5, "A", 3, "label-bold")); s.append(txt(ex1+4, cy-1.5, "A", 3, "label-bold"))

    front = View(full, (0, -200, 10), (0, 0, 1), 106, 176, k)
    s.append(front.svg())
    s.append(txt(106, 196, "ÉLÉVATION AVANT", 3, "label", "middle"))
    fy0, fy1 = front.point(P(0, 0, d.height))[1], front.point(P(0, 0, 0))[1]
    fx0 = front.point(P(-d.length/2-d.ear_length, 0, 0))[0]
    s.append(dim_v(fy0, fy1, fx0-6, fx0, f"{d.height:g}"))

    side = View(full, (-200, 0, 10), (0, 0, 1), 236, 176, k)
    s.append(side.svg())
    s.append(txt(236, 196, "PROFIL GAUCHE — USB-C ET BOUTON", 3, "label", "middle"))
    pu = side.point(P(-d.length/2, d.usb_y, top_z + 1.6))
    pb = side.point(P(-d.length/2, d.button_y, top_z + 1.75))
    s.append(balloon(pu[0], pu[1], pu[0]-14, pu[1]-22, "U"))
    s.append(balloon(pb[0], pb[1], pb[0]+16, pb[1]-22, "B"))
    s.append(txt(196, 216, f"U  port USB-C {d.usb_width:g} × {d.usb_height:g} (charge) — bouchon silicone", 2.4, "label"))
    s.append(txt(196, 221, f"B  perçage Ø{d.button_d:g} pour SW1 — membrane à prévoir", 2.4, "label"))

    # Exact section through U1, the GNSS patch and the USB-C port (Y = usb_y).
    cut = Plane(origin=(0, d.usb_y, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    shells = [section(base, section_by=cut), section(lid, section_by=cut)]
    inner = [section(solid, section_by=cut) for p in electronics for solid in p.solid.solids()
             if solid.bounding_box().min.Y < d.usb_y < solid.bounding_box().max.Y]
    sc, scx, scy = 1.5, 322, 64
    s.append(section_svg(shells, scx, scy, d, scale=sc))
    s.append(section_svg(inner, scx, scy, d, "hatch2", scale=sc))
    s.append(txt(scx, 94, f"COUPE A–A / Y = +{d.usb_y:g} / 1,5:1", 3, "label", "middle"))
    s.append(txt(scx, 99, "Boîtier hachuré blanc • électronique hachurée jaune (PCB1, U1, U6, ANT2, J1, BT1)",
                 2.2, "sub", "middle"))
    top_y, bot_y = scy - d.height/2*sc, scy + d.height/2*sc
    left = scx - (d.length/2 + d.ear_length)*sc
    s.append(dim_v(top_y, bot_y, left-5, left, f"{d.height:g}"))
    pcb_y = scy + (d.height/2 - top_z)*sc
    right = scx + (d.length/2 + d.ear_length)*sc
    s.append(dim_v(pcb_y, bot_y, right+6, scx + d.length/2*sc, f"PCB {top_z:g}"))

    iso = View(full, (125, -140, 120), (0, 0, 1), 330, 170, 1.0, look_at=(0, 0, 10))
    s.append(iso.svg(hidden=False))
    s.append(txt(330, 214, "VUE ISOMÉTRIQUE ASSEMBLÉE / 1:1", 3, "label", "middle"))
    for (x, y, z), label, dx, dy in (((-22, 2, d.height), "LP1 voyant", -26, -10),
                                     ((-22, 14, d.height), "évents buzzer", -30, 2)):
        px, py = iso.point(P(x, y, z))
        s.append(line(px, py, px+dx, py+dy, "leader") + f'<circle cx="{px:.2f}" cy="{py:.2f}" r=".6" class="dot"/>')
        s.append(txt(px+dx-1, py+dy+1, label, 2.4, "label", "end"))
    s.append('</svg>')
    return ''.join(s)


def ring_positions(points, box, pad):
    """Spread balloons evenly around a rectangle, ordered by angle around its centre."""
    (x0, y0, x1, y1) = box
    cx, cy = (x0+x1)/2, (y0+y1)/2
    order = sorted(points, key=lambda kv: math.atan2(kv[1][1]-cy, kv[1][0]-cx))
    w, h = x1-x0+2*pad, y1-y0+2*pad
    perim = 2*(w+h)
    out = {}
    # Start the walk at the angle of the first item so leaders stay short.
    for i, (key, (px, py)) in enumerate(order):
        ang = math.atan2(py-cy, px-cx)
        t = (i + 0.5) / len(order)
        a = -math.pi + 2*math.pi*t
        a = (a + ang) / 2 if abs(a - ang) < math.pi/2 else a
        dx, dy = math.cos(a), math.sin(a)
        sx = (w/2) / abs(dx) if abs(dx) > 1e-9 else 1e9
        sy = (h/2) / abs(dy) if abs(dy) > 1e-9 else 1e9
        r = min(sx, sy)
        out[key] = (cx + dx*r, cy + dy*r)
    return out


def sheet_two(parts, d: Dimensions):
    base, lid, electronics = parts
    s = sheet_start(2, "CARTE TA-MB-01 ET IMPLANTATION", "TA-TR-GA-02", "2:1 (carte), 1:1")
    top_z = board_top(d)
    on_board = [p for p in electronics if p.on_board]
    pcb = next(p for p in electronics if p.ref == "PCB1")
    k = 2.0
    v = View(Compound(children=[pcb.solid] + [p.solid for p in on_board]), (0, 0, 200), (0, 1, 0), 108, 106, k)
    # LTE antenna keep-out, hatched on the board.
    kx0, kx1, ky0, ky1 = ANT1_KEEPOUT
    (ax, ay), (bx, by) = v.point(P(kx0, ky1, top_z)), v.point(P(kx1, ky0, top_z))
    s.append(f'<rect x="{ax:.2f}" y="{ay:.2f}" width="{bx-ax:.2f}" height="{by-ay:.2f}" style="fill:url(#hatch2)" class="frame"/>')
    s.append(v.svg(hidden=False))
    s.append(txt((ax+bx)/2, ay-1.5, "ZONE DÉGAGÉE ANTENNE LTE", 2.1, "accent", "middle"))
    px0, py0 = v.point(P(-d.pcb_length/2, d.pcb_width/2, top_z))
    px1, py1 = v.point(P(d.pcb_length/2, -d.pcb_width/2, top_z))
    pts = {p.ref: v.point(P(p.ports["C"].X, p.ports["C"].Y, top_z)) for p in on_board}
    spots = ring_positions(list(pts.items()), (px0, py0, px1, py1), 13)
    for p in on_board:
        (x, y), (tx, ty) = pts[p.ref], spots[p.ref]
        s.append(balloon(x, y, tx, ty, p.find))
        s.append(txt(tx + (5 if tx > (px0+px1)/2 else -5), ty + 1, p.ref, 2.2, "sub",
                     "start" if tx > (px0+px1)/2 else "end"))
    s.append(dim_h(px0, px1, py0-26, py0-15, f"{d.pcb_length:g}"))
    s.append(dim_v(py0, py1, px1+30, px1+16, f"{d.pcb_width:g}"))
    s.append(txt(108, py1+30, "01 CARTE TA-MB-01 — FACE COMPOSANTS / 2:1", 3, "label", "middle"))
    s.append(txt(108, py1+35, f"Épaisseur {d.pcb_thickness:g} • 4 encoches R{d.boss_radius+d.pcb_notch_gap:g} aux bossages "
                 f"• face supérieure à Z = {top_z:g}", 2.3, "sub", "middle"))

    under = View(lid, (0, 0, -200), (0, 1, 0), 318, 66, 1.0)
    s.append(under.svg(hidden=False))
    s.append(txt(318, 102, "CAPOT / FACE INTÉRIEURE / 1:1", 3, "label", "middle"))
    s.append(txt(318, 107, f"Ø{d.light_hole_d:g} guide de lumière LP1 • 3 évents Ø{d.vent_d:g} buzzer • zone GNSS sans métal",
                 2.2, "sub", "middle"))

    bt = next(p for p in electronics if p.ref == "BT1")
    lower = View(Compound(children=[base, bt.solid]), (0, 0, 200), (0, 1, 0), 318, 145, 1.0)
    s.append(lower.svg(hidden=False))
    c = lower.point(P(d.battery_x, 0, 7.5))
    s.append(balloon(c[0], c[1], c[0]+26, c[1]+24, bt.find))
    s.append(txt(318, 182, "BASE + BT1 SUR MOUSSE (CARTE RETIRÉE) / 1:1", 3, "label", "middle"))

    rules = ["RÈGLES D'IMPLANTATION",
             "• ANT1 en bord de carte, zone dégagée sans cuivre ni composant (contrôlée).",
             "• ANT2 face au capot polymère ; aucun métal au-dessus.",
             "• U2/U3 près du centre de la carte, fixée par 4 points rigides.",
             "• Batterie sous la carte : vérifier l'accord des antennes.",
             "• J1 et SW1 alignés sur les ouvertures de la paroi -X (contrôlé)."]
    for i, r in enumerate(rules):
        s.append(txt(236, 196 + i*5.6, r, 2.8 if i == 0 else 2.35, "label-bold" if i == 0 else "label"))
    s.append(line(222, 24, 222, 244, "thin"))
    s.append('</svg>')
    return ''.join(s)


EXPLODE = {"base": (0, 0, 0), "BT1": (0, 0, 16), "pcb": (0, 0, 34), "LP1": (0, 0, 52), "LID": (0, 0, 62)}


def exploded(parts, d: Dimensions):
    """Groups lifted along Z: base, battery, populated board, light pipe, lid."""
    base, lid, electronics = parts
    solids, moved = [base, Pos(*EXPLODE["LID"]) * lid], {}
    for p in electronics:
        off = EXPLODE.get(p.ref, EXPLODE.get(p.mount, (0, 0, 0)))
        solids.append(Pos(*off) * p.solid)
        moved[p.ref] = off
    return Compound(children=solids), moved


def view_bbox(view):
    xs, ys = [], []
    for e in view.vis:
        for x, y in polyline(e):
            sx, sy = view.xy(x, y)
            xs.append(sx); ys.append(sy)
    return min(xs), min(ys), max(xs), max(ys)


def sheet_three(parts, d: Dimensions):
    base, lid, electronics = parts
    data = load_netlist()
    s = sheet_start(3, "VUE ÉCLATÉE — TOUS LES COMPOSANTS", "TA-TR-GA-03", "1,45:1 (éclaté)")
    shape, moved = exploded(parts, d)
    iso = View(shape, (125, -140, 120), (0, 0, 1), 125, 142, 1.45, look_at=(0, 0, 40))
    # Assembly axes through the four screw centres, drawn behind the parts.
    for x, y in screw_centers(d):
        (ax, ay), (bx, by) = iso.point(P(x, y, 0)), iso.point(P(x, y, d.height + EXPLODE["LID"][2] + 6))
        s.append(line(ax, ay, bx, by, "center"))
    s.append(iso.svg(hidden=False))
    for wid, (a, b) in wire_routes(electronics).items():
        pa = (Pos(*moved["BT1"]) * Pos(a.X, a.Y, a.Z)).position
        pb = (Pos(*moved["J3"]) * Pos(b.X, b.Y, b.Z)).position
        (x1, y1), (x2, y2) = iso.point(pa), iso.point(pb)
        s.append(f'<path class="wire" d="M{x1:.2f},{y1:.2f} C{x1-12:.2f},{y1:.2f} {x2-12:.2f},{y2:.2f} {x2:.2f},{y2:.2f}"/>')
    # One balloon per item (20 electronic parts, base, lid), spread around the view.
    anchors = {}
    for p in electronics:
        bb = p.solid.bounding_box()
        cx, cy = bb.center().X, bb.center().Y
        z = bb.max.Z
        if p.ref == "PCB1":
            cx, cy, z = 0, -d.pcb_width/2 + 1.5, bb.max.Z
        anchors[p.find] = iso.point((Pos(*moved[p.ref]) * Pos(cx, cy, z)).position)
    bb = base.bounding_box()
    anchors[21] = iso.point(P(bb.max.X - 6, bb.min.Y, 3))
    anchors[22] = iso.point(P(-d.length/2 + 8, -d.width/2, d.height + EXPLODE["LID"][2] - 2))
    spots = ring_positions(list(anchors.items()), view_bbox(iso), 12)
    for n, (x, y) in anchors.items():
        tx, ty = spots[n]
        s.append(balloon(x, y, tx, ty, n))
    s.append(txt(125, 246, "VUE ÉCLATÉE ISOMÉTRIQUE — 22 REPÈRES • AXES DE VISSAGE EN TRAITS MIXTES • W1 CÂBLE BATTERIE EN JAUNE", 2.6, "label", "middle"))

    rows = [["REP", "QTÉ", "DÉSIGNATION", "RÉFÉRENCE", "CONTOUR mm", "DONNÉE"]]
    for c in sorted(data["components"], key=lambda c: c["find"]):
        size = " × ".join(f"{v:g}".replace(".", ",") for v in c["size_mm"][:2])
        rows.append([str(c["find"]), "1", f'{c["ref"]} {c["name"]}', c["part"], size, c["size_status"]])
    rows += [["21", "1", "Base, oreilles de sangle", "TA-TR-GA-01", f"{d.length+2*d.ear_length:g} × {d.width:g}", "modèle CAO"],
             ["22", "1", "Capot (polymère non métallique)", "TA-TR-GA-02", f"{d.length:g} × {d.width:g}", "modèle CAO"],
             ["23", "4", "Vis auto-taraudeuse plastique", "à choisir", f"Ø{d.screw_diameter:g}", "à définir"],
             ["24", "1", "Mousse adhésive batterie", "à choisir", "62 × 34 × 0,5", "à définir"],
             ["25", "1", "Joint + sangle textile 25 mm", "à choisir", "—", "à définir"]]
    tx0 = 252
    s.append(txt(tx0, 34, "NOMENCLATURE", 3.2, "label-bold"))
    s.append(table(tx0, 37, [7, 6, 52, 30, 20, 43], rows, 4.75, 1.9, 1.7))
    ty = 37 + 4.75*len(rows) + 4
    s.append(txt(tx0, ty, "Sources : hardware/trace-v2/netlist.json • « gabarit indicatif » : cote à relever sur la pièce choisie.", 1.9, "sub"))
    s.append(txt(tx0, ty + 9, "ENSEMBLE MONTÉ", 3, "label-bold"))
    whole = View(assembly(parts), (125, -140, 120), (0, 0, 1), tx0 + 40, ty + 44, 0.85, look_at=(0, 0, 10))
    s.append(whole.svg(hidden=False))
    facts = ["86 × 58 × 20 mm (106 mm avec oreilles)", "20 composants + boîtier, 1 seul câble", "LTE-M / NB-IoT + GNSS dans un SiP 12 × 11 mm",
             "Choc ±200 g • inclinaison • journal en flash"]
    for i, f in enumerate(facts):
        s.append(txt(tx0 + 92, ty + 30 + i*7, "• " + f, 2.1, "label"))
    s.append('</svg>')
    return ''.join(s)


def block(x, y, w, h, title, subtitle=""):
    out = rect(x, y, w, h, "frame") + rect(x, y, w, 5, "head") + txt(x + w/2, y + 3.7, title, 2.4, "label-bold", "middle")
    if subtitle:
        out += txt(x + w/2, y + 9, subtitle, 2.0, "sub", "middle")
    return out


def link(points, label=None, at=0, cls="wire", dx=1, dy=-1):
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)
    out = f'<path class="{cls}" d="{d}"/>'
    if label:
        x, y = points[at]
        out += txt(x + dx, y + dy, label, 2.0, "accent")
    return out


def sheet_four(parts, d: Dimensions):
    data = load_netlist()
    s = sheet_start(4, "ARCHITECTURE ÉLECTRIQUE", "TA-TR-EL-04", "schéma NTS")
    s.append(txt(16, 32, "SCHÉMA FONCTIONNEL — DEPUIS hardware/trace-v2/netlist.json", 3, "label-bold"))
    # Power path (left), processor (centre), radio and SIM (right), sensors and storage (below).
    s.append(block(16, 46, 30, 18, "J1 USB-C", "VBUS 5 V, charge"))
    s.append(block(16, 82, 30, 22, "BT1 Li-Po 1S", "1200 mAh • J3 / W1"))
    s.append(block(66, 46, 40, 58, "U4 nPM1300", "PMIC"))
    for i, t in enumerate(["chargeur 32–800 mA", "jauge (SoC)", "BUCK1 → 1,8 V", "VSYS → nRF9151", "LED0 (sink)", "I²C + GPIO0 IRQ"]):
        s.append(txt(68, 60 + i*6.6, t, 2.1, "label"))
    s.append(block(140, 46, 50, 92, "U1 nRF9151", "LTE-M / NB-IoT + GNSS"))
    for i, t in enumerate(["VDD ← VSYS", "VDD_GPIO ← 1,8 V", "SPI : SCK MOSI MISO", "CS0 → U2  CS1 → U5",
                           "TWI ← U3, U4", "INT1 ← U2  INT2 ← U3", "INT3 ← U4", "BTN ← SW1  BUZ → Q1",
                           "ANT → ANT1", "GPS ← U6", "SIM ↔ J2", "SWD ↔ J4"]):
        s.append(txt(142, 60 + i*6.2, t, 2.1, "label"))
    s.append(block(216, 46, 36, 14, "ANT1 NN02-224", "antenne LTE"))
    s.append(block(216, 68, 16, 14, "U6", "filtre+LNA"))
    s.append(block(238, 68, 22, 14, "ANT2", "patch GNSS"))
    s.append(block(216, 90, 36, 14, "J2 eSIM MFF2", "soudée"))
    s.append(block(216, 112, 36, 14, "J4 SWD", "Tag-Connect"))
    s.append(block(66, 120, 40, 16, "U3 ADXL367", "inclinaison • I²C"))
    s.append(block(66, 146, 40, 16, "U2 ADXL372", "choc ±200 g • SPI"))
    s.append(block(66, 172, 40, 16, "U5 MX25R6435F", "journal 64 Mb • SPI"))
    s.append(block(140, 154, 22, 14, "SW1", "bouton"))
    s.append(block(168, 154, 30, 20, "Q1 + D2 + BZ1", "buzzer"))
    s.append(block(16, 120, 30, 14, "D1 LED", "+ LP1"))
    def dot(x, y):
        return f'<circle cx="{x:.2f}" cy="{y:.2f}" r=".7" class="pin"/>'
    # Power.
    s += [link([(46, 55), (66, 55)], "VBUS", 0, dy=-1.2), link([(46, 93), (66, 93)], "VBAT", 0, dy=-1.2),
          link([(106, 52), (140, 52)], "VSYS", 0, dy=-1.2),
          link([(100, 46), (100, 40), (183, 40), (183, 154)], "VSYS → BZ1", 2, dx=1.2, dy=6), dot(100, 46),
          link([(86, 104), (86, 112), (31, 112), (31, 120)], "LED0", 1, dy=-1.2)]
    # One vertical channel per bus: V1V8 x=110, I²C x=116, SPI x=122, INT x=128.
    channels = {
        "V1V8": (110, [(60, 140), (127, 106), (153, 106), (179, 106)]),
        "I²C": (116, [(84, 140), (84, 106), (130.5, 106)]),
        "SPI": (122, [(72, 140), (157, 106), (184, 106)]),
        "INT": (128, [(96, 140), (90, 106), (134, 106), (160, 106)]),
    }
    for name, (cx, taps) in channels.items():
        ys = [y for y, _ in taps]
        s.append(link([(cx, min(ys)), (cx, max(ys))]))
        s.append(txt(cx, min(ys) - 1.5 - (2.8 if name in ("I²C", "INT") else 0), name, 2.0, "accent", "middle"))
        for y, x in taps:
            s.append(link([(x, y), (cx, y)]) + dot(cx, y))
    s += [link([(106, 60), (110, 60)]),
          link([(151, 154), (151, 138)], "BTN", 0, dx=1.2, dy=-3), link([(176, 154), (176, 138)], "BUZ", 0, dx=1.2, dy=-3)]
    # Radio and service links.
    s += [link([(190, 53), (216, 53)], "RF_LTE", 0, "wire-rf", dy=-1.2),
          link([(190, 75), (216, 75)], "GNSS", 0, "wire-rf", dy=-1.2),
          link([(232, 75), (238, 75)], None, 0, "wire-rf"),
          link([(190, 97), (216, 97)], "SIM ×4", 0, dy=-1.2),
          link([(190, 119), (216, 119)], "SWD", 0, dy=-1.2)]
    s.append(txt(16, 200, "Lignes jaunes pleines : signaux et alimentations • pointillés : RF 50 Ω.", 2.2, "sub"))
    s.append(txt(16, 205, "Un seul câble dans l'appareil : W1 (BT1 → J3). Tout le reste est routé sur la carte.", 2.2, "sub"))

    rails = [["RAIL", "SOURCE", "TENSION", "CONSOMMATEURS"]]
    loads = {"VBUS": "U4", "VBAT": "U4", "VSYS": "U1 VDD, BZ1, D1", "V1V8": "U1 GPIO, U2, U3, U5, U6, J4"}
    for name, r in data["rails"].items():
        volt = f'{r["min_v"]:g} V' if r["min_v"] == r["max_v"] else f'{r["min_v"]:g}–{r["max_v"]:g} V'
        rails.append([name, r["source"], volt, loads[name]])
    s.append(txt(272, 34, "RAILS (PLAGES CONTRÔLÉES)", 3, "label-bold"))
    s.append(table(272, 37, [14, 38, 18, 64], rails, 5, 2.0, 1.9))
    buses = [["BUS", "MEMBRES", "SÉLECTION / ADRESSE"],
             ["SPI", "U2 ADXL372, U5 flash", "CS_IMPACT, CS_FLASH"],
             ["I²C", "U3 ADXL367, U4 nPM1300", "0x1D, 0x6B (à confirmer)"],
             ["RF", "U1 → ANT1 ; ANT2 → U6 → U1", "50 Ω, adaptation à régler"]]
    s.append(txt(272, 72, "BUS", 3, "label-bold"))
    s.append(table(272, 75, [14, 60, 60], buses, 5, 2.0, 1.9))
    s.append(txt(272, 104, "CÂBLE", 3, "label-bold"))
    w = data["wires"][0]
    s.append(table(272, 107, [10, 22, 66, 14, 22], [["FIL", "DE → À", "CONNECTIQUE", "L mm", "SIGNAUX"],
                                                    [w["id"], f'{w["from"]} → {w["to"]}', w["connector"], str(w["length_mm"]),
                                                     " ".join(w["signals"])]], 5, 2.0, 1.9))
    s.append(txt(272, 126, "POINTS FIRMWARE À FIGER", 3, "label-bold"))
    for i, n in enumerate(data["firmware_notes"]):
        s.append(txt(272, 132 + i*5.2, f"• {n}", 2.0, "label"))
    s.append(txt(272, 152, "POURQUOI CETTE ARCHITECTURE", 3, "label-bold"))
    why = ["• Modem LTE-M/NB-IoT et GNSS dans un seul SiP 12 × 11 mm.",
           "• ADXL372 conçu pour la détection d'impacts d'actifs en transit :",
           "   veille active 1,4 µA, capture du pic au-dessus du seuil.",
           "• ADXL367 : inclinaison et réveil sur mouvement à 180 nA.",
           "• nPM1300 : charge USB-C, jauge et rails en une puce.",
           "• Journal en flash : rien n'est perdu sans réseau.",
           "• eSIM soudée : aucune carte qui se déloge lors d'un choc."]
    for i, n in enumerate(why):
        s.append(txt(272, 158 + i*5.2, n, 2.1, "label"))
    s.append('</svg>')
    return ''.join(s)


def publish(svgs):
    """Copy the sheets where the README and dashboard link to them."""
    pdf = REPO / "documentation" / "tiltalert-trace-plans-A3.pdf"
    subprocess.run(['rsvg-convert', '-f', 'pdf', '-o', str(pdf)] + [str(p) for p in svgs], check=True)
    shutil.copy(pdf, REPO / "web" / "public" / "assets" / pdf.name)
    shutil.copy(svgs[0], REPO / "documentation" / "tiltalert-trace-blueprint.svg")
    shutil.copy(svgs[2], REPO / "documentation" / "tiltalert-trace-exploded.svg")
    shutil.copy(svgs[0], REPO / "web" / "public" / "assets" / "tiltalert-trace-blueprint.svg")
    shutil.copy(svgs[2], REPO / "web" / "public" / "assets" / "tiltalert-trace-parts.svg")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='validate geometry only')
    args=parser.parse_args()
    parts=make_parts()
    check(parts)
    if args.check:
        print('Geometry checks passed')
        return
    OUT.mkdir(exist_ok=True)
    base,lid,_=parts
    for name,part in [('base',base),('lid',lid)]:
        export_step(part,OUT/f'tiltalert-trace-{name}.step')
        export_stl(part,OUT/f'tiltalert-trace-{name}.stl')
    export_step(assembly(parts), OUT/'tiltalert-trace-assembly.step')
    svgs=[]
    for number,fn in [(1,sheet_one),(2,sheet_two),(3,sheet_three),(4,sheet_four)]:
        svg=OUT/f'tiltalert-trace-sheet-{number}.svg'
        svg.write_text(fn(parts,D),encoding='utf-8')
        subprocess.run(['rsvg-convert','-f','pdf','-o',str(svg.with_suffix('.pdf')),str(svg)],check=True)
        subprocess.run(['rsvg-convert','-f','png','-w','2200','-o',str(svg.with_suffix('.png')),str(svg)],check=True)
        svgs.append(svg)
    publish(svgs)
    print(f'Generated CAD and drawing exports in {OUT}')


if __name__=='__main__':
    main()
