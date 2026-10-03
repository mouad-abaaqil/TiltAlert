# TiltAlert — étude mécanique paramétrique

Ce dossier contient le **concept de boîtier et d'implantation de la V2** (carte TA-MB-01, nRF9151), distinct du montage Arduino Uno actuel. Les dimensions sont **provisoires**. Le PCB n'est pas routé ; l'étanchéité, la visserie et les tolérances d'assemblage ne sont pas validées. `components.py` modélise les composants et `drafting.py` le cadre A3 commun.

## Reproduire les exports

Sur macOS avec Python 3.12 et `rsvg-convert` :

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r cad/requirements.txt
.venv/bin/python cad/generate.py --check
.venv/bin/python cad/generate.py
```

Le modèle, la carte peuplée TA-MB-01 (contours sourcés dans `hardware/trace-v2/netlist.json`) et les quatre plans A3 sont générés depuis les paramètres `Dimensions` de [`generate.py`](generate.py). Les cotes, les positions des bossages, la coupe A–A, les vues orthographiques et la vue éclatée sont calculées depuis la même géométrie. `rsvg-convert` transforme les SVG en PDF et PNG. Tous les fichiers produits sont dans [`output/`](output/).

| Fichier | Usage |
|---|---|
| `tiltalert-trace-sheet-1.svg/.pdf/.png` | Assemblage : dessus, face, profil USB-C/bouton, coupe A–A, isométrie. |
| `tiltalert-trace-sheet-2.svg/.pdf/.png` | Carte TA-MB-01 à 2:1 avec repères et zone dégagée LTE, capot intérieur, batterie. |
| `tiltalert-trace-sheet-3.svg/.pdf/.png` | Vue éclatée repérée et nomenclature complète. |
| `tiltalert-trace-sheet-4.svg/.pdf/.png` | Architecture électrique : schéma fonctionnel, rails, bus, câble. |
| `tiltalert-trace-assembly.step` | Assemblage complet : boîtier, carte, composants, batterie. |
| `tiltalert-trace-base.step/.stl` | Solide de la base conceptuelle. |
| `tiltalert-trace-lid.step/.stl` | Solide du capot conceptuel. |

Le code de génération vérifie les dimensions extérieures, les volumes positifs, le perçage des quatre bossages, les ouvertures USB-C et bouton, la netlist V2 (rails, bus, câble) et l'absence de contact entre composants, parois et bossages (jeu ≥ 0,2 mm), y compris la zone dégagée de l'antenne LTE. Le script copie ensuite les feuilles vers `documentation/` et `web/public/assets/`. Ce contrôle géométrique ne remplace pas un essai d'impression, une revue mécanique, ni une validation de fabrication.
