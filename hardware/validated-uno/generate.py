#!/usr/bin/env python3
"""Generate and validate the corrected TiltAlert Uno electrical blueprint."""

import html
import json
import shutil
import subprocess
from pathlib import Path

import physical

HERE = Path(__file__).resolve().parent
NETLIST = HERE / "netlist.json"
SVG = HERE / "tiltalert-uno-electrical.svg"
PHYS = HERE / "tiltalert-uno-physical.svg"
PDF = HERE / "tiltalert-uno-electrical.pdf"
BOM = HERE / "BOM.md"


def validate(data):
    refs = {c["ref"] for c in data["components"]}
    assert len(refs) == len(data["components"]), "Duplicate component reference"
    nets = {n["name"]: set(n["terminals"]) for n in data["nets"]}
    assert len(nets) == len(data["nets"]), "Duplicate net name"
    expected = {
        "+5V": {"U1.5V", "S1.1", "BZ1.VCC"},
        "GND": {"U1.GND", "R1.2", "S2.2", "D1.K", "BZ1.GND"},
        "TILT_D2": {"U1.D2", "S1.2", "R1.1"},
        "RESET_D12": {"U1.D12", "S2.1"},
        "ALARM_D13": {"U1.D13", "R2.1"},
        "LED_A": {"R2.2", "D1.A"},
        "BUZZ_D3": {"U1.D3", "BZ1.SIG"},
    }
    assert nets == expected, "Circuit does not match the reviewed Uno topology"
    terminals = [t for net in data["nets"] for t in net["terminals"]]
    assert len(terminals) == len(set(terminals)), "One terminal is assigned to multiple nets"
    assert all(t.split(".")[0] in refs for t in terminals), "Unknown component reference"
    assert "U1.5V" not in nets["GND"] and "U1.GND" not in nets["+5V"], "Direct supply short"
    assert next(c for c in data["components"] if c["ref"] == "BZ1")["type"] == "Buzzer actif 5 V"
    return nets


def esc(value):
    return html.escape(str(value), quote=True)


def line(x1, y1, x2, y2, cls="wire"):
    return f'<path class="{cls}" d="M{x1} {y1} L{x2} {y2}"/>'


def path(d, cls="wire"):
    return f'<path class="{cls}" d="{d}"/>'


def text(x, y, value, cls="label", anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text class="{cls}" x="{x}" y="{y}"{a}>{esc(value)}</text>'


def dot(x, y):
    return f'<circle class="junction" cx="{x}" cy="{y}" r="5"/>'


def box(x, y, w, h, cls="box"):
    return f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}"/>'


def terminal(x, y, net):
    return dot(x, y) + text(x + 11, y - 9, net, "net")



STYLE = """<defs><pattern id="minor" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="#ffffff" stroke-opacity=".075" stroke-width="1"/></pattern><pattern id="major" width="100" height="100" patternUnits="userSpaceOnUse"><rect width="100" height="100" fill="url(#minor)"/><path d="M100 0H0V100" fill="none" stroke="#ffffff" stroke-opacity=".13" stroke-width="1"/></pattern></defs>
<style>
.border,.box,.wire,.symbol,.dim{fill:none;stroke:#f5fbff;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}.border{stroke-width:3}.wire{stroke-width:3}.symbol{stroke-width:2.6}.thin{fill:none;stroke:#cfe6f6;stroke-width:1.2}.dash{fill:none;stroke:#f5fbff;stroke-width:2;stroke-dasharray:9 7}.junction{fill:#f5fbff}.label{font:20px Arial,sans-serif;fill:#f5fbff}.small{font:16px Arial,sans-serif;fill:#d5e7f8}.tiny{font:13px Arial,sans-serif;fill:#c4ddef}.title{font:bold 45px Arial,sans-serif;fill:white;letter-spacing:2px}.section{font:bold 23px Arial,sans-serif;fill:white;letter-spacing:1px}.ref{font:bold 22px Arial,sans-serif;fill:white}.net{font:bold 17px Arial,sans-serif;fill:#f5fbff}.netw{font:bold 15px Arial,sans-serif;fill:#ffe463}.pin{font:18px Consolas,monospace;fill:white}.pins{font:11px Consolas,monospace;fill:#c4ddef}.pinb{font:bold 12px Consolas,monospace;fill:#ffe463}.accent{fill:#ffe463;stroke:#ffe463}.pad{fill:none;stroke:#f5fbff;stroke-width:1.2}.hole{fill:none;stroke:#9fc6e2;stroke-width:1}.part{fill:#0b4a80;stroke:#f5fbff;stroke-width:2.2}.jumper{fill:none;stroke:#ffe463;stroke-width:3;stroke-linejoin:round;stroke-linecap:round}
</style>"""


def sheet_header(title, rev, subtitle):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 1600 1131" role="img" aria-label="TiltAlert Uno">\n'
            + STYLE + '\n<rect width="1600" height="1131" fill="#07345e"/><rect width="1600" height="1131" fill="url(#major)"/>\n'
            + '<rect class="border" x="28" y="28" width="1544" height="1075"/><path class="border" d="M28 131H1572M28 889H1572"/>\n'
            + text(65, 89, title, "title") + text(1535, 84, rev, "section", "end") + text(1535, 111, subtitle, "small", "end"))


def sheet_footer(notes, document, subtitle):
    p = [text(60, 928 + 28 * i, n, "small") for i, n in enumerate(notes)]
    p += [text(60, 1008, "TILTALERT", "section"), text(60, 1038, subtitle, "small"),
          text(60, 1070, "Échelle : schématique (NTS)  •  A3 paysage  •  Unités : V / Ω", "tiny"),
          box(1030, 982, 500, 97), line(1220, 982, 1220, 1079), line(1370, 982, 1370, 1079),
          text(1050, 1010, "DOCUMENT", "tiny"), text(1050, 1047, document, "ref"),
          text(1240, 1010, "RÉVISION", "tiny"), text(1240, 1047, "A", "ref"),
          text(1390, 1010, "FORMAT", "tiny"), text(1390, 1047, "A3 / NTS", "ref"), "</svg>"]
    return "\n".join(p)


def build_svg(data):
    comp = {c["ref"]: c for c in data["components"]}
    p = []
    p.append(sheet_header("TILTALERT / SCHÉMA ÉLECTRIQUE", "UNO · REV A", "Prototype 5 V USB  •  contact + alarme"))

    # Section frames. Every line ends at a junction or named Uno pin.
    p += [box(65, 165, 1455, 690),
          text(95, 206, "01  ENTRÉE INCLINAISON", "section"),
          text(95, 543, "02  ACQUITTEMENT", "section"),
          text(1065, 206, "03  SORTIES D'ALARME", "section")]
    # Controller U1 with labelled pads.
    p += [box(615, 276, 365, 440), text(797, 319, "U1", "ref", "middle"),
          text(797, 350, comp["U1"]["type"], "label", "middle"),
          line(615, 384, 980, 384, "dash")]
    for y, pin, side in [(415, "5V", "left"), (477, "D2", "left"), (625, "D12", "left"),
                         (445, "D13", "right"), (540, "D3", "right"), (685, "GND", "right")]:
        x = 615 if side == "left" else 980
        p += [f'<circle class="symbol" cx="{x}" cy="{y}" r="6"/>',
              text(x + (23 if side == "left" else -23), y + 7, pin, "pin", "start" if side == "left" else "end")]

    # +5V sensor feed, contact switch, and D2 pulldown.
    p += [path("M615 415 H500 V315 H230 V368"), terminal(230, 315, "+5V"),
          text(110, 362, "S1", "ref"), text(110, 390, "KY-020 / contact NO", "small"),
          line(210, 369, 255, 369), dot(230, 369),
          line(255, 369, 300, 400, "symbol"),
          line(310, 425, 360, 425), dot(310, 425),
          path("M360 425 H475 V477 H615"),
          text(372, 414, "TILT_D2", "net"),
          path("M475 477 V498"),
          path("M475 498 l-15 10 30 14 -30 14 30 14 -30 14 15 10" , "symbol"),
          path("M475 574 V585 M456 585 H494 M463 594 H487 M469 603 H481", "symbol"),
          text(500, 535, "R1", "ref"), text(500, 563, comp["R1"]["value"], "small"),
          text(504, 596, "GND", "tiny")]
    # Switch intended terminals: left contact +5 at x230; right side from x310 to D2.
    p += [text(100, 250, "Fermé → D2 = HIGH", "small"),
          text(100, 274, "Ouvert → R1 tire D2 à LOW", "small")]

    # Reset button to ground, with internal pullup note.
    p += [path("M615 625 H490 V638 H300"),
          line(300, 613, 300, 660, "symbol"), line(300, 675, 300, 794),
          line(273, 660, 327, 660, "symbol"),
          text(110, 619, "S2", "ref"), text(110, 647, "Bouton NO", "small"),
          text(110, 683, "Appuyé → D12 = LOW", "small"),
          text(110, 708, "INPUT_PULLUP interne", "small"),
          text(322, 630, "RESET_D12", "net")]

    # D13 to resistor and external LED to ground.
    p += [path("M980 445 H1103"),
          path("M1103 445 l14 -14 18 28 18 -28 18 28 18 -28 14 14", "symbol"),
          line(1203, 445, 1252, 445),
          path("M1252 417 V473 M1252 445 H1294 M1294 417 V473 M1294 445 H1375 V794", "symbol"),
          path("M1297 399 l24 -19 M1321 380 l-3 16 M1321 380 l-17 5 M1315 410 l24 -19 M1339 391 l-3 16 M1339 391 l-17 5", "symbol"),
          text(1110, 405, "R2  " + comp["R2"]["value"], "ref"),
          text(1232, 360, "D1  LED rouge", "ref"),
          text(1000, 468, "ALARM_D13", "net"),
          text(1218, 490, "A", "pin"), text(1294, 490, "K", "pin")]

    # Active 3-pin buzzer. Supply and ground wires are separated and named.
    p += [path("M980 540 H1050 V642 H1115"), box(1115, 580, 212, 135),
          text(1180, 628, "BZ1", "ref"),
          text(1170, 658, "BUZZER ACTIF", "small"),
          text(1124, 668, "SIG", "tiny"),
          text(1000, 528, "BUZZ_D3", "net"),
          path("M1205 580 V556"),
          path("M1265 715 V794"),
          text(1195, 577, "+", "pin"), text(1255, 738, "−", "pin"),
          text(1217, 558, "+5V", "net"), dot(1205, 556),
          text(1124, 690, "Module actif, entrée SIG", "tiny"), text(1124, 706, "courant de commande faible", "tiny")]

    # Ground bus and named ground symbol. No +5V connection to this bus.
    p += [path("M300 794 H1450"), dot(1265, 794), dot(1375, 794),
          path("M980 685 H1015 V794"), dot(1015, 794),
          path("M1450 794 V811 M1428 811 H1472 M1437 820 H1463 M1444 829 H1456", "symbol"),
          text(1450, 782, "GND", "net", "end")]

    p.append(sheet_footer([
        "NETLISTE VALIDÉE PAR SCRIPT · +5V ET GND SÉPARÉS · BROCHES D2 / D12 / D13 / D3 SELON LE SKETCH",
        "S1 est un contact simulé, pas une mesure de choc; le buzzer doit être ACTIF. Alimenter l'Uno par USB 5 V.",
    ], "TA-EL-001", "SCHÉMA ÉLECTRIQUE — PROTOTYPE ARDUINO UNO"))
    return "\n".join(p)


def build_bom(data):
    rows = ["# Nomenclature — TiltAlert Uno corrigé", "", "| Réf. | Composant | Quantité / valeur | Note |", "|---|---|---|---|"]
    rows += [f"| {c['ref']} | {c['type']} | {c['value']} | {c['note']} |" for c in data["components"]]
    rows += ["", "Ajouter une breadboard, des fils de liaison et un câble USB pour le montage d'essai.",
             "Le buzzer actif doit accepter un signal logique de 5 V et présenter une entrée de commande à faible courant.",
             "La valeur de 220 Ω donne environ 10–15 mA pour une LED rouge typique; vérifier la LED et la limite de la broche.", ""]
    return "\n".join(rows)


def main():
    data = json.loads(NETLIST.read_text(encoding="utf-8"))
    nets = validate(data)
    SVG.write_text(build_svg(data), encoding="utf-8")
    BOM.write_text(build_bom(data), encoding="utf-8")
    converter = shutil.which("rsvg-convert")
    if not converter:
        raise SystemExit("rsvg-convert is needed to build the A3 PDF")
    physical.validate_layout(nets)
    PHYS.write_text(physical.build_physical_svg(data, sheet_header, sheet_footer), encoding="utf-8")
    subprocess.run([converter, "-f", "pdf", "-o", str(PDF), str(SVG), str(PHYS)], check=True)
    for svg in (SVG, PHYS):
        subprocess.run([converter, "-w", "2200", "-o", str(svg.with_suffix(".png")), str(svg)], check=True)
    print(f"Validated {len(nets)} nets and the breadboard layout; generated {SVG.name}, {PHYS.name}, {PDF.name}, {BOM.name}")


if __name__ == "__main__":
    main()
