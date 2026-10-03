#!/usr/bin/env python3
"""A3 blueprint of the TiltAlert dashboard (web/), drawn in the CAD frame.

Zones mirror the sections built by web/src/main.js and the sizes set in
web/src/style.css (desktop layout, 1440 px wide).  Run from the repository:
    python3 documentation/interface/generate.py
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "cad"))
from drafting import balloon, line, rect, sheet_start, table, txt  # noqa: E402

OUT = REPO / "documentation" / "tiltalert-interface-blueprint.svg"
K = 0.148          # mm per CSS pixel
X0, Y0 = 18, 28    # sheet origin of the 1440 px viewport


def px(x, y):
    return X0 + x * K, Y0 + y * K


def box(x, y, w, h, cls="frame"):
    sx, sy = px(x, y)
    return rect(sx, sy, w * K, h * K, cls)


def label(x, y, value, size=2.0, cls="sub", anchor="start"):
    sx, sy = px(x, y)
    return txt(sx, sy, value, size, cls, anchor)


def bars(x, y, widths, gap=16):
    """Placeholder text lines."""
    return "".join(line(*px(x, y + i * gap), *px(x + w, y + i * gap), "thin") for i, w in enumerate(widths))


def wireframe():
    s = [box(0, 0, 1440, 1460, "border")]
    # 1 Sidebar.
    s += [box(0, 0, 256, 1460), box(28, 28, 190, 40), label(40, 54, "LOGO TILTALERT", 1.8),
          label(28, 108, "ESPACE DE TRAVAIL", 1.6)]
    for i, name in enumerate(["Vue d'ensemble", "Carte du trajet", "Incidents", "Le produit"]):
        s += [box(16, 128 + i * 50, 224, 42, "frame" if i else "head"), label(52, 154 + i * 50, name, 1.8, "label")]
    s += [box(16, 620, 224, 54), label(30, 652, "● TILT-001  balise de démonstration", 1.7, "label")]
    # 2 Top bar, 3 page head, 4 notice.
    s += [box(256, 0, 1184, 72), label(298, 42, "WORKSPACE / MONITORING / VUE D'ENSEMBLE", 1.7),
          box(1150, 22, 170, 28), label(1162, 41, "● MODE DÉMONSTRATION", 1.6, "accent"),
          box(1340, 20, 34, 32), label(1349, 42, "⇪", 2.2, "label")]
    s += [label(298, 118, "MISSION CONTROL / 01", 1.6), label(298, 168, "LA VÉRITÉ DU TRAJET.", 4.2, "label-bold"),
          bars(298, 192, [380]), box(1190, 150, 208, 44, "head"), label(1206, 177, "⇩ EXPORTER LE RAPPORT", 1.7, "label-bold")]
    s += [box(298, 214, 1100, 40), label(316, 239, "ⓘ  Scénario simulé — valeurs, événements et positions de démonstration", 1.7)]
    # 5 Mission card.
    s += [box(298, 268, 1100, 182, "head"), label(322, 300, "DOSSIER TRAJET • TA-2048", 1.6, "accent"),
          label(322, 340, "Transport optique de précision", 3.0, "label-bold"), bars(322, 366, [300]),
          label(322, 420, "PARIS", 1.8, "label"), line(*px(390, 415), *px(640, 415), "wire"), label(650, 420, "LYON", 1.8, "label"),
          line(*px(1078, 268), *px(1078, 450), "frame")]
    for i, k in enumerate(["STATUT", "DATE", "BALISE", "DERNIER FIX GNSS"]):
        s += [label(1096, 300 + i * 38, k, 1.5), bars(1096, 314 + i * 38, [220])]
    # 6 Stats.
    for i, k in enumerate(["ÉVÉNEMENTS 05", "CRITIQUES 01", "LOCALISÉS 3/5", "BATTERIE —"]):
        x = 298 + i * 279
        s += [box(x, 468, 264, 104), box(x + 18, 486, 34, 34), label(x + 66, 506, k, 1.9, "label-bold"), bars(x + 66, 528, [140])]
    # 7 Map panel, 8 events panel (1.45fr / 1fr).
    s += [box(298, 590, 646, 520), label(318, 622, "VISUALISATION / 02 — CARTE DU TRAJET", 1.7, "label-bold"),
          label(690, 622, "● mesurée   ○ dernière connue", 1.5), box(312, 642, 618, 416, "frame")]
    route = [(360, 700), (450, 760), (520, 820), (600, 870), (700, 930), (800, 990), (880, 1030)]
    s.append('<polyline class="wire-rf" points="' + " ".join("%.2f,%.2f" % px(x, y) for x, y in route) + '"/>')
    for (x, y), measured in zip(route[1::2], [True, False, True]):
        cx, cy = px(x, y)
        s.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="2.2" class="{"balloon" if measured else "frame"}"/>')
    s += [label(318, 1088, "◎ 3 positions mesurées sur 5 événements", 1.5), label(820, 1088, "Voir tout ↗", 1.5, "accent")]
    s += [box(961, 590, 437, 520), label(981, 622, "JOURNAL / 03 — INCIDENTS", 1.7, "label-bold")]
    for i, f in enumerate(["Tous", "Chocs", "Inclin.", "Critiques"]):
        s += [box(981 + i * 100, 640, 90, 30, "head" if i == 0 else "frame"), label(993 + i * 100, 660, f, 1.6, "label")]
    for i in range(4):
        y = 690 + i * 100
        s += [box(981, y, 397, 88, "head" if i == 0 else "frame"), box(995, y + 14, 26, 26),
              bars(1036, y + 28, [210, 300], 22), label(1036, y + 78, "CRITIQUE   ● GPS MESURÉ", 1.4, "accent")]
    # 9 Playback, 10 product, 11 footer.
    s += [box(298, 1127, 1100, 92), label(322, 1158, "◷ REJOUER LE TRAJET", 1.8, "label-bold"),
          line(*px(322, 1185), *px(1374, 1185), "wire"), f'<circle cx="{px(1374, 1185)[0]:.2f}" cy="{px(1374, 1185)[1]:.2f}" r="1.6" class="pin"/>',
          label(322, 1208, "Départ", 1.5), label(1330, 1208, "Livraison", 1.5)]
    s += [box(298, 1236, 1100, 160, "head"), label(322, 1280, "CONCEPT PRODUIT / 04", 1.6, "accent"),
          label(322, 1320, "UNE BALISE. DES FAITS.", 3.0, "label-bold"), label(322, 1360, "Plans A3 ›   Planche des pièces ›", 1.6, "label"),
          label(1000, 1330, "[ photo produit ]", 1.8)]
    s += [line(*px(298, 1420), *px(1398, 1420), "thin"), label(298, 1446, "TILTALERT © 2026 • DETECT / ALERT / PROTECT", 1.5)]
    # Width call-outs taken from style.css.
    sx0, sy = px(0, -18)
    sx1, _ = px(256, 0)
    s.append(line(sx0, sy, sx1, sy, "dimension") + txt((sx0 + sx1) / 2, sy - 1, "256 px", 2.2, "dimension-text", "middle"))
    a, _ = px(298, 0)
    b, _ = px(944, 0)
    c, _ = px(1398, 0)
    s.append(line(a, sy, b, sy, "dimension") + txt((a + b) / 2, sy - 1, "1,45 fr (carte)", 2.2, "dimension-text", "middle"))
    s.append(line(b + 4 * K, sy, c, sy, "dimension") + txt((b + c) / 2, sy - 1, "1 fr, min 340 px (journal)", 2.2, "dimension-text", "middle"))
    return "".join(s)


ZONES = [  # (n, x, y anchor in px, balloon offset mm, zone, content, data / action)
    (1, 128, 440, (0, 10), "Barre latérale", "Logo, 4 liens d'ancrage, balise active", "Navigation dans la page"),
    (2, 640, 40, (12, 0), "Barre supérieure", "Fil d'Ariane, pastille démo, import", "Import JSON schemaVersion 1"),
    (3, 1398, 152, (6, -6), "En-tête", "Titre, promesse, bouton d'export", "Export CSV des incidents"),
    (4, 1398, 234, (6, 0), "Avertissement", "Rappel : scénario simulé", "Toujours visible"),
    (5, 1078, 330, (-10, -4), "Dossier trajet", "Identifiant, route, statut, dernier fix", "trip.* du journal"),
    (6, 1398, 520, (6, 0), "Indicateurs", "Événements, critiques, localisés, batterie", "tripStats()"),
    (7, 312, 760, (-8, 6), "Carte Leaflet", "Route, marqueurs mesurés / dernière position", "Clic : sélection + popup"),
    (8, 1378, 900, (8, 0), "Journal", "Filtres et cartes d'incident", "visibleEvents(), locationLabel()"),
    (9, 1398, 1185, (6, 0), "Rejouer", "Curseur 0…N événements", "Filtre temporel de la carte"),
    (10, 1398, 1300, (6, 4), "Concept produit", "Photo, liens vers les plans A3", "Assets de web/public"),
]


def build():
    s = sheet_start(1, "INTERFACE — TABLEAU DE BORD", "TA-UI-01", "≈ 0,15 mm / px", total=1,
                    subtitle="TiltAlert — centre de suivi web (web/), vue bureau 1440 px",
                    revision="Plan d'interface du dashboard",
                    notes=["1. Zones et libellés tirés de web/src/main.js ; largeurs et grilles de web/src/style.css.",
                           "2. Points de rupture CSS : 1250 px, 930 px, 620 px (empilement des panneaux sur mobile).",
                           "3. Données de démonstration (web/src/demo-trip.json) ; aucune mesure réelle affichée.",
                           "4. Règle de preuve : un point n'est jamais présenté comme mesuré s'il vient d'un fix antérieur."],
                    material="—")
    s.append(wireframe())
    for n, x, y, (dx, dy), *_ in ZONES:
        ax, ay = px(x, y)
        s.append(balloon(ax, ay, ax + dx, ay + dy, n))
    rows = [["N°", "ZONE", "CONTENU", "DONNÉE / ACTION"]] + [[str(n), z, c, a] for n, _, _, _, z, c, a in ZONES]
    s.append(txt(258, 34, "NOMENCLATURE DES ZONES", 3.2, "label-bold"))
    s.append(table(258, 37, [7, 24, 60, 59], rows, 5.2, 2.0, 1.85))
    # Detail A: anatomy of one incident card, scaled 3:1 from the 397 x 88 px card.
    x, y, k = 262, 112, 0.36
    s.append(txt(x, y - 4, "DÉTAIL A — CARTE D'INCIDENT (3:1)", 3, "label-bold"))
    s.append(rect(x, y, 397 * k, 88 * k, "frame"))
    s.append(rect(x + 14 * k, y + 14 * k, 26 * k, 26 * k, "head"))
    s.append(txt(x + 27 * k, y + 32 * k, "!", 3, "label-bold", "middle"))
    s.append(txt(x + 55 * k, y + 28 * k, "Choc important", 2.6, "label-bold"))
    s.append(txt(x + 340 * k, y + 28 * k, "11:42", 2.4, "label"))
    s.append(txt(x + 55 * k, y + 52 * k, "Pic simulé : 38 g · contrôle du colis conseillé", 2.2, "sub"))
    s.append(txt(x + 55 * k, y + 76 * k, "CRITIQUE", 2.1, "accent"))
    s.append(txt(x + 130 * k, y + 76 * k, "● GPS MESURÉ  |  ○ DERNIÈRE POSITION  |  — INDISPONIBLE", 2.0, "accent"))
    for letter, ax, ay in (("a", 8, 12), ("b", 47, 16), ("c", 47, 42), ("d", 47, 66), ("e", 122, 66)):
        s.append(txt(x + ax * k, y + ay * k, letter, 2.0, "accent"))
    for i, (t, ax, ay) in enumerate([("a  symbole : ! choc, ↗ inclinaison", 27, 27), ("b  titre + heure de Paris", 120, 28),
                                     ("c  détail et valeur (unité g ou °)", 120, 52), ("d  gravité : critique / modéré / léger", 80, 76),
                                     ("e  statut de position (règle de preuve)", 250, 76)]):
        tx, ty = x + 2, y + 88 * k + 8 + i * 5.2
        s.append(txt(tx, ty, t, 2.2, "label"))
    s.append(txt(262, 186, "PARCOURS UTILISATEUR", 3, "label-bold"))
    for i, t in enumerate(["1. Importer un journal JSON (2) ou garder la démo.", "2. Lire le dossier (5) et les indicateurs (6).",
                           "3. Filtrer le journal (8) ; cliquer un incident centre la carte (7).",
                           "4. Rejouer le trajet (9) pour voir l'ordre des événements.",
                           "5. Exporter le rapport CSV (3) pour un litige ou un audit."]):
        s.append(txt(262, 192 + i * 5.4, t, 2.25, "label"))
    s.append("</svg>")
    return "".join(s)


def main():
    OUT.write_text(build(), encoding="utf-8")
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(OUT.with_suffix(".pdf")), str(OUT)], check=True)
    subprocess.run(["rsvg-convert", "-w", "2200", "-o", str(OUT.with_suffix(".png")), str(OUT)], check=True)
    print(f"Generated {OUT.name} (+ .pdf, .png)")


if __name__ == "__main__":
    main()
