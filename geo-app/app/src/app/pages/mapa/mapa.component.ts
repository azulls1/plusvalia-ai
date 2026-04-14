// src/app/pages/mapa/mapa.component.ts - Componente principal del mapa
import { Component, OnInit, OnDestroy } from '@angular/core'; // decoradores de Angular
import { CommonModule } from '@angular/common'; // módulo común para directivas básicas
import { FormsModule } from '@angular/forms'; // módulo para ngModel y formularios
import * as L from 'leaflet'; // librería Leaflet para mapas
import './leaflet-extensions'; // importa extensiones de Leaflet (heat y markercluster)
import { ApiService } from '../../services/api.service'; // servicio API
import { MapStateService } from '../../services/map-state.service'; // servicio de estado del mapa
import { AnalyticsService } from '../../services/analytics.service'; // servicio de analytics
import { CircuitBreakerService } from '../../services/circuit-breaker.service'; // servicio circuit breaker
import { FiltersPanelComponent } from '../../components/filters-panel/filters-panel.component'; // componente de filtros
import { AddressSearchComponent } from '../../components/address-search/address-search.component'; // componente de búsqueda
import { AdvancedFiltersComponent, AdvancedFilters } from '../../components/advanced-filters/advanced-filters.component'; // componente de filtros avanzados
import { FileUploadComponent } from '../../components/file-upload/file-upload.component'; // componente de subida de archivos
import { Tile, Amenity, HeatmapPoint, CityStats, AmenityFilters } from '../../models/interfaces'; // interfaces tipadas

// Declaración de tipos para extensiones de Leaflet (complementa src/types/*.d.ts)
declare module 'leaflet' {
  function heatLayer(latlngs: [number, number, number][], options?: HeatMapOptions): HeatLayer;
  function markerClusterGroup(options?: MarkerClusterGroupOptions): MarkerClusterGroup;
}

// Lista de los 32 estados de México (shared constant)
const MEXICAN_STATES: string[] = [
  'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche',
  'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima',
  'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo',
  'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca',
  'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa',
  'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán',
  'Zacatecas'
];

@Component({ // decorador del componente
  selector: 'app-mapa', // selector HTML
  standalone: true, // componente standalone
  imports: [CommonModule, FormsModule, FiltersPanelComponent, AddressSearchComponent, AdvancedFiltersComponent, FileUploadComponent], // importa componentes y módulos
  templateUrl: './mapa.component.html', // ruta del template HTML
  styleUrls: ['./mapa.component.css'] // ruta de estilos CSS
})
export class MapaComponent implements OnInit, OnDestroy { // clase del componente implementa OnInit, OnDestroy
  private map!: L.Map; // instancia del mapa Leaflet
  private heatLayer!: L.HeatLayer; // capa de heatmap de tiles (modo precios)
  private markersLayer!: L.MarkerClusterGroup; // grupo de clusters de marcadores
  private predictionsMarkersLayer!: L.LayerGroup; // capa de circle markers para predicciones
  private statesLayer!: L.GeoJSON; // capa GeoJSON de estados mexicanos
  private searchMarker: L.Marker | null = null; // marcador de búsqueda
  private legendControl: L.Control | null = null; // control de leyenda del mapa
  private statesGeoData: GeoJSON.FeatureCollection | null = null; // datos GeoJSON cacheados

  // Single source of truth for map interaction mode
  mapMode: 'country' | 'state' = 'country';
  private activeStateLayer: L.Path | null = null; // currently selected state layer in state mode
  private stateLabelsLayer!: L.LayerGroup; // capa de labels centrados en cada estado
  private stateScores: Map<string, { avg: number; count: number }> = new Map(); // scores promedio por estado

  tiles: Tile[] = []; // array de tiles de la grilla
  amenities: Amenity[] = []; // array de amenidades
  predictions: HeatmapPoint[] = []; // array de predicciones ML (todas)
  filteredPredictions: HeatmapPoint[] = []; // array de predicciones filtradas
  loading = false; // flag de carga
  message = ''; // mensaje para el usuario
  messageType: 'success' | 'error' | 'info' = 'info'; // tipo de mensaje

  // Modo de visualización
  currentYear = new Date().getFullYear();
  viewMode: 'tiles' | 'predictions' = 'predictions';
  selectedCity: string = '';
  selectedState: string = '';
  citiesStats: CityStats[] = [];
  summaryPopup: string = '';
  summaryPopupTitle: string = '';
  summaryPopupContent: string = '';

  // Lista de los 32 estados de México (referencia a constante compartida)
  mexicanStates: string[] = MEXICAN_STATES;

  // Timer management
  private messageTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private apiService: ApiService,
    private mapState: MapStateService,
    private analytics: AnalyticsService,
    private circuitBreaker: CircuitBreakerService
  ) {}

  ngOnInit(): void {
    this.analytics.trackPageView('/mapa');
    this.initMap();
    this.loadData();
  }

  ngOnDestroy(): void {
    // Clear timers
    if (this.messageTimer) {
      clearTimeout(this.messageTimer);
      this.messageTimer = null;
    }

    // Clear all layers
    if (this.markersLayer) this.markersLayer.clearLayers();
    if (this.predictionsMarkersLayer) this.predictionsMarkersLayer.clearLayers();
    if (this.stateLabelsLayer) this.stateLabelsLayer.clearLayers();
    if (this.statesLayer) this.statesLayer.clearLayers();

    // Null out cached GeoJSON data
    this.statesGeoData = null;

    // Destroy map
    if (this.map) {
      this.map.off();
      this.map.remove();
    }
  }

  // Inicializa el mapa Leaflet
  private initMap(): void {
    // Configurar iconos de Leaflet (fix para marker-shadow.png)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Leaflet icon URL workaround
    delete (L.Icon.Default.prototype as any)._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
    });

    this.map = L.map('map', { preferCanvas: true }).setView([23.6, -102.5], 5);

    // Capa base CartoDB Positron (limpia, profesional)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
    }).addTo(this.map);

    // Capas de heatmap (ocultas, se usan solo en modo tiles)
    this.heatLayer = L.heatLayer([], {
      radius: 25, blur: 15, maxZoom: 10, max: 1.0,
      gradient: { 0.0: 'blue', 0.5: 'yellow', 1.0: 'red' }
    });
    this.predictionsMarkersLayer = L.layerGroup();

    // Capa de labels de estado (se agrega encima del GeoJSON)
    this.stateLabelsLayer = L.layerGroup().addTo(this.map);

    // Cargar GeoJSON de estados mexicanos (choropleth + click)
    this.loadStatesGeoJSON();

    // Clusters de amenidades — SIEMPRE visibles
    this.markersLayer = L.markerClusterGroup({
      maxClusterRadius: 50,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: true,
      zoomToBoundsOnClick: true
    });
    this.map.addLayer(this.markersLayer);

    // Leyenda
    this.addHeatmapLegend();

    // Zoom-based auto-transition: state -> country when zooming out
    this.map.on('zoomend', () => {
      if (this.mapMode === 'state' && this.map.getZoom() <= 5) {
        this.setMapMode('country');
      }
    });

    // Click en el mapa para predicciones cercanas
    this.map.on('click', (e: L.LeafletMouseEvent) => {
      if (this.viewMode === 'predictions') {
        this.showNearbyPredictions(e.latlng.lat, e.latlng.lng);
      }
    });
  }

  // Carga GeoJSON de estados y configura choropleth + interacciones
  private async loadStatesGeoJSON(): Promise<void> {
    try {
      const response = await fetch('assets/mexico-states.geojson');
      this.statesGeoData = await response.json();

      this.statesLayer = L.geoJSON(this.statesGeoData, {
        style: () => this.getEmptyStateStyle(),
        onEachFeature: (feature, layer) => {
          const stateName = feature.properties?.['name'] || 'Estado';
          const stateId = feature.properties?.['id'] || feature.properties?.['name'] || '';

          // --- HOVER: tooltip only, NO color changes ---
          layer.on('mouseover', () => {
            const scoreData = this.stateScores.get(stateId);
            const avg = scoreData ? (scoreData.avg * 100).toFixed(1) : '--';
            const count = scoreData ? scoreData.count.toLocaleString() : '0';
            const potential = scoreData
              ? (scoreData.avg >= 0.7 ? 'Alto' : scoreData.avg >= 0.4 ? 'Medio' : 'Bajo')
              : '--';
            const color = scoreData ? this.getChoroplethColor(scoreData.avg) : '#94a3b8';

            layer.bindTooltip(`
              <div style="min-width:180px;font-family:'DM Sans',sans-serif;padding:2px;">
                <div style="font-size:14px;font-weight:700;color:#1e3a5f;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                  <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};"></span>
                  ${stateName}
                </div>
                <div style="font-size:12px;color:#374151;line-height:1.6;">
                  <div><strong>Score promedio:</strong> ${avg}/100</div>
                  <div><strong>Potencial:</strong> ${potential}</div>
                  <div><strong>Predicciones:</strong> ${count}</div>
                </div>
              </div>
            `, {
              sticky: true, className: 'state-tooltip-choropleth', direction: 'top', offset: [0, -10],
            }).openTooltip();
            // No style changes on hover — tooltip only
          });

          layer.on('mouseout', () => {
            layer.closeTooltip();
            layer.unbindTooltip();
            // No style restoration needed — we never changed styles on hover
          });

          // --- CLICK: transition to state mode ---
          layer.on('click', (e) => {
            L.DomEvent.stopPropagation(e);
            this.selectState(feature, layer as L.Path);
          });
        }
      }).addTo(this.map);

    } catch (error) {
      console.error('Error cargando GeoJSON de estados:', error);
    }
  }

  // Selects a state: enters state mode and shows city markers
  private selectState(feature: GeoJSON.Feature, layer: L.Path): void {
    const stateName = feature.properties?.['name'] || 'Estado';
    const bounds = (layer as unknown as L.Polygon).getBounds();

    // Animate zoom to the state
    this.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8, animate: true, duration: 0.6 });

    if (this.mapMode === 'state') {
      // Already in state mode — switching states: reset previous border and clear markers
      if (this.activeStateLayer) {
        this.activeStateLayer.setStyle({ fillColor: 'transparent', fillOpacity: 0, color: '#cbd5e1', weight: 0.5, opacity: 0.3 });
      }
      this.predictionsMarkersLayer.clearLayers();
      this.map.closePopup();
    } else {
      // Enter state mode from country (clears fills, labels)
      this.setMapMode('state');
    }

    // Mark this specific state with a subtle border
    this.activeStateLayer = layer;
    layer.setStyle({ fillColor: 'transparent', fillOpacity: 0, color: '#2563eb', weight: 2, opacity: 0.8 });

    // Filter predictions inside the real polygon geometry
    const geom = feature.geometry;
    const statePoints = this.filteredPredictions.filter(p => {
      if (!bounds.contains(L.latLng(p[0], p[1]))) return false;
      return this.pointInGeoJSON(p[1], p[0], geom);
    });
    this.showStatePoints(statePoints, bounds);

    // Show info popup at state center
    const avgScore = statePoints.length > 0
      ? (statePoints.reduce((sum, p) => sum + p[2], 0) / statePoints.length * 100).toFixed(1) : '0';
    const color = statePoints.length > 0
      ? this.getChoroplethColor(statePoints.reduce((sum, p) => sum + p[2], 0) / statePoints.length) : '#94a3b8';

    L.popup()
      .setLatLng(bounds.getCenter())
      .setContent(`
        <div style="min-width:220px;font-family:'DM Sans',sans-serif;">
          <h5 style="margin:0 0 8px;font-size:15px;font-weight:700;color:#1e3a5f;border-bottom:2px solid ${color};padding-bottom:6px;">
            ${stateName}
          </h5>
          <p style="margin:4px 0;font-size:13px;"><strong>Predicciones:</strong> ${statePoints.length.toLocaleString()}</p>
          <p style="margin:4px 0;font-size:13px;"><strong>Score promedio:</strong> ${avgScore}/100</p>
          <p style="margin:6px 0 0;font-size:11px;color:#6b7280;">Click en el mapa para ver prediccion cercana</p>
        </div>
      `)
      .openOn(this.map);

    this.showMessage(`${stateName} — ${statePoints.length.toLocaleString()} predicciones`, 'info');
  }

  // Single method that controls ALL map mode transitions
  setMapMode(mode: 'country' | 'state'): void {
    if (this.mapMode === mode) return;
    this.mapMode = mode;

    if (mode === 'country') {
      // --- TRANSITION: State -> Country ---
      // 1. Clear city markers
      this.predictionsMarkersLayer.clearLayers();
      if (this.map.hasLayer(this.predictionsMarkersLayer)) {
        this.map.removeLayer(this.predictionsMarkersLayer);
      }

      // 2. Restore choropleth fills on all states
      this.applyChoroplethStyles();
      this.activeStateLayer = null;

      // 3. Restore state labels
      if (!this.map.hasLayer(this.stateLabelsLayer)) {
        this.map.addLayer(this.stateLabelsLayer);
      }

      // 4. Close any open popup
      this.map.closePopup();

    } else {
      // --- TRANSITION: Country -> State ---
      // 1. Remove state labels
      if (this.map.hasLayer(this.stateLabelsLayer)) {
        this.map.removeLayer(this.stateLabelsLayer);
      }

      // 2. Make ALL state fills transparent (white base map shows through)
      if (this.statesLayer) {
        this.statesLayer.eachLayer((l) => {
          (l as L.Path).setStyle({
            fillColor: 'transparent',
            fillOpacity: 0,
            color: '#cbd5e1',
            weight: 0.5,
            opacity: 0.3,
          });
        });
      }

      // 3. Clear old markers (selectState will add new ones)
      this.predictionsMarkersLayer.clearLayers();
    }
  }

  // Calcula average scores per state from predictions data and updates choropleth
  private updateChoropleth(): void {
    this.stateScores.clear();

    // Esperar a que el GeoJSON esté listo (puede tardar si aún carga), max 10 retries
    let retries = 0;
    const maxRetries = 10;
    const tryUpdate = () => {
      if (!this.statesGeoData || !this.statesLayer) {
        retries++;
        if (retries >= maxRetries) {
          console.warn('updateChoropleth: max retries reached, GeoJSON not loaded');
          return;
        }
        setTimeout(() => tryUpdate(), 500);
        return;
      }
      this.loadChoroplethData();
    };
    tryUpdate();
  }

  private loadChoroplethData(): void {
    this.apiService.getStatsByState()
      .then(data => {
        const statesData = data.states || {};

        for (const feature of this.statesGeoData!.features) {
          const geoId = feature.properties?.['id'] || '';
          const d = statesData[geoId];
          if (d && d.count > 0) {
            this.stateScores.set(geoId, {
              avg: d.avg_score / 100,
              count: d.count,
            });
          }
        }

        // Aplicar estilo a cada layer individualmente (más confiable que setStyle con función)
        if (this.statesLayer) {
          this.statesLayer.eachLayer((layer) => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const feature = (layer as any).feature as GeoJSON.Feature;
            if (feature) {
              (layer as L.Path).setStyle(this.getChoroplethStyle(feature));
            }
          });
        }
        this.updateStateLabels();
      })
      .catch(err => {
        console.error('Error loading state stats:', err);
      });
  }

  // Aplica estilos coropléticos a cada layer individualmente
  private applyChoroplethStyles(): void {
    if (!this.statesLayer) return;
    this.statesLayer.eachLayer((layer) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const feature = (layer as any).feature as GeoJSON.Feature;
      if (feature) {
        (layer as L.Path).setStyle(this.getChoroplethStyle(feature));
      }
    });
  }

  // Returns Leaflet style for a state feature based on its score
  private getChoroplethStyle(feature?: GeoJSON.Feature): L.PathOptions {
    if (!feature) return this.getEmptyStateStyle();

    const stateId = feature.properties?.['id'] || feature.properties?.['name'] || '';
    const scoreData = this.stateScores.get(stateId);

    if (!scoreData) return this.getEmptyStateStyle();

    const fillColor = this.getChoroplethColor(scoreData.avg);

    return {
      fillColor,
      fillOpacity: 0.55,
      color: '#ffffff',
      weight: 1.5,
      opacity: 0.8,
    };
  }

  // Neutral style for states with no data
  private getEmptyStateStyle(): L.PathOptions {
    return {
      fillColor: '#e2e8f0',
      fillOpacity: 0.25,
      color: '#94a3b8',
      weight: 1,
      opacity: 0.5,
    };
  }

  // Paleta Forest Design System — calibrada al rango real de scores (55-85)
  private getChoroplethColor(value: number): string {
    // value es 0-1 (score/100). Rango real: ~0.55-0.85
    if (value <= 0.55) return '#c8e6c9';  // verde muy claro — bajo
    if (value <= 0.60) return '#a5d6a7';  // verde claro
    if (value <= 0.65) return '#81c784';  // verde medio
    if (value <= 0.70) return '#66bb6a';  // verde
    if (value <= 0.75) return '#4caf50';  // verde fuerte
    if (value <= 0.80) return '#388e3c';  // verde oscuro
    return '#1b5e20';                     // verde bosque — muy alto
  }

  // Creates DivIcon labels at the center of each state showing name + score
  private updateStateLabels(): void {
    this.stateLabelsLayer.clearLayers();

    if (!this.statesGeoData) return;

    for (const feature of this.statesGeoData.features) {
      const stateId = feature.properties?.['id'] || feature.properties?.['name'] || '';
      const stateName = feature.properties?.['name'] || '';
      const scoreData = this.stateScores.get(stateId);

      // Only show labels for states that have data
      if (!scoreData) continue;

      const scorePercent = Math.round(scoreData.avg * 100);
      const center = L.geoJSON(feature as GeoJSON.Feature).getBounds().getCenter();

      // Abbreviated name for smaller states
      const displayName = stateName.length > 12 ? this.abbreviateStateName(stateName) : stateName;

      const label = L.marker(center, {
        interactive: false,
        icon: L.divIcon({
          className: 'state-label-choropleth',
          html: `<div class="state-label-inner">
                   <span class="state-label-name">${displayName}</span>
                   <span class="state-label-score">${scorePercent}</span>
                 </div>`,
          iconSize: [80, 36],
          iconAnchor: [40, 18],
        }),
      });

      this.stateLabelsLayer.addLayer(label);
    }

    // Show labels layer if not already on map
    if (!this.map.hasLayer(this.stateLabelsLayer)) {
      this.map.addLayer(this.stateLabelsLayer);
    }
  }

  // Abbreviates long state names for map labels
  private abbreviateStateName(name: string): string {
    const abbreviations: Record<string, string> = {
      'Aguascalientes': 'Ags.',
      'Baja California': 'B.C.',
      'Baja California Sur': 'B.C.S.',
      'Coahuila de Zaragoza': 'Coah.',
      'Ciudad de Mexico': 'CDMX',
      'Ciudad de México': 'CDMX',
      'Distrito Federal': 'CDMX',
      'Estado de Mexico': 'Edo. Mex.',
      'Estado de México': 'Edo. Mex.',
      'México': 'Edo. Mex.',
      'Mexico': 'Edo. Mex.',
      'Michoacán de Ocampo': 'Mich.',
      'Michoacan de Ocampo': 'Mich.',
      'Nuevo Leon': 'N.L.',
      'Nuevo León': 'N.L.',
      'Quintana Roo': 'Q. Roo',
      'San Luis Potosi': 'S.L.P.',
      'San Luis Potosí': 'S.L.P.',
      'Veracruz de Ignacio de la Llave': 'Ver.',
    };
    return abbreviations[name] || name.substring(0, 10) + '.';
  }

  // Carga datos iniciales (tiles, amenidades y predicciones)
  async loadData(): Promise<void> {
    this.loading = true;
    this.showMessage('Cargando datos...', 'info');
    const startTime = performance.now();

    try {
      // Todas las llamadas en PARALELO (Promise.allSettled no falla si una falla)
      const [tilesR, amenitiesR, statsR, predsR] = await Promise.allSettled([
        this.apiService.getTiles(5000),
        this.apiService.getAmenities({}),
        this.apiService.getPredictionsStatsByCity(),
        this.apiService.getPredictionsHeatmap(this.selectedCity || undefined, undefined, 5000),
      ]);

      this.tiles = tilesR.status === 'fulfilled' ? tilesR.value : [];
      this.amenities = amenitiesR.status === 'fulfilled' ? amenitiesR.value : [];
      this.citiesStats = (statsR.status === 'fulfilled' ? statsR.value.cities : []) || [];
      this.predictions = predsR.status === 'fulfilled' ? (predsR.value.points || []) : [];
      this.filteredPredictions = [...this.predictions];

      this.analytics.trackPerformance('load_data', performance.now() - startTime);

      // Actualizar UI de una vez
      this.updateMarkers();
      if (this.viewMode === 'tiles') this.updateHeatmap();
      this.updateChoropleth();
      this.addHeatmapLegend();

      this.showMessage(
        `${this.citiesStats.length} ciudades, ${this.predictions.length.toLocaleString()} predicciones`,
        'success'
      );
    } catch (error) {
      console.error('Error cargando datos:', error);
      this.analytics.trackError('load_data_failed', { error: String(error) });
      this.showMessage('Error cargando datos del servidor', 'error');
    } finally {
      this.loading = false;
    }
  }

  // Limpia el cache y recarga los datos
  async clearCache(): Promise<void> {
    this.loading = true;
    this.showMessage('Limpiando cache y recargando datos...', 'info');
    this.apiService.clearCache();
    await this.loadData();
  }

  // Actualiza la capa de heatmap con los tiles (modo precios)
  private updateHeatmap(): void {
    const heatPoints: [number, number, number][] = [];
    const maxPrice = this.tiles.reduce((max, t) => Math.max(max, t.price_m2_avg || 0), 0);

    this.tiles.forEach(tile => {
      if (tile.lat && tile.lon && tile.price_m2_avg) {
        const intensity = tile.price_m2_avg / maxPrice;
        heatPoints.push([tile.lat, tile.lon, intensity]);
      }
    });

    this.heatLayer.setLatLngs(heatPoints);
  }

  // Muestra markers de ciudades dentro del estado seleccionado
  private showStatePoints(statePoints: HeatmapPoint[], bounds: L.LatLngBounds): void {
    this.predictionsMarkersLayer.clearLayers();
    if (!this.map.hasLayer(this.predictionsMarkersLayer)) {
      this.map.addLayer(this.predictionsMarkersLayer);
    }

    // Agrupar puntos por zona (~ciudad) usando grid de 0.1° (~11km)
    const clusters: Map<string, { lat: number; lon: number; scores: number[]; count: number }> = new Map();

    for (const pred of statePoints) {
      const key = `${Math.round(pred[0] * 10) / 10},${Math.round(pred[1] * 10) / 10}`;
      const existing = clusters.get(key);
      if (existing) {
        existing.scores.push(pred[2]);
        existing.count++;
        // Promediar posición para centrar el marker
        existing.lat = (existing.lat * (existing.count - 1) + pred[0]) / existing.count;
        existing.lon = (existing.lon * (existing.count - 1) + pred[1]) / existing.count;
      } else {
        clusters.set(key, { lat: pred[0], lon: pred[1], scores: [pred[2]], count: 1 });
      }
    }

    // Crear marker por cada cluster/ciudad
    clusters.forEach((cluster) => {
      const avgScore = cluster.scores.reduce((a, b) => a + b, 0) / cluster.scores.length;
      const scorePercent = Math.round(avgScore * 100);
      const color = this.getGradientColor(avgScore);
      const potential = avgScore >= 0.7 ? 'Alto' : avgScore >= 0.4 ? 'Medio' : 'Bajo';

      const marker = L.marker([cluster.lat, cluster.lon], {
        bubblingMouseEvents: false,
      });

      marker.bindPopup(`
        <div style="min-width:180px;font-family:'DM Sans',sans-serif;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${color};"></span>
            <strong style="font-size:14px;">Score: ${scorePercent}/100</strong>
          </div>
          <p style="margin:3px 0;font-size:12px;"><strong>Potencial:</strong> ${potential}</p>
          <p style="margin:3px 0;font-size:12px;"><strong>Datos en zona:</strong> ${cluster.count}</p>
          <p style="margin:3px 0;font-size:11px;color:#6b7280;">
            ${cluster.lat.toFixed(4)}, ${cluster.lon.toFixed(4)}
          </p>
        </div>
      `);

      this.predictionsMarkersLayer.addLayer(marker);
    });
  }

  // Ray-casting: verifica si un punto [lon, lat] está dentro de un GeoJSON geometry
  private pointInGeoJSON(lon: number, lat: number, geom: GeoJSON.Geometry): boolean {
    if (geom.type === 'Polygon') {
      return this.pointInPolygon(lon, lat, geom.coordinates);
    } else if (geom.type === 'MultiPolygon') {
      return geom.coordinates.some(poly => this.pointInPolygon(lon, lat, poly));
    }
    return false;
  }

  private pointInPolygon(lon: number, lat: number, rings: number[][][]): boolean {
    // Test contra el anillo exterior (rings[0])
    const ring = rings[0];
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const xi = ring[i][0], yi = ring[i][1];
      const xj = ring[j][0], yj = ring[j][1];
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) {
        inside = !inside;
      }
    }
    return inside;
  }

  // Vuelve a la vista completa del país (quita puntos, restaura choropleth)
  resetToCountryView(): void {
    this.setMapMode('country');
    this.map.setView([23.6, -102.5], 5, { animate: true, duration: 0.8 });
    this.showMessage('Vista nacional', 'info');
  }

  // Obtiene color de gradiente verde-amarillo-rojo
  private getGradientColor(value: number): string {
    // Gradiente: verde (bajo) -> amarillo (medio) -> naranja -> rojo (alto)
    if (value <= 0.25) {
      return '#22c55e'; // verde
    } else if (value <= 0.45) {
      return '#84cc16'; // lima
    } else if (value <= 0.6) {
      return '#eab308'; // amarillo
    } else if (value <= 0.75) {
      return '#f97316'; // naranja
    } else if (value <= 0.9) {
      return '#ef4444'; // rojo
    }
    return '#dc2626'; // rojo fuerte
  }

  // Actualiza los marcadores de amenidades
  private updateMarkers(): void {
    this.markersLayer.clearLayers();

    this.amenities.forEach(amenity => {
      if (amenity.lat && amenity.lon) {
        const marker = L.marker([amenity.lat, amenity.lon]);
        marker.bindPopup(`
          <strong>${amenity.name || 'Sin nombre'}</strong><br>
          Tipo: ${amenity.amenity_type || 'N/A'}<br>
          Ciudad: ${amenity.city || 'N/A'}
        `);
        this.markersLayer.addLayer(marker);
      }
    });
  }

  // Cambia entre modo tiles y modo predicciones
  switchViewMode(mode: 'tiles' | 'predictions'): void {
    this.analytics.trackAction('switch_view_mode', 'map', mode);
    this.viewMode = mode;

    if (mode === 'tiles') {
      // Quitar puntos de predicciones, mostrar heatmap de precios
      this.predictionsMarkersLayer.clearLayers();
      this.map.addLayer(this.heatLayer);
      this.updateHeatmap();
    } else {
      // Modo predicciones: quitar heatmap (puntos aparecen al click en estado)
      this.map.removeLayer(this.heatLayer);
      this.predictionsMarkersLayer.clearLayers();
    }

    this.showMessage(`Modo cambiado a: ${mode === 'tiles' ? 'Precios' : 'Predicciones ML'}`, 'info');
  }

  // Muestra predicciones cercanas al hacer click en el mapa
  async showNearbyPredictions(lat: number, lng: number): Promise<void> {
    try {
      this.loading = true;

      const result = await this.apiService.getPredictionsNearby(lat, lng, 2.0, 10);

      if (result.predictions && result.predictions.length > 0) {
        const nearest = result.predictions[0];

        const popupContent = `
          <div style="min-width: 250px;">
            <h6 style="margin-bottom: 10px; color: #333;">Prediccion ML</h6>
            <div style="border-left: 3px solid ${this.getColorByScore(nearest.plusvalia_score)}; padding-left: 10px;">
              <p style="margin: 5px 0;"><strong>Ciudad:</strong> ${nearest.city}</p>
              <p style="margin: 5px 0;"><strong>Precio/m2:</strong> $${nearest.predicted_price_m2.toLocaleString()}</p>
              <p style="margin: 5px 0;"><strong>Score Plusvalia:</strong> ${nearest.plusvalia_score.toFixed(1)}/100</p>
              <p style="margin: 5px 0;"><strong>Potencial:</strong>
                <span style="font-weight: bold; color: ${this.getColorByPotential(nearest.growth_potential)};">
                  ${nearest.growth_potential.toUpperCase()}
                </span>
              </p>
              <p style="margin: 5px 0; font-size: 0.9em; color: #666;">
                <strong>Distancia:</strong> ${nearest.distance_km} km
              </p>
            </div>
            ${result.predictions.length > 1 ?
              `<p style="margin-top: 10px; font-size: 0.9em; color: #999;">
                +${result.predictions.length - 1} predicciones mas en 2km
              </p>` : ''
            }
          </div>
        `;

        L.popup()
          .setLatLng([nearest.lat, nearest.lon])
          .setContent(popupContent)
          .openOn(this.map);
      } else {
        this.showMessage('No hay predicciones cercanas en esta ubicacion', 'info');
      }

    } catch (error) {
      console.error('Error obteniendo predicciones cercanas:', error);
      this.showMessage('Error al buscar predicciones cercanas', 'error');
    } finally {
      this.loading = false;
    }
  }

  // Filtra por ciudad
  async filterByCity(city: string): Promise<void> {
    this.analytics.trackAction('filter_by_city', 'filters', city);
    this.selectedCity = city;

    const coords = this.mapState.getCityCoordinates(city);
    if (coords) {
      this.map.setView([coords[0], coords[1]], coords[2]);
    }

    await this.loadData();
  }

  // Precio promedio nacional calculado de citiesStats
  get avgNationalPrice(): number {
    if (!this.citiesStats.length) return 0;
    const sum = this.citiesStats.reduce((acc, c) => acc + (c.avg_price_m2 || 0), 0);
    return sum / this.citiesStats.length;
  }

  // Score promedio nacional calculado de citiesStats
  get avgNationalScore(): number {
    if (!this.citiesStats.length) return 0;
    const sum = this.citiesStats.reduce((acc, c) => acc + (c.avg_plusvalia_score || 0), 0);
    return sum / this.citiesStats.length;
  }

  // Popup de resumen enriquecido al click en cards
  showSummaryPopup(type: string): void {
    const stats = this.citiesStats;
    const scores = Array.from(this.stateScores.entries());

    if (type === 'estados') {
      this.summaryPopupTitle = 'Cobertura por Estado';
      const top5 = [...scores].sort((a, b) => b[1].avg - a[1].avg).slice(0, 5);
      const bottom5 = [...scores].sort((a, b) => a[1].avg - b[1].avg).slice(0, 5);
      this.summaryPopupContent = `
        <div><strong>32 estados</strong> analizados con datos de precios y plusvalia.</div>
        <div class="mt-1"><strong>Top 5 por score:</strong></div>
        ${top5.map(([id, d]) => `<div style="font-size:0.9em;padding:1px 0;">${id.replace('MX-', '')} — <strong>${(d.avg * 100).toFixed(0)}</strong>/100 (${d.count.toLocaleString()} pred.)</div>`).join('')}
        <div class="mt-1"><strong>Menor score:</strong></div>
        ${bottom5.map(([id, d]) => `<div style="font-size:0.9em;padding:1px 0;">${id.replace('MX-', '')} — ${(d.avg * 100).toFixed(0)}/100</div>`).join('')}
      `;
    } else if (type === 'predicciones') {
      this.summaryPopupTitle = 'Predicciones ML';
      const totalPred = this.predictions.length;
      const totalCities = stats.length;
      const avgPerCity = totalCities > 0 ? Math.round(totalPred / totalCities) : 0;
      this.summaryPopupContent = `
        <div><strong>${totalPred.toLocaleString()}</strong> predicciones generadas por el modelo v6.0.</div>
        <div class="mt-1"><strong>${totalCities}</strong> ciudades cubiertas.</div>
        <div><strong>${avgPerCity}</strong> predicciones promedio por ciudad.</div>
        <div class="mt-1" style="color:#666;">Modelo: HierarchicalPredictor v6.0<br>Entrenado con 94K+ registros</div>
      `;
    } else if (type === 'precio') {
      this.summaryPopupTitle = 'Precio Promedio Nacional';
      const prices = stats.filter(c => c.avg_price_m2 > 0).map(c => c.avg_price_m2);
      const maxP = prices.length ? Math.max(...prices) : 0;
      const minP = prices.length ? Math.min(...prices) : 0;
      const topCity = stats.reduce((best, c) => c.avg_price_m2 > (best?.avg_price_m2 || 0) ? c : best, stats[0]);
      const lowCity = stats.reduce((best, c) => (c.avg_price_m2 > 0 && c.avg_price_m2 < (best?.avg_price_m2 || Infinity)) ? c : best, stats[0]);
      this.summaryPopupContent = `
        <div>Precio promedio: <strong>$${this.avgNationalPrice.toLocaleString('es-MX', {maximumFractionDigits: 0})}/m²</strong></div>
        <div class="mt-1"><strong>Mas caro:</strong> ${topCity?.city || '-'} — $${maxP.toLocaleString('es-MX', {maximumFractionDigits: 0})}/m²</div>
        <div><strong>Mas accesible:</strong> ${lowCity?.city || '-'} — $${minP.toLocaleString('es-MX', {maximumFractionDigits: 0})}/m²</div>
        <div class="mt-1"><strong>Rango:</strong> $${minP.toLocaleString('es-MX', {maximumFractionDigits: 0})} — $${maxP.toLocaleString('es-MX', {maximumFractionDigits: 0})}/m²</div>
      `;
    } else if (type === 'score') {
      this.summaryPopupTitle = 'Score de Plusvalia';
      const allScores = stats.filter(c => c.avg_plusvalia_score > 0);
      const alto = allScores.filter(c => c.avg_plusvalia_score >= 70).length;
      const medio = allScores.filter(c => c.avg_plusvalia_score >= 40 && c.avg_plusvalia_score < 70).length;
      const bajo = allScores.filter(c => c.avg_plusvalia_score < 40).length;
      this.summaryPopupContent = `
        <div>Score promedio: <strong>${this.avgNationalScore.toFixed(1)}/100</strong></div>
        <div class="mt-1"><strong>Potencial alto (70+):</strong> ${alto} ciudades</div>
        <div><strong>Potencial medio (40-70):</strong> ${medio} ciudades</div>
        <div><strong>Potencial bajo (&lt;40):</strong> ${bajo} ciudades</div>
        <div class="mt-1" style="color:#666;">Score basado en precio/m², ubicacion, poblacion y tendencias.</div>
      `;
    }

    this.summaryPopup = type;
  }

  // Obtiene color según el score de plusvalía
  getColorByScore(score: number): string {
    return this.mapState.getColorByScore(score);
  }

  // Obtiene color según el potencial de crecimiento
  private getColorByPotential(potential: string): string {
    return this.mapState.getColorByPotential(potential);
  }

  // Agrega leyenda de colores al mapa (choropleth)
  private addHeatmapLegend(): void {
    if (this.legendControl) {
      this.map.removeControl(this.legendControl);
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- L.Control constructor typing mismatch
    const legend = new (L.Control as any)({ position: 'topright' });

    const statesWithData = this.stateScores.size;

    legend.onAdd = () => {
      const div = L.DomUtil.create('div', 'info legend');
      div.innerHTML = `
        <div style="
          background: white;
          padding: 14px 16px;
          border-radius: 10px;
          box-shadow: 0 2px 12px rgba(0,0,0,0.12);
          font-family: 'DM Sans', Arial, sans-serif;
          font-size: 12px;
          line-height: 1.5;
          min-width: 170px;
        ">
          <h4 style="margin: 0 0 10px 0; font-size: 13px; font-weight: 700; color: #1a1a2e; letter-spacing: -0.3px;">
            Plusvalia por Estado
          </h4>
          <div style="display:flex;flex-direction:column;gap:4px;">
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="display:inline-block;width:24px;height:12px;background:#c8e6c9;border-radius:2px;border:1px solid #e0e0e0;"></span>
              <span>Bajo (&lt;55)</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="display:inline-block;width:24px;height:12px;background:#a5d6a7;border-radius:2px;"></span>
              <span>Medio-bajo (55-60)</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="display:inline-block;width:24px;height:12px;background:#66bb6a;border-radius:2px;"></span>
              <span>Medio (60-70)</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="display:inline-block;width:24px;height:12px;background:#4caf50;border-radius:2px;"></span>
              <span>Alto (70-75)</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="display:inline-block;width:24px;height:12px;background:#388e3c;border-radius:2px;"></span>
              <span>Muy alto (75-80)</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="display:inline-block;width:24px;height:12px;background:#1b5e20;border-radius:2px;"></span>
              <span>Premium (80+)</span>
            </div>
          </div>
          <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #6b7280; text-align: center;">
            ${statesWithData} estados &middot; ${this.predictions.length.toLocaleString()} predicciones
          </div>
          <div style="font-size: 10px; color: #9ca3af; text-align: center; margin-top: 3px;">
            Click en un estado para ver detalle
          </div>
        </div>
      `;
      return div;
    };

    legend.addTo(this.map);
    this.legendControl = legend;
  }

  // Maneja selección de ubicación desde el buscador
  onLocationSelected(location: {lat: number, lon: number, name: string}): void {

    if (this.searchMarker) {
      this.map.removeLayer(this.searchMarker);
    }

    const searchIcon = L.icon({
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
    });

    this.searchMarker = L.marker([location.lat, location.lon], { icon: searchIcon })
      .addTo(this.map)
      .bindPopup(`
        <div style="min-width: 200px;">
          <h4 style="margin: 0 0 10px 0; color: #2563eb;">Ubicacion Encontrada</h4>
          <p style="margin: 5px 0; font-size: 13px;"><strong>${location.name}</strong></p>
          <p style="margin: 5px 0; font-size: 12px; color: #666;">
            Lat: ${location.lat.toFixed(5)}, Lon: ${location.lon.toFixed(5)}
          </p>
        </div>
      `)
      .openPopup();

    this.map.setView([location.lat, location.lon], 15, { animate: true, duration: 1 });
    this.showMessage(`Ubicacion encontrada: ${location.name}`, 'success');
  }

  // Maneja cambios en filtros avanzados
  onAdvancedFiltersChanged(filters: AdvancedFilters): void {
    this.filteredPredictions = this.predictions.filter(pred => {
      const score = pred[2] * 100;

      if (score < filters.scoreMin || score > filters.scoreMax) return false;

      let potentialLevel = 'bajo';
      if (score >= 66) potentialLevel = 'alto';
      else if (score >= 33) potentialLevel = 'medio';

      if (!filters.potentialLevels.includes(potentialLevel)) return false;
      return true;
    });

    this.filteredPredictions.sort((a, b) => {
      const compareValue = (a[2] * 100) - (b[2] * 100);
      return filters.sortOrder === 'asc' ? compareValue : -compareValue;
    });

    // Si seleccionó un estado, navegar al estado
    if (filters.selectedState) {
      this.selectedState = filters.selectedState;
      const coords = this.mapState.getCityCoordinates(filters.selectedState);
      if (coords) {
        this.map.setView([coords[0], coords[1]], coords[2]);
      }
    }

    this.updateChoropleth();
    this.addHeatmapLegend();

    this.showMessage(
      `Filtros aplicados: ${this.filteredPredictions.length} de ${this.predictions.length} predicciones`,
      'success'
    );
  }

  // Maneja evento de subida de archivo exitosa
  onFileUploaded(_event: Record<string, unknown>): void {
    this.showMessage('Archivo CSV procesado correctamente', 'success');
  }

  // Maneja evento de aplicar filtros
  onFiltersApplied(filters: AmenityFilters): void {
    this.loading = true;
    this.apiService.getAmenities(filters)
      .then(data => {
        this.amenities = data;

        let filteredTiles = [...this.tiles];
        if (filters.priceMin !== undefined) {
          const minPrice = filters.priceMin;
          filteredTiles = filteredTiles.filter(t => (t.price_m2_avg || 0) >= minPrice);
        }
        if (filters.priceMax !== undefined) {
          const maxPrice = filters.priceMax;
          filteredTiles = filteredTiles.filter(t => (t.price_m2_avg || 0) <= maxPrice);
        }
        this.tiles = filteredTiles;

        this.updateMarkers();
        this.updateHeatmap();
        this.showMessage(`Filtros aplicados: ${data.length} amenidades`, 'success');
      })
      .catch(error => {
        console.error('Error aplicando filtros:', error);
        this.showMessage('Error aplicando filtros', 'error');
      })
      .finally(() => {
        this.loading = false;
      });
  }

  // Maneja evento de extraer amenidades OSM
  async onExtractOsm(params: { city: string; state: string; types: string[] }): Promise<void> {
    this.loading = true;
    this.showMessage('Extrayendo amenidades de OSM...', 'info');

    try {
      const result = await this.apiService.fetchOsmAmenities(params.city, params.state, params.types);
      this.showMessage(`Extraidas ${result['upserts'] || 0} amenidades`, 'success');
      await this.loadData();
    } catch (error) {
      console.error('Error extrayendo OSM:', error);
      this.showMessage('Error extrayendo datos de OSM', 'error');
    } finally {
      this.loading = false;
    }
  }

  // Maneja evento de recalcular grilla
  async onRebuildGrid(): Promise<void> {
    this.loading = true;
    this.showMessage('Recalculando grilla...', 'info');

    try {
      const result = await this.apiService.rebuildGrid();
      this.showMessage(`Grilla recalculada: ${result['tiles'] || 0} tiles`, 'success');
      await this.loadData();
    } catch (error) {
      console.error('Error recalculando grilla:', error);
      this.showMessage('Error recalculando grilla', 'error');
    } finally {
      this.loading = false;
    }
  }

  // TrackBy function para citiesStats *ngFor
  trackByCity(_index: number, city: CityStats): string {
    return city.city;
  }

  // Muestra mensaje al usuario
  private showMessage(msg: string, type: 'success' | 'error' | 'info'): void {
    this.message = msg;
    this.messageType = type;
    if (this.messageTimer) {
      clearTimeout(this.messageTimer);
    }
    this.messageTimer = setTimeout(() => { this.message = ''; this.messageTimer = null; }, 5000);
  }
}
