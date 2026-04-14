// src/types/leaflet-heat.d.ts - Definiciones de tipos para leaflet.heat
import * as L from 'leaflet'; // importa tipos de Leaflet

declare module 'leaflet' { // extiende el módulo leaflet
  function heatLayer( // declara función heatLayer
    latlngs: [number, number, number][], // array de [lat, lon, intensity]
    options?: HeatMapOptions // opciones opcionales
  ): HeatLayer; // retorna HeatLayer

  interface HeatMapOptions { // interfaz para opciones del heatmap
    minOpacity?: number; // opacidad mínima
    maxZoom?: number; // zoom máximo
    max?: number; // valor máximo para normalización
    radius?: number; // radio de cada punto
    blur?: number; // desenfoque
    gradient?: { [key: number]: string }; // gradiente de colores
  }

  interface HeatLayer extends L.Layer { // interfaz para la capa de calor
    setLatLngs(latlngs: [number, number, number][]): this; // método para actualizar puntos
    addLatLng(latlng: [number, number, number]): this; // método para añadir punto
    setOptions(options: HeatMapOptions): this; // método para actualizar opciones
    redraw(): this; // método para redibujar
  }
}

