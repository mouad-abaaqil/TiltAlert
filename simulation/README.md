# Simulation du firmware Uno

`npm test` compile **le vrai `code/tiltalert.ino`** avec le cœur Arduino AVR puis exécute le fichier Intel HEX dans [avr8js](https://github.com/wokwi/avr8js). Le script pilote les broches du microcontrôleur virtuel, écoute l'UART et vérifie D13 (LED) et D3 (buzzer). Le résultat reproductible est `evidence/avr8js-run.json`.

Pré-requis : Node 20.19+, `arduino-cli`, cœur `arduino:avr`, et un compilateur AVR utilisable par votre machine. Sur macOS ARM sans Rosetta, le compilateur AVR officiel Arduino est x86_64 : installer le compilateur natif avec `brew tap osx-cross/avr && brew trust osx-cross/avr && brew install avr-gcc`, puis `brew install universal-ctags`. Le script détecte ces outils dans le `PATH`; `AVR_COMPILER_PATH=/opt/homebrew/bin/ npm test` permet de fixer explicitement le compilateur.

```sh
arduino-cli core update-index
arduino-cli core install arduino:avr
cd simulation
npm ci
npm test
```

Le script de compilation copie le corps du sketch tel quel dans une unité C++ avec `#include <Arduino.h>` ; cela contourne la génération automatique de prototypes d'Arduino CLI, incompatible ici avec la variante de ctags ARM. Le scénario vérifie le démarrage, rejette un rebond de 10 ms, produit cinq transitions LOW→HIGH confirmées sur D2, confirme l'alarme sur D13 et D3, puis appuie sur le bouton D12 pour la réinitialiser. La simulation vérifie la logique et la correspondance des broches du firmware ; elle ne mesure ni les courants, ni l'acoustique du KY-012, ni le comportement physique du KY-020.

`wokwi/diagram.json` offre une version visuelle du même câblage. Le switch D2 sélectionne 0 V ou 5 V pour reproduire l'état logique OUT du KY-020 ; maintenir chaque position plus de 40 ms. Le bouton D12 correspond au reset. La LED orange supplémentaire témoigne de la sortie D3, car le buzzer piézo passif proposé par Wokwi ne représente pas exactement le module **actif** KY-012 alimenté en continu. `wokwi/sketch.ino` est généré depuis le firmware avec `npm run wokwi:generate` ; il ne doit pas être modifié à la main. Le même fichier sert au montage [Tinkercad](./tinkercad/README.md).

Le 3 octobre 2026, un essai interactif dans Wokwi (`diagram.json` + `sketch.ino` chargés tels quels) a affiché successivement `ready`, cinq événements `tilt` puis `alarm` à `count=5`, avec les LED D13 et D3 allumées, puis `reset` à `count=0` après appui sur RESET, LED éteintes. Les [captures](./captures/) le montrent : [démarrage](./captures/wokwi-ready.jpg), [alarme](./captures/wokwi-alarm.jpg), [acquittement](./captures/wokwi-reset.jpg) et [journal série complet](./captures/wokwi-serial-log.jpg). Le reset est aussi couvert par le test AVR automatique. Remarque de reproduction : l'onglet doit être visible, sinon le navigateur ralentit la simulation à quelques pour cent et les basculements sont trop brefs pour passer l'anti-rebond de 40 ms. Le [chronogramme SVG](./evidence/avr8js-timeline.svg) est généré depuis la trace réelle par `python3 generate-evidence.py` ; il montre les cinq événements, l'alarme et le reset, sans inventer de mesure analogique.
