#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_bin=$(mktemp "${TMPDIR:-/tmp}/tiltalert-core.XXXXXX")
trap 'rm -f "$test_bin"' EXIT HUP INT TERM

g++ -std=c++11 -Wall -Wextra -Werror -pedantic \
  "$project_dir/tests/test_core.cpp" -o "$test_bin"
"$test_bin"
g++ -std=c++11 -Wall -Wextra -Werror -pedantic \
  -include "$project_dir/tests/arduino_stub.h" -x c++ -fsyntax-only \
  "$project_dir/code/tiltalert.ino"
printf '%s\n' 'Arduino sketch syntax check passed'
