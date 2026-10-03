#include "TiltAlertCore.h"

// Validated Uno wiring: KY-020 OUT -> D2, KY-012 -> D3,
// red LED -> D13, KY-004 button -> D12 (active LOW).
const uint8_t tiltPin = 2;
const uint8_t buzzerPin = 3;
const uint8_t ledPin = 13;
const uint8_t buttonPin = 12;

tiltalert::Controller controller;

void printEvent(const char* event, uint32_t now) {
  // JSON Lines over USB serial. uptime_ms is time since boot, not a UTC date.
  Serial.print(F("{\"event\":\""));
  Serial.print(event);
  Serial.print(F("\",\"uptime_ms\":"));
  Serial.print(now);
  Serial.print(F(",\"count\":"));
  Serial.print(controller.count());
  Serial.print(F(",\"threshold\":"));
  Serial.print(tiltalert::kThreshold);
  Serial.println(F("}"));
}

void setup() {
  pinMode(tiltPin, INPUT);  // Existing circuit uses an external pull-down.
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);
  digitalWrite(ledPin, LOW);

  Serial.begin(9600);
  const uint32_t now = millis();
  controller.begin(now, digitalRead(tiltPin) == HIGH,
                   digitalRead(buttonPin) == LOW);
  printEvent("ready", now);
}

void loop() {
  const uint32_t now = millis();
  const tiltalert::Events events = controller.update(
      now, digitalRead(tiltPin) == HIGH, digitalRead(buttonPin) == LOW);

  if (events.tiltRecorded) printEvent("tilt", now);
  if (events.alarmStarted) printEvent("alarm", now);
  if (events.reset) printEvent("reset", now);

  const uint8_t output = controller.alarmActive() ? HIGH : LOW;
  digitalWrite(buzzerPin, output);
  digitalWrite(ledPin, output);
}
