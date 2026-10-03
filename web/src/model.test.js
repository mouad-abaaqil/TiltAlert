import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseTrip, visibleEvents, tripStats, locationLabel, toCsv } from './model.js';

const fixture = JSON.parse(readFileSync(new URL('./demo-trip.json', import.meta.url), 'utf8'));

test('demo trip parses and produces the expected incident summary', () => {
  const trip = parseTrip(structuredClone(fixture));
  assert.equal(trip.events.length, 5);
  assert.deepEqual(tripStats(trip.events), { total: 5, critical: 1, impacts: 2, tilts: 3, measured: 3 });
  assert.equal(visibleEvents(trip.events, 'critical').length, 1);
  assert.equal(visibleEvents(trip.events, 'impact').length, 2);
});

test('the last known fix remains explicitly uncertain', () => {
  const trip = parseTrip(structuredClone(fixture));
  assert.match(locationLabel(trip.events[2]), /lieu de l’incident incertain/);
  assert.notEqual(trip.events[2].location.capturedAt, trip.events[2].occurredAt);
});

test('an event cannot claim a measured position from an earlier fix', () => {
  const invalid = structuredClone(fixture);
  invalid.events[0].location.capturedAt = '2026-09-18T07:10:00Z';
  assert.throws(() => parseTrip(invalid), /position invalide/i);
});

test('CSV keeps location status and escapes quotation marks', () => {
  const trip = parseTrip(structuredClone(fixture));
  trip.events[0].id = 'EV-"001';
  const csv = toCsv(trip.events);
  assert.match(csv, /"EV-""001"/);
  assert.match(csv, /"last_known"/);
  assert.equal(csv.split('\n').length, 6);
});
