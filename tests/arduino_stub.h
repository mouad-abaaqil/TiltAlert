// Minimal declarations for host-side syntax checking of the Arduino sketch.
#include <stdint.h>

#define HIGH 1
#define LOW 0
#define INPUT 0
#define INPUT_PULLUP 2
#define OUTPUT 1
#define F(x) x

void pinMode(uint8_t, uint8_t);
void digitalWrite(uint8_t, uint8_t);
int digitalRead(uint8_t);
uint32_t millis();

struct SerialStub {
  void begin(unsigned long);
  void print(const char*);
  void print(uint8_t);
  void print(uint32_t);
  void println(const char*);
};

extern SerialStub Serial;
