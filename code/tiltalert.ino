// TiltAlert - Dispositif de Détection de Chocs et d'Inclinaisons

// Définition des broches
const int tiltPin = 2;         // Pin de signal du capteur de basculement KY-020
const int buzzerPin = 3;       // Pin pour le buzzer KY-012
const int ledPin = 13;         // Pin pour la LED rouge
const int buttonPin = 12;      // Pin pour le bouton poussoir KY-004

// Variables globales
int tiltCounter = 0;           // Compteur d'inclinaisons détectées
int tiltThreshold = 5;         // Seuil d'inclinaisons pour déclencher l'alarme
bool isTilted = false;         // Indicateur si le capteur est incliné
bool alarmActive = false;      // Indicateur si l'alarme est activée

void setup() {
  // Configuration des broches
  pinMode(tiltPin, INPUT);           // Capteur KY-020 en entrée
  pinMode(buzzerPin, OUTPUT);        // Buzzer KY-012 en sortie
  pinMode(ledPin, OUTPUT);           // LED rouge en sortie
  pinMode(buttonPin, INPUT_PULLUP);  // Bouton poussoir KY-004 en entrée avec pull-up
  Serial.begin(9600);                // Initialisation du moniteur série

  // Message de bienvenue
  Serial.println("TiltAlert - Surveillance d'inclinaisons activée.");
}

void loop() {
  // Lecture de l'état du bouton poussoir
  int buttonState = digitalRead(buttonPin);

  // Réinitialisation du système si le bouton est pressé
  if (buttonState == LOW && alarmActive) {
    Serial.println("Réinitialisation !");
    digitalWrite(buzzerPin, LOW);    // Désactiver le buzzer
    digitalWrite(ledPin, LOW);       // Éteindre la LED
    tiltCounter = 0;                 // Réinitialiser le compteur
    alarmActive = false;             // Désactiver l'alarme
    delay(200);                      // Pause pour éviter un rebond du bouton
  }

  // Lecture de l'état du capteur de basculement
  int tiltState = digitalRead(tiltPin);

  // Détection d'une nouvelle inclinaison
  if (tiltState == HIGH && !isTilted && !alarmActive) {
    tiltCounter++;                  // Incrémenter le compteur
    isTilted = true;                // Marquer l'état incliné
    Serial.print("Inclinaisons détectées : ");
    Serial.println(tiltCounter);
  }

  // Réinitialisation de l'état incliné si le capteur revient à LOW
  if (tiltState == LOW) {
    isTilted = false;
  }

  // Activation de l'alarme si le seuil est atteint
  if (tiltCounter >= tiltThreshold && !alarmActive) {
    Serial.println("Seuil atteint, activation de l'alarme !");
    digitalWrite(buzzerPin, HIGH);  // Activer le buzzer
    digitalWrite(ledPin, HIGH);     // Allumer la LED
    alarmActive = true;             // Marquer l'alarme active
  }

  delay(100);  // Petite pause avant la prochaine itération
}
