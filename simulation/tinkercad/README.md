# Variante Tinkercad Circuits (guide, non réalisée)

Les captures de la preuve de concept ont été faites dans Wokwi (voir [`../captures/`](../captures/)), car Tinkercad ne sait pas importer un circuit décrit en code : tout y est placé à la main. Ce guide reste valable pour refaire le montage dans Tinkercad.

Ce montage reproduit dans [Tinkercad Circuits](https://www.tinkercad.com/circuits) le circuit Uno validé ([`hardware/validated-uno/netlist.json`](../../hardware/validated-uno/netlist.json)) et exécute le firmware réel. Il complète la [simulation AVR automatique](../README.md), sans la remplacer. Ici, l'objectif est d'obtenir des **captures visuelles** pour la présentation.

## Code

L'éditeur de Tinkercad n'accepte qu'un seul fichier. Utiliser [`../wokwi/sketch.ino`](../wokwi/sketch.ino) : c'est le firmware `code/tiltalert.ino` avec `TiltAlertCore.h` intégré, généré par `npm run wokwi:generate`. Dans Tinkercad, ouvrir **Code → Texte**, tout remplacer par ce fichier, puis lancer la simulation.

## Câblage (identique à la netlist)

| Pièce Tinkercad | Raccordement | Réseau |
|---|---|---|
| Arduino Uno R3 | 5V → rail +, GND → rail − | `+5V`, `GND` |
| Interrupteur à glissière (à la place du KY-020) | broche commune → D2 ; une extrémité → rail + | `TILT_D2` |
| Résistance 10 kΩ (R1) | D2 → rail − | rappel de D2 |
| Bouton-poussoir (S2) | D12 → bouton → rail − | `RESET_D12` (INPUT_PULLUP) |
| Résistance 220 Ω (R2) + LED rouge (D1) | D13 → R2 → anode ; cathode → rail − | `ALARM_D13`, `LED_A` |
| Résistance 220 Ω + LED orange | D3 → résistance → anode ; cathode → rail − | `BUZZ_D3` (témoin) |

Deux substitutions, comme dans la version Wokwi :

- **Capteur :** l'interrupteur remplace la sortie logique du contact d'inclinaison. Il ne modélise ni la mécanique, ni un choc.
- **Buzzer :** le firmware applique un niveau HIGH continu sur D3, prévu pour un buzzer **actif**. Le piézo de Tinkercad est passif et resterait muet avec ce signal. Une LED témoin affiche donc l'état de D3.

## Scénario de capture

1. Démarrer la simulation, puis ouvrir le moniteur série : la ligne `{"event":"ready",...}` s'affiche.
2. Basculer l'interrupteur 5 fois (aller-retour, en maintenant chaque position plus de 40 ms) : 5 lignes `tilt` s'affichent.
3. Au 5ᵉ basculement, la ligne `alarm` apparaît et les LED D13 et D3 s'allument. **Capture 1 : alarme.**
4. Appuyer sur le bouton : la ligne `reset` apparaît et les LED s'éteignent. **Capture 2 : acquittement.**

Les captures sont à enregistrer dans ce dossier (`tinkercad-alarm.png`, `tinkercad-reset.png`), avec le lien public du projet Tinkercad s'il est partagé.
