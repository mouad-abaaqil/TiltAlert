export const severityOrder = { critical: 3, medium: 2, low: 1 };

export function parseTrip(data) {
  if (!data || data.schemaVersion !== 1 || !data.trip || !Array.isArray(data.events)) {
    throw new Error('Format invalide : schemaVersion 1, trip et events sont requis.');
  }
  const trip = data.trip;
  if (!trip.id || !trip.name || !validDate(trip.startedAt) || !validDate(trip.endedAt) ||
      Date.parse(trip.startedAt) > Date.parse(trip.endedAt) ||
      !Array.isArray(trip.route) || trip.route.length < 2 ||
      !trip.route.every(point => validCoordinates(point[0], point[1]))) {
    throw new Error('Trajet invalide : identifiant, nom et coordonnées sont requis.');
  }
  if (trip.lastPosition && (!validCoordinates(trip.lastPosition.lat, trip.lastPosition.lon) ||
      !validDate(trip.lastPosition.capturedAt) ||
      Date.parse(trip.lastPosition.capturedAt) > Date.parse(trip.endedAt) ||
      !Number.isFinite(trip.lastPosition.accuracyM) || trip.lastPosition.accuracyM < 0)) {
    throw new Error('Dernière position du trajet invalide.');
  }
  const ids = new Set();
  const events = data.events.map(event => {
    if (!event.id || ids.has(event.id) || !['impact', 'tilt'].includes(event.type) ||
        !Object.hasOwn(severityOrder, event.severity) || !validDate(event.occurredAt) ||
        typeof event.title !== 'string' || typeof event.detail !== 'string' ||
        !Number.isFinite(event.value) || !['g', '°'].includes(event.unit)) {
      throw new Error(`Événement invalide : ${event.id || 'sans identifiant'}.`);
    }
    ids.add(event.id);
    const loc = event.location;
    if (!loc || !['measured', 'last_known', 'unavailable'].includes(loc.status)) {
      throw new Error(`Position invalide pour ${event.id}.`);
    }
    if (loc.status !== 'unavailable' &&
        (!validCoordinates(loc.lat, loc.lon) || !validDate(loc.capturedAt) ||
         !Number.isFinite(loc.accuracyM) || loc.accuracyM < 0 ||
         Date.parse(loc.capturedAt) > Date.parse(event.occurredAt) ||
         (loc.status === 'measured' && loc.capturedAt !== event.occurredAt))) {
      throw new Error(`Mesure de position invalide pour ${event.id}.`);
    }
    return event;
  });
  return { ...data, events: events.sort((a, b) => Date.parse(a.occurredAt) - Date.parse(b.occurredAt)) };
}

function validDate(value) {
  return typeof value === 'string' && Number.isFinite(Date.parse(value));
}

function validCoordinates(lat, lon) {
  return Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
}

export function visibleEvents(events, filter, until = Infinity) {
  return events.filter(event =>
    Date.parse(event.occurredAt) <= until &&
    (filter === 'all' || event.type === filter || event.severity === filter)
  );
}

export function tripStats(events) {
  return {
    total: events.length,
    critical: events.filter(event => event.severity === 'critical').length,
    impacts: events.filter(event => event.type === 'impact').length,
    tilts: events.filter(event => event.type === 'tilt').length,
    measured: events.filter(event => event.location.status === 'measured').length
  };
}

export function locationLabel(event) {
  if (event.location.status === 'unavailable') return 'Position indisponible';
  if (event.location.status === 'measured') return 'Position mesurée lors de l’incident';
  return 'Dernière position connue — lieu de l’incident incertain';
}

export function toCsv(events) {
  const headings = ['id', 'type', 'severity', 'occurredAt', 'value', 'unit', 'locationStatus', 'lat', 'lon', 'locationCapturedAt', 'accuracyM'];
  const rows = events.map(event => [event.id, event.type, event.severity, event.occurredAt, event.value,
    event.unit, event.location.status, event.location.lat ?? '', event.location.lon ?? '',
    event.location.capturedAt ?? '', event.location.accuracyM ?? '']);
  return [headings, ...rows].map(row => row.map(cell => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n');
}
