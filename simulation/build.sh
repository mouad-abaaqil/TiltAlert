#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p simulation/.build/TiltAlert simulation/.build/output
# Arduino CLI's prototype generator uses ctags. Put the unchanged sketch body
# in a C++ unit so a host-native ctags can process an empty .ino on ARM Macs.
printf '%s\n' '// Firmware body is compiled from Firmware.cpp.' > simulation/.build/TiltAlert/TiltAlert.ino
{ printf '%s\n' '#include <Arduino.h>'; cat code/tiltalert.ino; } > simulation/.build/TiltAlert/Firmware.cpp
cp code/TiltAlertCore.h simulation/.build/TiltAlert/TiltAlertCore.h
compiler_path="${AVR_COMPILER_PATH:-}"
if [ -z "$compiler_path" ] && command -v avr-g++ >/dev/null 2>&1; then
  compiler_path="$(dirname "$(command -v avr-g++)")/"
fi
if [ -n "$compiler_path" ]; then
  arduino-cli compile --fqbn arduino:avr:uno --build-property "compiler.path=$compiler_path" \
    --build-property "runtime.tools.ctags.path=$(dirname "$(command -v ctags)")" \
    --output-dir simulation/.build/output simulation/.build/TiltAlert
else
  arduino-cli compile --fqbn arduino:avr:uno \
    --output-dir simulation/.build/output simulation/.build/TiltAlert
fi
