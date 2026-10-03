# Circuit Uno corrigé — TiltAlert

Ce dossier décrit **le prototype Arduino Uno actuel**, avec une netlist explicite, un schéma électrique A3, une [implantation physique sur breadboard](./tiltalert-uno-physical.svg) et une nomenclature. Le [schéma SVG](./tiltalert-uno-electrical.svg) et le [PDF de deux pages](./tiltalert-uno-electrical.pdf) sont générés par `generate.py` depuis `netlist.json` ; l'implantation vient de la table de placement de `physical.py`. Le dessin est schématique, sans échelle physique.

## Générer et contrôler

```bash
python3 hardware/validated-uno/generate.py
```

La génération vérifie toutes les affectations de bornes, la topologie attendue, l'unicité des bornes, et la séparation de `+5V` et `GND`. Elle reconstruit aussi les nœuds électriques de la breadboard (bandes a–e / f–j, rails, jumpers) et refuse l'implantation si un réseau est coupé, si deux réseaux se touchent ou si deux pattes partagent un trou. `rsvg-convert` est nécessaire pour le PDF. Ce contrôle statique ne remplace pas les essais sur carte ni la vérification électrique d'un montage physique.

## Câblage

| Réseau | Bornes |
|---|---|
| `+5V` | Uno 5V, contact d'inclinaison S1-1, buzzer actif BZ1-VCC |
| `GND` | Uno GND, R1-2, bouton S2-2, LED D1 cathode, buzzer BZ1-GND |
| `TILT_D2` | Uno D2, S1-2, R1-1 |
| `RESET_D12` | Uno D12, S2-1 |
| `ALARM_D13` | Uno D13, R2-1 |
| `LED_A` | R2-2, anode LED D1 |
| `BUZZ_D3` | Uno D3, entrée SIG du buzzer actif BZ1 |

Le code utilise `INPUT` sur D2 : **R1 (10 kΩ) est indispensable avec un contact nu** pour définir LOW quand S1 est ouvert. La fermeture de S1 applique HIGH à D2. D12 utilise `INPUT_PULLUP`; le bouton relie D12 à la masse lorsqu'il est pressé. La LED **externe** a sa propre résistance R2 de 220 Ω. La LED intégrée de l'Uno, également pilotée par D13, peut s'allumer en parallèle.

Le sketch applique un niveau HIGH continu à D3 pendant l'alarme. Il faut donc un **buzzer actif** à entrée de commande logique 5 V et faible courant. Une simple pastille piezo passive à deux bornes n'émettra pas une tonalité continue avec ce code. Si un module actif consomme plus que ce que la sortie D3 peut fournir ou n'a pas d'entrée SIG, prévoir un étage transistor adapté avant montage; le présent schéma suppose une entrée SIG à faible courant.

Le fichier historique `hardware/wiring_diagram.brd` relie par erreur la broche **5V** de l'Uno au réseau **GND** et représente un piezo passif. Ne pas le reproduire comme câblage validé. Le contact simulé représente uniquement l'état ouvert/fermé du KY-020; il ne démontre ni sensibilité aux chocs, ni accélération, ni position.

**À vérifier sur le module KY-020 reçu.** Certains modules portent une résistance embarquée. Mesurer au multimètre, module hors tension, la résistance entre S et +V puis entre S et GND. Une résistance de rappel vers +V combinée à R1 formerait un diviseur et laisserait D2 à un niveau intermédiaire : dans ce cas seulement, retirer R1 ou utiliser un contact d'inclinaison nu, comme sur l'implantation. Une résistance vers GND se met simplement en parallèle de R1 sans gêner la lecture.
