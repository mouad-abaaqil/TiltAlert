import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import {
  avrInstruction, CPU, AVRIOPort, AVRTimer, AVRUSART, PinState,
  portBConfig, portCConfig, portDConfig,
  timer0Config, timer1Config, timer2Config, usart0Config,
} from 'avr8js';

const here = dirname(fileURLToPath(import.meta.url));
const hexPath = resolve(here, '.build/output/TiltAlert.ino.hex');
const hex = readFileSync(hexPath, 'utf8');

// Decode the actual Arduino CLI Intel HEX image into the Uno's program flash.
const bytes = new Uint8Array(0x8000 * 2);
let addressBase = 0;
for (const line of hex.trim().split(/\r?\n/)) {
  assert.ok(line.startsWith(':'), 'Invalid Intel HEX record');
  const record = Buffer.from(line.slice(1), 'hex');
  assert.equal(record.reduce((sum, value) => sum + value, 0) & 255, 0, 'Intel HEX checksum');
  const size = record[0];
  const addr = (record[1] << 8) | record[2];
  const type = record[3];
  if (type === 0) bytes.set(record.subarray(4, 4 + size), addressBase + addr);
  if (type === 4) addressBase = ((record[4] << 8) | record[5]) << 16;
}
const cpu = new CPU(new Uint16Array(bytes.buffer));
new AVRTimer(cpu, timer0Config);
new AVRTimer(cpu, timer1Config);
new AVRTimer(cpu, timer2Config);
const portB = new AVRIOPort(cpu, portBConfig);
new AVRIOPort(cpu, portCConfig);
const portD = new AVRIOPort(cpu, portDConfig);
const usart = new AVRUSART(cpu, usart0Config, 16e6);

// D2=PD2: external KY-020 output with pull-down; D12=PB4: INPUT_PULLUP button.
portD.setPin(2, false);
portB.setPin(4, true);

let serialBuffer = '';
const serial = [];
usart.onByteTransmit = (value) => {
  serialBuffer += String.fromCharCode(value);
  if (serialBuffer.endsWith('\n')) {
    serial.push(JSON.parse(serialBuffer));
    serialBuffer = '';
  }
};

const timeline = [];
const ms = () => cpu.cycles / 16000;
function runUntil(targetMs) {
  const targetCycles = Math.round(targetMs * 16000);
  assert.ok(targetCycles >= cpu.cycles);
  while (cpu.cycles < targetCycles) {
    avrInstruction(cpu);
    cpu.tick();
  }
}
function snapshot(label) {
  const row = {
    label, simulated_ms: Math.round(ms()), tilt_D2: Boolean(cpu.data[0x29] & (1 << 2)),
    reset_D12: !(cpu.data[0x23] & (1 << 4)),
    led_D13: portB.pinState(5) === PinState.High,
    buzzer_D3: portD.pinState(3) === PinState.High,
    latest_serial: serial.at(-1) ?? null,
  };
  timeline.push(row);
  return row;
}
function assertOutputs(active) {
  assert.equal(portB.pinState(5) === PinState.High, active, 'D13 LED');
  assert.equal(portD.pinState(3) === PinState.High, active, 'D3 buzzer');
}

runUntil(100);
assert.deepEqual(serial.map(item => item.event), ['ready']);
assertOutputs(false);
snapshot('boot');

// A 10 ms contact spike is shorter than the 40 ms debounce window.
portD.setPin(2, true);
runUntil(110);
portD.setPin(2, false);
runUntil(170);
assert.equal(serial.length, 1, '10 ms contact chatter ignored');
snapshot('contact chatter ignored');

for (let count = 1; count <= 5; count++) {
  portD.setPin(2, true);
  runUntil(ms() + 100);
  assert.equal(serial.filter(item => item.event === 'tilt').length, count);
  assert.equal(serial.at(-1).count, count);
  assertOutputs(count === 5);
  snapshot(`tilt ${count}`);
  portD.setPin(2, false);
  runUntil(ms() + 80);
}
assert.equal(serial.filter(item => item.event === 'alarm').length, 1);
assertOutputs(true);
snapshot('alarm latched');

// One confirmed press on D12 clears the latched alarm.
portB.setPin(4, false);
runUntil(ms() + 130);
assert.equal(serial.at(-1).event, 'reset');
assert.equal(serial.at(-1).count, 0);
assertOutputs(false);
snapshot('button reset');
portB.setPin(4, true);
runUntil(ms() + 80);

const result = {
  simulator: 'avr8js',
  mcu: 'ATmega328P / Arduino Uno / 16 MHz',
  firmware: 'Arduino CLI compiled code/tiltalert.ino + code/TiltAlertCore.h',
  hex_sha256: createHash('sha256').update(hex).digest('hex'),
  assertions: 'PASS: chatter ignored; exactly five tilt events; D13 and D3 HIGH only at alarm; reset clears outputs',
  timeline,
  serial,
};
const resultPath = resolve(here, 'evidence/avr8js-run.json');
mkdirSync(dirname(resultPath), { recursive: true });
writeFileSync(resultPath, JSON.stringify(result, null, 2) + '\n');
console.log(`PASS: ${serial.length} serial events, ${timeline.length} snapshots, firmware ${result.hex_sha256.slice(0, 12)}…`);
console.log(`Evidence: ${resultPath}`);
