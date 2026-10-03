#ifndef TILT_ALERT_CORE_H
#define TILT_ALERT_CORE_H

#include <stdint.h>

// Pure C++ state machine; no Arduino dependency, so transitions can be tested
// with synthetic inputs before uploading to an Uno.
namespace tiltalert {

static const uint8_t kThreshold = 5;
static const uint32_t kTiltDebounceMs = 40;
static const uint32_t kButtonDebounceMs = 35;

struct Events {
  bool tiltRecorded;
  bool alarmStarted;
  bool reset;
};

class DebouncedInput {
 public:
  explicit DebouncedInput(uint32_t intervalMs)
      : intervalMs_(intervalMs), raw_(false), stable_(false), changedAt_(0) {}

  void begin(bool value, uint32_t now) {
    raw_ = value;
    stable_ = value;
    changedAt_ = now;
  }

  bool update(bool value, uint32_t now) {
    if (value != raw_) {
      raw_ = value;
      changedAt_ = now;
    }
    if (stable_ != raw_ && static_cast<uint32_t>(now - changedAt_) >= intervalMs_) {
      stable_ = raw_;
      return true;
    }
    return false;
  }

  bool stable() const { return stable_; }

 private:
  uint32_t intervalMs_;
  bool raw_;
  bool stable_;
  uint32_t changedAt_;
};

class Controller {
 public:
  Controller()
      : tilt_(kTiltDebounceMs), button_(kButtonDebounceMs),
        count_(0), alarm_(false), started_(false) {}

  void begin(uint32_t now, bool tiltHigh, bool buttonPressed) {
    tilt_.begin(tiltHigh, now);
    button_.begin(buttonPressed, now);
    count_ = 0;
    alarm_ = false;
    started_ = true;
  }

  Events update(uint32_t now, bool tiltHigh, bool buttonPressed) {
    Events events = {false, false, false};
    if (!started_) return events;

    const bool tiltChanged = tilt_.update(tiltHigh, now);
    const bool buttonChanged = button_.update(buttonPressed, now);

    // One confirmed press resets a latched alarm. A held button cannot
    // repeatedly reset the counter or acknowledge a later alarm.
    if (buttonChanged && button_.stable() && alarm_) {
      count_ = 0;
      alarm_ = false;
      events.reset = true;
      return events;
    }

    // A cycle means a stable LOW -> HIGH transition. Contact chatter and
    // an initially HIGH sensor are not counted as new inclinations.
    if (tiltChanged && tilt_.stable() && !alarm_) {
      ++count_;
      events.tiltRecorded = true;
      if (count_ >= kThreshold) {
        alarm_ = true;
        events.alarmStarted = true;
      }
    }
    return events;
  }

  uint8_t count() const { return count_; }
  bool alarmActive() const { return alarm_; }

 private:
  DebouncedInput tilt_;
  DebouncedInput button_;
  uint8_t count_;
  bool alarm_;
  bool started_;
};

}  // namespace tiltalert

#endif
