"""Shared A3 blueprint frame and drafting primitives for TiltAlert drawings."""

from html import escape


def txt(x, y, value, size=3, cls="label", anchor="start"):
    return f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" font-size="{size}" text-anchor="{anchor}">{escape(str(value))}</text>'


def line(x1,y1,x2,y2,cls="thin"):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" class="{cls}"/>'


def rect(x, y, w, h, cls="frame"):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" class="{cls}"/>'


def dim_h(x1,x2,y,ey,label):
    return (line(x1,ey,x1,y-2,"extension") + line(x2,ey,x2,y-2,"extension") +
            line(x1,y,x2,y,"dimension") +
            f'<path class="arrow" d="M{x1:.2f},{y:.2f} l3,-1 l0,2 z M{x2:.2f},{y:.2f} l-3,-1 l0,2 z"/>'+
            txt((x1+x2)/2,y-1.7,label,2.8,"dimension-text","middle"))


def dim_v(y1,y2,x,ex,label):
    mid=(y1+y2)/2
    return (line(ex,y1,x+2,y1,"extension")+line(ex,y2,x+2,y2,"extension")+
            line(x,y1,x,y2,"dimension")+
            f'<path class="arrow" d="M{x:.2f},{y1:.2f} l-1,3 l2,0 z M{x:.2f},{y2:.2f} l-1,-3 l2,0 z"/>'+
            f'<text x="{x-2:.2f}" y="{mid:.2f}" transform="rotate(-90 {x-2:.2f} {mid:.2f})" class="dimension-text" font-size="2.8" text-anchor="middle">{escape(str(label))}</text>')


def balloon(x, y, tx, ty, number):
    """Find-number balloon at (tx,ty) with a leader ending on a dot at (x,y)."""
    return (line(x, y, tx, ty, "leader") + f'<circle cx="{x:.2f}" cy="{y:.2f}" r=".7" class="dot"/>' +
            f'<circle cx="{tx:.2f}" cy="{ty:.2f}" r="3.6" class="balloon"/>' +
            txt(tx, ty+1.15, number, 3.2, "label-bold", "middle"))


def table(x, y, widths, rows, row_h=5.2, header_size=2.3, size=2.15):
    out = [rect(x, y, sum(widths), row_h*len(rows), "frame")]
    for r, row in enumerate(rows):
        yy = y + r*row_h
        if r:
            out.append(line(x, yy, x+sum(widths), yy, "grid-line"))
        else:
            out.append(rect(x, yy, sum(widths), row_h, "head"))
        xx = x
        for c, (w, cell) in enumerate(zip(widths, row)):
            if c:
                out.append(line(xx, y, xx, y+row_h*len(rows), "grid-line"))
            out.append(txt(xx+1.4, yy+row_h*0.68, cell, header_size if r == 0 else size,
                           "label-bold" if r == 0 else "label"))
            xx += w
    return "".join(out)


STYLE = '''<style>
  .object{fill:none;stroke:#f8fcff;stroke-width:.34;stroke-linecap:round;stroke-linejoin:round}
  .hidden{fill:none;stroke:#bad9eb;stroke-width:.16;stroke-dasharray:1.5 1.2}
  .thin,.extension{fill:none;stroke:#d5ebfa;stroke-width:.16}
  .leader{stroke:#f8fcff;stroke-width:.2}
  .dot{fill:#f8fcff}
  .balloon{fill:#0b4a80;stroke:#f8fcff;stroke-width:.3}
  .dimension{stroke:#f2faff;stroke-width:.16} .dimension-text{font-family:Arial,sans-serif;fill:#f8fcff}
  .arrow{fill:#f8fcff} .label{font-family:Arial,sans-serif;fill:#fff}
  .label-bold{font-family:Arial,sans-serif;fill:#fff;font-weight:700}
  .sub{font-family:Arial,sans-serif;fill:#d2e7f5}
  .accent{font-family:Arial,sans-serif;fill:#f3cf29;font-weight:700}
  .center{stroke:#afcfdf;stroke-width:.15;stroke-dasharray:5 1 1 1}
  .cut{stroke:#fff;stroke-width:.42;stroke-dasharray:8 1 2 1}
  .frame{fill:none;stroke:#eff9ff;stroke-width:.3}
  .border{fill:none;stroke:#eff9ff;stroke-width:.5}
  .grid-line{stroke:#cfe6f6;stroke-width:.15}
  .head{fill:#103e6a;stroke:#eff9ff;stroke-width:.3}
  .wire{fill:none;stroke:#f3cf29;stroke-width:.45;stroke-linecap:round;stroke-linejoin:round}
  .wire-rf{fill:none;stroke:#f3cf29;stroke-width:.45;stroke-dasharray:2 .8}
  .pin{fill:#f8fcff}
</style>'''


CAD_NOTES = ["1. Cotes en mm. Projection 3e dièdre. Tolérances générales à définir (proposé ISO 2768-m).",
             "2. Contours des cartes : données fabricant/distributeur citées dans hardware/trace-v2/netlist.json.",
             "3. Hauteurs de composants, connecteurs et positions de prises : gabarits indicatifs à mesurer.",
             "4. Géométrie et plans générés par cad/generate.py (build123d 0.13.0) ; contrôles --check."]


def sheet_start(number, title, docno, scale_note="1:1 sauf indication", total=4, date="2026-10-03",
                subtitle="TiltAlert V2 — balise de suivi de chocs, carte TA-MB-01 (nRF9151)",
                revision="Carte nRF9151 + boîtier 86 × 58", notes=CAD_NOTES, material="à définir"):
    """A3 frame: zone border A–F / 1–8, revision block and title block."""
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">', STYLE,
         '''<defs>
  <pattern id="grid-small" width="5" height="5" patternUnits="userSpaceOnUse"><path d="M5 0H0V5" fill="none" stroke="#7bb2d4" stroke-width=".09" opacity=".28"/></pattern>
  <pattern id="grid-large" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" fill="none" stroke="#b9daf0" stroke-width=".16" opacity=".30"/></pattern>
  <pattern id="hatch" width="2.6" height="2.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0 V2.6" stroke="#bedff1" stroke-width=".18"/></pattern>
  <pattern id="hatch2" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><path d="M0 0 V1.6" stroke="#f3cf29" stroke-width=".16"/></pattern>
</defs>
<rect width="420" height="297" fill="#0b4a80"/>
<rect width="420" height="297" fill="url(#grid-small)"/>
<rect width="420" height="297" fill="url(#grid-large)"/>''']
    # Zone border, as on a defence-style drawing frame.
    s.append(rect(5, 5, 410, 287, "border"))
    s.append(rect(10, 10, 400, 277, "border"))
    cols, rows = 8, 6
    for i in range(cols):
        x0 = 10 + 400*i/cols
        if i:
            s.append(line(x0, 5, x0, 10, "frame") + line(x0, 287, x0, 292, "frame"))
        for yy in (8.9, 290.9):
            s.append(txt(x0 + 25, yy, i+1, 2.6, "label", "middle"))
    for j in range(rows):
        y0 = 10 + 277*j/rows
        if j:
            s.append(line(5, y0, 10, y0, "frame") + line(410, y0, 415, y0, "frame"))
        for xx in (7.5, 412.5):
            s.append(txt(xx, y0 + 277/rows/2 + 1, "ABCDEF"[j], 2.6, "label", "middle"))
    # Header band.
    s.append(rect(10, 10, 400, 8, "head"))
    s.append('<path d="M10 18 H410" stroke="#f3cf29" stroke-width=".6"/>')
    s.append(txt(14, 15.6, "TILTALERT / TRACE", 3.6, "label-bold"))
    s.append(txt(80, 15.6, "ÉTUDE CONCEPTUELLE — COTES PROVISOIRES — NE PAS FABRIQUER SANS REVUE", 2.5, "accent"))
    # Revision block, top right.
    s.append(table(318, 21, [10, 52, 22], [["RÉV", "DESCRIPTION", "DATE"],
                                          ["0", revision, date]], 4.6, 2.2, 2.1))
    # Title block, bottom right; notes zone bottom left.
    tb = 250
    s.append(f'<path d="M10 {tb} H410 M232 {tb} V287 M232 {tb+13} H410 M232 {tb+25} H410 '
             f'M292 {tb+13} V287 M342 {tb+13} V287 M372 {tb+13} V287" class="border"/>')
    s.append(txt(14, tb+6, "NOTES GÉNÉRALES", 2.8, "label-bold"))
    for i, n in enumerate(notes):
        s.append(txt(14, tb+12+i*5.6, n, 2.35, "sub"))
    s.append(txt(236, tb+6.5, title, 4, "label-bold"))
    s.append(txt(236, tb+11, subtitle, 2.4, "sub"))
    cells = [(236, "N° PLAN", docno), (296, "ÉCHELLE", scale_note), (346, "RÉV", "0"), (376, "FEUILLE", f"{number} / {total}")]
    for x, k, v in cells:
        s.append(txt(x, tb+17, k, 2, "sub"))
        s.append(txt(x, tb+22.4, v, 2.8, "label-bold"))
    s.append(txt(236, tb+29.5, "DESSINÉ : M. ABAAQIL", 2.2, "sub"))
    s.append(txt(296, tb+29.5, f"DATE : {date}", 2.2, "sub"))
    s.append(txt(346, tb+29.5, f"MATIÈRE : {material}", 2.2, "sub"))
    return s



