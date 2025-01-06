<p align="center">
  <img src="./documentation/TiltAlert.png" alt="Logo TiltAlert" width="200">
</p>

# Cahier des Charges - Projet TiltAlert

## 1. Introduction
TiltAlert est un projet basé sur Arduino qui permet de surveiller des colis ou équipements sensibles en détectant les chocs et les inclinaisons critiques. Ce dispositif offre une alerte sonore et visuelle en cas de mouvement anormal, et il est réinitialisable pour une utilisation multiple.

### Objectif
Fournir une solution abordable et efficace pour le transport sécurisé de biens fragiles ou sensibles aux chocs.

---

## 2. Analyse des Besoins

### 2.1 Fonctionnalités Requises
- Détection précise des inclinaisons critiques.
- Alerte sonore avec buzzer (KY-012).
- Alerte visuelle avec une LED rouge.
- Possibilité de réinitialisation via un bouton poussoir (KY-004).

### 2.2 Contraintes
- **Technique** : 
  - Doit être compatible avec un Arduino Uno.
  - Alimenté via USB ou batterie portable.
- **Pratique** : 
  - Facile à intégrer dans un boîtier compact.
  - Doit fonctionner dans des environnements variés (température ambiante normale).
- **Budget** : 
  - Conception avec des composants économiques et facilement accessibles.

### 2.3 Applications
- Transport logistique : Surveillance de colis fragiles.
- Industries : Surveillance des équipements sensibles.
- Usage personnel : Suivi des objets fragiles pendant un déplacement.

---

## 3. Spécifications Techniques

### 3.1 Matériel Utilisé
- 1x Arduino Uno
- 1x Capteur KY-020 (inclinaison)
- 1x Buzzer KY-012
- 1x Bouton poussoir KY-004
- 1x LED rouge
- Résistances : 220 Ω, 10 kΩ
- Breadboard
- Câbles de connexion

### 3.2 Fonctionnement
1. Lorsqu'une inclinaison critique est détectée par le capteur KY-020, le système incrémente un compteur interne.
2. Si le nombre d'inclinaisons détectées atteint le seuil (5), une LED rouge s'allume et le buzzer émet un son continu.
3. L'utilisateur peut réinitialiser le système via un bouton poussoir pour recommencer une nouvelle surveillance.

### 3.3 Schéma de Câblage
Le schéma de câblage complet est disponible dans le fichier `wiring_diagram.png`.

---

## 4. Tests et Validation

### 4.1 Scénarios de Test
- Inclinaison simulée avec le capteur KY-020 pour vérifier le seuil critique.
- Activation des alertes visuelles et sonores.
- Réinitialisation via le bouton poussoir.

### 4.2 Résultats Attendus
- Inclinaison détectée : LED et buzzer activés lorsque le seuil est atteint.
- Réinitialisation : Compteur remis à zéro, LED et buzzer éteints.

---

## 5. Améliorations Futures
- Ajout d'un module Bluetooth pour envoyer des notifications sur smartphone.
- Remplacement du capteur KY-020 par un accéléromètre pour une détection plus précise.
- Intégration dans un boîtier imprimé en 3D pour une solution plus robuste.

---

## 6. Conclusion
Le projet TiltAlert est une solution simple et abordable pour la surveillance des objets fragiles. Son architecture basée sur Arduino permet une personnalisation et une évolutivité importantes.

---

Pour toute question ou suggestion d'amélioration, n'hésitez pas à contribuer via le repository GitHub !
