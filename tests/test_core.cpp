#include "../code/TiltAlertCore.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

using tiltalert::Controller;
using tiltalert::Events;

static Events step(Controller& device, uint32_t now, bool tilt, bool button = false) {
  return device.update(now, tilt, button);
}

static void recordCycle(Controller& device, uint32_t start, uint8_t expectedCount) {
  assert(!step(device, start, true).tiltRecorded);
  assert(!step(device, start + 20, false).tiltRecorded);  // contact bounce
  assert(!step(device, start + 25, true).tiltRecorded);
  Events e = step(device, start + 65, true);
  assert(e.tiltRecorded);
  assert(e.alarmStarted == (expectedCount == tiltalert::kThreshold));
  assert(device.count() == expectedCount);
  assert(!step(device, start + 70, true).tiltRecorded);  // held high
  assert(!step(device, start + 80, false).tiltRecorded);
  assert(!step(device, start + 110, true).tiltRecorded); // release bounced
  assert(!step(device, start + 120, false).tiltRecorded);
  assert(!step(device, start + 160, false).tiltRecorded);
}

int main() {
  Controller device;
  assert(!step(device, 0, true).tiltRecorded);  // no begin, no event
  device.begin(0, false, false);

  for (uint8_t n = 1; n <= tiltalert::kThreshold; ++n)
    recordCycle(device, static_cast<uint32_t>(n) * 200, n);
  assert(device.alarmActive());
  assert(device.count() == 5);

  // Further movement cannot inflate a latched alarm's count.
  assert(!step(device, 1300, true).tiltRecorded);
  assert(!step(device, 1340, true).tiltRecorded);
  assert(device.count() == 5);

  // Short or bouncing button presses are ignored.
  assert(!step(device, 1400, false, true).reset);
  assert(!step(device, 1410, false, false).reset);
  assert(!step(device, 1420, false, true).reset);
  assert(!step(device, 1454, false, true).reset);
  assert(device.alarmActive());
  assert(step(device, 1455, false, true).reset);
  assert(!device.alarmActive() && device.count() == 0);
  assert(!step(device, 1500, false, true).reset);  // held button

  // A high sensor at boot requires a confirmed LOW before the next HIGH.
  device.begin(0, true, false);
  assert(!step(device, 100, true).tiltRecorded);
  assert(!step(device, 101, false).tiltRecorded);
  assert(!step(device, 141, false).tiltRecorded);
  assert(!step(device, 142, true).tiltRecorded);
  assert(step(device, 182, true).tiltRecorded);

  // millis() wraparound must not break debounce timing.
  device.begin(UINT32_MAX - 20, false, false);
  assert(!step(device, UINT32_MAX - 10, true).tiltRecorded);
  assert(!step(device, 28, true).tiltRecorded);
  assert(step(device, 29, true).tiltRecorded);

  puts("TiltAlert core tests passed");
}
