import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './style.css';
import demoTrip from './demo-trip.json';
import { parseTrip, visibleEvents, tripStats, locationLabel, toCsv } from './model.js';

const icons = {
  activity: '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
  map: '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>',
  package: '<path d="m12 2 9 5-9 5-9-5 9-5zM3 7v10l9 5 9-5V7M12 12v10"/>',
  alert: '<path d="m12 2 10 18H2L12 2z"/><path d="M12 9v4m0 4h.01"/>',
  download: '<path d="M12 3v12m-4-4 4 4 4-4M4 17v4h16v-4"/>',
  upload: '<path d="M12 16V4m-4 4 4-4 4 4M4 17v4h16v-4"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  battery: '<rect x="2" y="7" width="18" height="10" rx="2"/><path d="M22 10v4"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="m15 9-2 4-4 2 2-4z"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 1v3m0 16v3M1 12h3m16 0h3"/>'
};
const icon = (name, size = 18) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]}</svg>`;
const asset = filename => `${import.meta.env.BASE_URL}assets/${filename}`;
const clean = value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
const formatTime = iso => new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', hour: '2-digit', minute: '2-digit' }).format(new Date(iso));
const formatDate = iso => new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(iso));
const formatCoords = location => `${location.lat.toFixed(4)}° N, ${location.lon.toFixed(4)}° E`;

let data = parseTrip(demoTrip);
let filter = 'all';
let selectedId = data.events.find(event => event.severity === 'critical')?.id ?? data.events[0]?.id;
let playbackIndex = data.events.length;
let map;
let routeLayer;
let markerLayer;
let selectedLayer;

function shell() {
  document.querySelector('#app').innerHTML = `
    <div class="shell">
      <aside class="sidebar">
        <div class="brand"><img src="${asset('logo.png')}" alt="TiltAlert" /><span class="brand-subtitle">TILTALERT / CONTROL CENTER</span></div>
        <div class="workspace-label">ESPACE DE TRAVAIL <span>↗</span></div>
        <nav aria-label="Navigation principale">
          <a class="nav-item active" href="#dashboard">${icon('activity')} Vue d'ensemble</a>
          <a class="nav-item" href="#map-panel">${icon('map')} Carte du trajet</a>
          <a class="nav-item" href="#events-panel">${icon('alert')} Incidents</a>
          <a class="nav-item" href="#product-panel">${icon('package')} Le produit</a>
        </nav>
        <div class="sidebar-bottom"><div class="sidebar-device"><span class="live-dot"></span><div><strong>TILT-001</strong><small>Balise de démonstration</small></div>${icon('chevron', 16)}</div><p>Une preuve claire pour chaque trajet.</p><div class="mini-stripes" aria-hidden="true"></div></div>
      </aside>
      <main id="dashboard" class="main">
        <header class="topbar"><div class="breadcrumb">WORKSPACE <span>/</span> MONITORING <span>/</span> <strong>VUE D'ENSEMBLE</strong></div><div class="top-actions"><span class="demo-pill"><span></span> MODE DÉMONSTRATION</span><button id="import-button" class="icon-button" aria-label="Importer un journal JSON" title="Importer un journal JSON">${icon('upload')}</button><input id="import-input" type="file" accept="application/json,.json" hidden /></div></header>
        <div class="content">
          <section class="page-head"><div><div class="eyebrow"><span class="eyebrow-line"></span> MISSION CONTROL / 01</div><h1>La vérité du trajet<span class="yellow">.</span></h1><p>Chaque mouvement compte. Voyez ce qui s'est passé, quand et avec quelle certitude.</p></div><button id="export-button" class="primary-button">${icon('download', 17)} Exporter le rapport</button></section>
          <section class="notice" role="note">${icon('info', 17)} <span><strong>Scénario simulé.</strong> Les valeurs, événements et positions affichés servent à présenter le produit TiltAlert. Le prototype Arduino actuel ne mesure pas ces données.</span></section>
          <section class="mission-card"><div class="mission-main"><span class="section-kicker">DOSSIER TRAJET <span class="kicker-dot"></span> <span id="mission-id"></span></span><h2 id="mission-name"></h2><p id="cargo"></p><div class="route-names"><span id="origin"></span><span class="route-line"><i></i><i></i></span><span id="destination"></span></div></div><div class="mission-meta"><div><small>STATUT DU TRAJET</small><strong class="status-complete">● Terminé</strong></div><div><small>DATE</small><strong id="mission-date"></strong></div><div><small>BALISE</small><strong id="device-id"></strong></div><div><small>DERNIER FIX GNSS</small><strong id="last-position"></strong></div></div></section>
          <section id="stats" class="stats-grid" aria-label="Résumé du trajet"></section>
          <div class="dashboard-grid"><section id="map-panel" class="panel map-panel"><div class="panel-heading"><div><span class="section-kicker">VISUALISATION / 02</span><h2>Carte du trajet</h2></div><div class="map-legend"><span><i class="legend-dot measured"></i> Position mesurée</span><span><i class="legend-dot uncertain"></i> Dernière position connue</span></div></div><div id="map" role="img" aria-label="Carte interactive du trajet et de ses incidents"></div><div class="map-footer"><div>${icon('target', 16)} <span id="map-note"></span></div><button id="reset-map" class="text-button">Voir tout le trajet ↗</button></div></section>
          <section id="events-panel" class="panel events-panel"><div class="panel-heading"><div><span class="section-kicker">JOURNAL / 03</span><h2>Incidents <span id="event-count" class="count-badge"></span></h2></div></div><div class="filters" role="group" aria-label="Filtrer les incidents"><button data-filter="all" class="filter active">Tous</button><button data-filter="impact" class="filter">Chocs</button><button data-filter="tilt" class="filter">Inclinaisons</button><button data-filter="critical" class="filter">Critiques</button></div><div id="event-list" class="event-list"></div></section></div>
          <section class="playback-panel"><div class="playback-head"><div>${icon('clock', 18)} <strong>Rejouer le trajet</strong><span>Parcourez le journal jusqu'à un incident donné.</span></div><span id="playback-label"></span></div><input id="playback" type="range" min="0" max="5" value="5" aria-label="Nombre d'incidents affichés" /><div class="playback-ends"><span>Départ · <span id="departure-time"></span></span><span>Livraison · <span id="arrival-time"></span></span></div></section>
          <section id="product-panel" class="product-panel"><img src="${asset('tiltalert-trace-in-action.png')}" alt="Concept photoréaliste de la balise TiltAlert fixée à une caisse de transport" /><div class="product-overlay"><span class="section-kicker">CONCEPT PRODUIT / 04</span><h2>Une balise.<br />Des faits.</h2><p>Un boîtier et une carte nRF9151 étudiés en CAO paramétrique, avec quatre planches techniques A3 et des cotes provisoires.</p><div class="product-links"><a href="${asset('tiltalert-trace-plans-A3.pdf')}" target="_blank" rel="noopener">Plans techniques A3 ${icon('chevron', 17)}</a><a href="${asset('tiltalert-trace-parts.svg')}" target="_blank" rel="noopener">Vue éclatée ${icon('chevron', 17)}</a></div></div></section>
          <footer><span>TILTALERT <b>© 2026</b></span><span>CONCEPT OPEN SOURCE · DETECT / ALERT / PROTECT</span></footer>
        </div>
      </main>
    </div>`;
  document.querySelector('#import-button').addEventListener('click', () => document.querySelector('#import-input').click());
  document.querySelector('#import-input').addEventListener('change', importFile);
  document.querySelector('#export-button').addEventListener('click', exportReport);
  document.querySelector('#reset-map').addEventListener('click', fitRoute);
  document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    document.querySelectorAll('.filter').forEach(item => item.classList.toggle('active', item === button));
    renderEvents();
  }));
  document.querySelector('#playback').addEventListener('input', event => {
    playbackIndex = Number(event.target.value);
    renderEvents();
  });
}

function renderDetails() {
  const { trip } = data;
  document.querySelector('#mission-id').textContent = trip.id;
  document.querySelector('#mission-name').textContent = trip.name;
  document.querySelector('#cargo').textContent = trip.cargo || 'Chargement sensible';
  document.querySelector('#origin').textContent = trip.origin || 'Départ';
  document.querySelector('#destination').textContent = trip.destination || 'Arrivée';
  document.querySelector('#mission-date').textContent = formatDate(trip.startedAt);
  document.querySelector('#device-id').textContent = trip.deviceId || '—';
  document.querySelector('#last-position').textContent = trip.lastPosition ? `${formatCoords(trip.lastPosition)} · ${formatTime(trip.lastPosition.capturedAt)}` : 'Non disponible';
  document.querySelector('#departure-time').textContent = formatTime(trip.startedAt);
  document.querySelector('#arrival-time').textContent = formatTime(trip.endedAt);
  document.querySelector('#playback').max = data.events.length;
  document.querySelector('#playback').value = playbackIndex;
  const stats = tripStats(data.events);
  document.querySelector('#stats').innerHTML = `
    <article class="stat-card"><div class="stat-icon yellow-bg">${icon('activity', 21)}</div><span>ÉVÉNEMENTS</span><strong>${stats.total.toString().padStart(2, '0')}</strong><small>Sur ce trajet</small></article>
    <article class="stat-card"><div class="stat-icon red-bg">${icon('alert', 21)}</div><span>CRITIQUES</span><strong>${stats.critical.toString().padStart(2, '0')}</strong><small>Contrôle recommandé</small></article>
    <article class="stat-card"><div class="stat-icon gray-bg">${icon('target', 21)}</div><span>LOCALISÉS</span><strong>${stats.measured}/${stats.total}</strong><small>Au moment de l'incident</small></article>
    <article class="stat-card"><div class="stat-icon gray-bg">${icon('battery', 21)}</div><span>BATTERIE SIMULÉE</span><strong>${Number.isFinite(trip.batteryPercent) ? trip.batteryPercent + '%' : '—'}</strong><small>Fin du trajet</small></article>`;
  document.querySelector('#map-note').textContent = `${stats.measured} positions mesurées sur ${stats.total} événements · les autres points indiquent la dernière position connue.`;
}

function renderEvents() {
  const cutoff = playbackIndex === 0 ? Date.parse(data.trip.startedAt) : Date.parse(data.events[playbackIndex - 1]?.occurredAt || data.trip.endedAt);
  const allVisible = visibleEvents(data.events, 'all', cutoff);
  const shown = visibleEvents(data.events, filter, cutoff).reverse();
  document.querySelector('#event-count').textContent = shown.length;
  document.querySelector('#playback-label').textContent = playbackIndex === data.events.length ? 'Trajet complet' : `${playbackIndex} / ${data.events.length} événements`;
  document.querySelector('#event-list').innerHTML = shown.length ? shown.map(event => `
    <button class="event-card ${event.id === selectedId ? 'selected' : ''}" data-id="${clean(event.id)}">
      <span class="event-rail"><i class="event-symbol ${event.severity}">${event.type === 'impact' ? '!' : '↗'}</i><i class="rail-line"></i></span>
      <span class="event-body"><span class="event-top"><strong>${clean(event.title)}</strong><time datetime="${clean(event.occurredAt)}">${formatTime(event.occurredAt)}</time></span><span class="event-detail">${clean(event.detail)}</span><span class="event-bottom"><span class="severity ${event.severity}">${event.severity === 'critical' ? 'CRITIQUE' : event.severity === 'medium' ? 'MODÉRÉ' : 'LÉGER'}</span><span class="location-chip ${event.location.status}">${event.location.status === 'measured' ? '● GPS MESURÉ' : event.location.status === 'last_known' ? '◌ DERNIÈRE POSITION' : '— INDISPONIBLE'}</span></span></span>
    </button>`).join('') : '<div class="empty-state">Aucun incident pour ce filtre et cette étape du trajet.</div>';
  document.querySelectorAll('.event-card').forEach(card => card.addEventListener('click', () => selectEvent(card.dataset.id)));
  drawMarkers(allVisible);
}

function selectEvent(id) {
  selectedId = id;
  const event = data.events.find(item => item.id === id);
  renderEvents();
  if (!event) return;
  if (event.location.status !== 'unavailable') {
    map.flyTo([event.location.lat, event.location.lon], 10, { duration: 0.6 });
    selectedLayer?.openPopup();
  }
}

function initMap() {
  map = L.map('map', { zoomControl: false, scrollWheelZoom: false });
  L.control.zoom({ position: 'bottomright' }).addTo(map);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map);
  routeLayer = L.polyline(data.trip.route, { color: '#eabf23', weight: 4, opacity: .85, dashArray: '8 8' }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  fitRoute();
}

function fitRoute() {
  if (routeLayer) map.fitBounds(routeLayer.getBounds().pad(.16), { animate: true });
}

function drawMarkers(events) {
  if (!map) return;
  markerLayer.clearLayers();
  selectedLayer = null;
  events.forEach(event => {
    const loc = event.location;
    if (loc.status === 'unavailable') return;
    const isSelected = event.id === selectedId;
    const marker = L.marker([loc.lat, loc.lon], {
      icon: L.divIcon({ className: `event-marker ${event.severity} ${loc.status} ${isSelected ? 'selected' : ''}`, html: `<span>${event.type === 'impact' ? '!' : '↗'}</span>`, iconSize: [32, 32], iconAnchor: [16, 16] })
    }).addTo(markerLayer);
    marker.bindPopup(`<div class="map-popup"><span class="popup-kicker">${clean(event.id)} · ${formatTime(event.occurredAt)}</span><strong>${clean(event.title)}</strong><span>${clean(locationLabel(event))}</span>${loc.status === 'measured' ? `<small>Précision déclarée : ±${loc.accuracyM} m · ${clean(formatCoords(loc))}</small>` : `<small>Fix du ${formatTime(loc.capturedAt)} · ${clean(formatCoords(loc))}</small>`}</div>`);
    marker.on('click', () => { selectedId = event.id; renderEvents(); });
    if (isSelected) selectedLayer = marker;
  });
}

function download(filename, contents, type) {
  const url = URL.createObjectURL(new Blob([contents], { type }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportReport() {
  const prefix = data.trip.id.replace(/[^a-zA-Z0-9_-]/g, '_');
  download(`${prefix}-incidents.csv`, '\uFEFF' + toCsv(data.events), 'text/csv;charset=utf-8');
}

async function importFile(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const parsed = parseTrip(JSON.parse(await file.text()));
    data = parsed;
    filter = 'all';
    selectedId = data.events[0]?.id;
    playbackIndex = data.events.length;
    document.querySelectorAll('.filter').forEach(button => button.classList.toggle('active', button.dataset.filter === 'all'));
    map.removeLayer(routeLayer);
    routeLayer = L.polyline(data.trip.route, { color: '#eabf23', weight: 4, opacity: .85, dashArray: '8 8' }).addTo(map);
    renderDetails();
    renderEvents();
    fitRoute();
  } catch (error) {
    alert(`Import impossible : ${error.message}`);
  } finally {
    event.target.value = '';
  }
}

shell();
renderDetails();
initMap();
renderEvents();
