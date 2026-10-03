# Nomenclature — TiltAlert Uno corrigé

| Réf. | Composant | Quantité / valeur | Note |
|---|---|---|---|
| U1 | Arduino Uno R3 | 1 | Sorties D3 et D13; entrées D2 et D12 |
| S1 | Contact d'inclinaison NO | 1 | KY-020 ou contact équivalent; fermé = HIGH sur D2 |
| R1 | Résistance | 10 kΩ | Pull-down externe de D2; 0,25 W |
| S2 | Bouton poussoir NO | 1 | Acquittement; D12 utilise INPUT_PULLUP |
| R2 | Résistance | 220 Ω | Limitation du courant de la LED externe; 0,25 W |
| D1 | LED rouge externe | 1 | Anode vers R2; cathode vers GND |
| BZ1 | Buzzer actif 5 V | 1 | Entrée signal compatible 5 V, faible courant; vérifier la fiche du module choisi |

Ajouter une breadboard, des fils de liaison et un câble USB pour le montage d'essai.
Le buzzer actif doit accepter un signal logique de 5 V et présenter une entrée de commande à faible courant.
La valeur de 220 Ω donne environ 10–15 mA pour une LED rouge typique; vérifier la LED et la limite de la broche.
