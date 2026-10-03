#!/usr/bin/env python3
"""Render an engineering timeline from the AVR simulator's recorded evidence."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "evidence/avr8js-run.json").read_text())
timeline = data["timeline"]
start, end = 0, 1250
left, right = 205, 1470
def x(ms):
    return left + (right - left) * (ms - start) / (end - start)
def line(x1, y1, x2, y2, cls):
    return f'<line x1="{x1:.1f}" y1="{y1}" x2="{x2:.1f}" y2="{y2}" class="{cls}"/>'
def text(x0, y0, value, cls):
    return f'<text x="{x0:.1f}" y="{y0}" class="{cls}">{html.escape(str(value))}</text>'

parts = ['''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 610" role="img" aria-label="TiltAlert AVR simulation timeline">
<style>
  .bg{fill:#102842}.panel{fill:#143554;stroke:#76a8d1;stroke-width:2}.grid{stroke:#2c5878;stroke-width:1}
  .axis{stroke:#a6d6f4;stroke-width:2}.event{stroke:#fff;stroke-width:3}.out{stroke:#ffdb51;stroke-width:5}
  .dot{fill:#ffdb51;stroke:#fff;stroke-width:2}.title{fill:#fff;font:700 31px Arial}
  .label{fill:#fff;font:700 18px Arial}.small{fill:#b6d5ea;font:15px Arial}.count{fill:#ffdb51;font:700 20px Arial}
</style><rect class="bg" width="1600" height="610"/><rect class="panel" x="28" y="28" width="1544" height="554" rx="10"/>''']
parts += [text(60, 82, "TILTALERT  /  SIMULATION AVR ATmega328P", "title"),
          text(60, 112, "Firmware compilé • événements série et états des broches enregistrés", "small")]
for t in range(0, 1251, 250):
    xx = x(t)
    parts += [line(xx, 155, xx, 505, "grid"), text(xx - 16, 532, f"{t} ms", "small")]
parts += [text(60, 195, "D2 • inclinaison", "label"),
          text(60, 310, "D13 • LED", "label"),
          text(60, 425, "D3 • buzzer", "label"),
          line(left, 215, right, 215, "axis")]
for item in timeline:
    if item["label"].startswith("tilt "):
        xx = x(item["simulated_ms"])
        n = item["latest_serial"]["count"]
        parts += [line(xx, 195, xx, 235, "event"),
                  f'<circle cx="{xx:.1f}" cy="215" r="10" class="dot"/>',
                  text(xx - 6, 180, n, "count")]
alarm_ms = next(item["simulated_ms"] for item in timeline if item["label"] == "tilt 5")
reset_ms = next(item["simulated_ms"] for item in timeline if item["label"] == "button reset")
for y in (330, 445):
    parts += [line(left, y, x(alarm_ms), y, "axis"),
              line(x(alarm_ms), y, x(alarm_ms), y - 32, "out"),
              line(x(alarm_ms), y - 32, x(reset_ms), y - 32, "out"),
              line(x(reset_ms), y - 32, x(reset_ms), y, "out"),
              line(x(reset_ms), y, right, y, "axis")]
parts += [text(x(alarm_ms) - 105, 277, "ALARME • 5/5", "count"),
          text(x(reset_ms) - 35, 387, "RESET", "count"),
          text(60, 562, "Source : simulation/evidence/avr8js-run.json • états numériques, pas mesures de courant ni de choc.", "small"),
          "</svg>"]
(ROOT / "evidence/avr8js-timeline.svg").write_text("".join(parts))
