# TiltAlert V2 — carte TA-MB-01 (nRF9151)

**Statut : architecture de conception sourcée.** Le PCB n'est ni routé, ni fabriqué, ni testé. Ce dossier ne décrit pas le prototype Uno de `code/` : celui-ci reste la preuve de concept logique.

La V2 remplace la pile de modules MKR envisagée au départ par **une seule carte sur mesure**. Le modem cellulaire et le GNSS sont intégrés dans un même boîtier SiP, et des capteurs conçus pour le suivi de colis sur batterie complètent la carte. Le boîtier passe ainsi d'environ 124 × 84 × 36 mm (encombrement de la pile MKR) à **86 × 58 × 20 mm**.

## Plans

| Planche | Contenu |
|---|---|
| [Feuille 1 — assemblage](../../cad/output/tiltalert-trace-sheet-1.pdf) | Vues cotées, coupe A–A à travers U1/ANT2/J1, profil USB-C + bouton, isométrie. |
| [Feuille 2 — carte et implantation](../../cad/output/tiltalert-trace-sheet-2.pdf) | Face composants 2:1 avec repères, zone dégagée de l'antenne LTE, capot intérieur, batterie. |
| [Feuille 3 — éclaté et nomenclature](../../cad/output/tiltalert-trace-sheet-3.pdf) | Vue éclatée repérée, 25 lignes de nomenclature avec statut de chaque cote. |
| [Feuille 4 — architecture électrique](../../cad/output/tiltalert-trace-sheet-4.pdf) | Schéma fonctionnel, rails contrôlés, bus, câble unique, points firmware. |

Le jeu complet est aussi disponible dans [`tiltalert-trace-plans-A3.pdf`](../../documentation/tiltalert-trace-plans-A3.pdf). Les quatre feuilles sont générées par `cad/generate.py` à partir de [`netlist.json`](./netlist.json) et du modèle 3D.

## Choix des composants

| Rep. | Composant | Pourquoi |
|---|---|---|
| U1 | [Nordic nRF9151](https://www.nordicsemi.com/Products/nRF9151) SiP 12 × 11 mm | Modem LTE-M/NB-IoT **et** GNSS intégrés, processeur Cortex-M33 applicatif. Remplace le MKR NB 1500 et le module GNSS séparé. |
| U2 | [ADXL372](https://www.analog.com/en/products/adxl372.html) ±200 g | Conçu pour la surveillance d'impacts sur des biens en transit : veille active de 1,4 µA, capture du seul pic au-dessus du seuil, FIFO profond. |
| U3 | [ADXL367](https://www.analog.com/en/products/adxl367.html) ±2/4/8 g | Inclinaison par la gravité et réveil sur mouvement à 180 nA. |
| U4 | [nPM1300](https://www.nordicsemi.com/Products/nPM1300) | Chargeur 32–800 mA, jauge, deux régulateurs abaisseurs et pilotes de LED dans une seule puce. |
| U5 | Macronix MX25R6435F, 64 Mbit | Journal non volatil : rien n'est perdu sans réseau. Courant de 7 nA en mise en veille profonde. |
| U6 + ANT2 | Filtre puis LNA + patch [Taoglas CGGBP.18.4.A.02](https://www.taoglas.com/product/cggbp-18-4-a-02-gpsglonassbeidou-patch-antenna-18mm-2) | Topologie [recommandée par Nordic](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/gps_if.html) avec une antenne passive. |
| ANT1 | Ignion NN02-224 (12 × 3 × 2,4 mm) | Antenne puce LTE couvrant 824–960 et 1710–2690 MHz, placée en bord de carte. |
| J2 | eSIM soudée MFF2 | Aucune carte SIM ne peut se déloger lors d'un choc. |
| BT1 | Li-Po 1S 1200 mAh protégée ([Adafruit 258](https://www.adafruit.com/product/258), 62 × 34 × 5 mm) | Cellule protégée et prise JST-PH, posée sur de la mousse sous la carte. |

Le nRF9151 n'a **pas d'USB natif**. Le port USB-C sert uniquement à la charge (VBUS vers le nPM1300). La programmation passe par des pastilles SWD Tag-Connect (J4).

Pour développer le firmware avant de fabriquer le PCB, la [Nordic Thingy:91 X](https://docs.nordicsemi.com/r/bundle/ug_thingy91x/page/ug/thingy91x/intro/frontpage.html) réunit le nRF9151, un PMIC nPM1300 et une batterie de 1350 mAh.

## Ce que les scripts vérifient

`cad/generate.py --check` contrôle, à chaque génération :

- **Netlist :**
  - chaque broche d'alimentation se trouve sur le rail déclaré ;
  - la plage de chaque rail tient dans la plage du composant (par exemple V1V8 dans 1,6–3,5 V pour l'ADXL372, VSYS dans 3,0–5,5 V pour le VDD du nRF9151) ;
  - aucune broche n'est reliée à deux réseaux, et chaque circuit intégré a une masse ;
  - les sélections SPI sont distinctes, les adresses I²C aussi, et chaque membre est bien sur son bus.
- **Mécanique :**
  - les 20 pièces sont dans la cavité ;
  - aucune ne touche une autre pièce, une paroi ou un bossage (jeu minimal de 0,2 mm) ;
  - les composants sont posés sur la carte, et aucun n'entre dans la zone dégagée de l'antenne LTE ;
  - les ouvertures USB-C et bouton traversent bien la paroi en face de J1 et SW1.

Ces contrôles ne remplacent ni un routage, ni une simulation RF, ni des essais.

## Points à lever avant le routage

1. **Séquencement :** VDD_GPIO (1,8 V) doit monter plus de 6 ms après VDD et ENABLE. Il faut le programmer sur le BUCK1 du nPM1300.
2. **Adresses I²C :** celles de l'ADXL367 (0x1D prévue) et du nPM1300 (0x6B prévue) sont à confirmer sur les fiches techniques.
3. **GPIO du nRF9151 :** leur affectation (CS0, CS1, INT1–3, BTN, BUZ, COEX0) est à figer au routage.
4. **Antennes :**
   - accord des antennes avec la batterie sous la carte et le capot final ;
   - zone dégagée LTE conforme à la fiche Ignion ;
   - patch GNSS sans aucun métal au-dessus.
5. **Fixation mécanique :** les accéléromètres doivent être couplés rigidement au boîtier, sinon la mesure du choc est faussée. Les 4 points de fixation de la carte restent à définir.
6. **Marge d'alimentation :** VSYS sur batterie descend jusqu'à 3,0 V (coupure de protection), soit exactement le minimum du VDD du nRF9151. Il ne reste donc aucune marge pour les chutes lors des émissions LTE. Il faut mesurer la tension minimale sous émission et, si besoin, arrêter l'appareil plus tôt par la jauge (seuil logiciel).
7. **Budget d'énergie :** il est à mesurer (par exemple au Power Profiler Kit) sur des profils de transport réels. Aucune autonomie n'est annoncée.

## Ordre de validation

1. Écrire le firmware sur Thingy:91 X : détection d'impacts, journal, envoi LTE-M, fix GNSS.
2. Router le PCB à 4 couches, puis faire une revue RF et une revue d'implantation.
3. Monter la carte : vérifier les rails, le séquencement, le SWD, puis la lecture des capteurs.
4. Faire des essais de chocs étalonnés, d'inclinaison et de faux positifs, carte fixée dans le boîtier.
5. Vérifier la qualité des fixes GNSS en extérieur et en véhicule, et l'enregistrement hors réseau.
6. Mesurer l'autonomie, la charge et la tenue en température avant toute promesse produit.
