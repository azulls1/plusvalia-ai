// src/types/leaflet-markercluster.d.ts - Definiciones de tipos para leaflet.markercluster
import * as L from 'leaflet'; // importa tipos de Leaflet

declare module 'leaflet' { // extiende el módulo leaflet
  function markerClusterGroup( // declara función markerClusterGroup
    options?: MarkerClusterGroupOptions // opciones opcionales
  ): MarkerClusterGroup; // retorna MarkerClusterGroup

  interface MarkerClusterGroupOptions { // interfaz para opciones del cluster
    showCoverageOnHover?: boolean; // mostrar área de cobertura al hover
    zoomToBoundsOnClick?: boolean; // hacer zoom al hacer click
    spiderfyOnMaxZoom?: boolean; // expandir marcadores en zoom máximo
    removeOutsideVisibleBounds?: boolean; // remover marcadores fuera de vista
    animate?: boolean; // animación
    animateAddingMarkers?: boolean; // animar al añadir marcadores
    disableClusteringAtZoom?: number; // desactivar clustering en zoom específico
    maxClusterRadius?: number; // radio máximo para clustering
    polygonOptions?: L.PolylineOptions; // opciones para polígono de cobertura
    singleMarkerMode?: boolean; // modo de marcador único
    spiderLegPolylineOptions?: L.PolylineOptions; // opciones para líneas spider
    spiderfyDistanceMultiplier?: number; // multiplicador de distancia spider
    iconCreateFunction?: (cluster: MarkerCluster) => L.Icon | L.DivIcon; // función para crear ícono
  }

  interface MarkerClusterGroup extends L.FeatureGroup { // interfaz para el grupo de clusters
    addLayer(layer: L.Layer): this; // añade capa
    removeLayer(layer: L.Layer): this; // remueve capa
    clearLayers(): this; // limpia todas las capas
    refreshClusters(clusters?: L.Marker | L.Marker[] | L.LayerGroup): this; // refresca clusters
    getVisibleParent(marker: L.Marker): L.Marker; // obtiene padre visible
    getAllChildMarkers(marker: L.Marker): L.Marker[]; // obtiene todos los hijos
  }

  interface MarkerCluster extends L.Marker { // interfaz para un cluster individual
    getAllChildMarkers(): L.Marker[]; // obtiene todos los marcadores hijos
    getChildCount(): number; // obtiene cantidad de hijos
  }
}

