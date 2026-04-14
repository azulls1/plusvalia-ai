// src/app/pages/mapa/leaflet-extensions.ts
// Force side-effect plugins to attach to the Leaflet namespace.
// With esbuild, bare `import 'pkg'` may be tree-shaken away.
import * as L from 'leaflet';
import 'leaflet.heat';
import 'leaflet.markercluster';

// Reference L so esbuild keeps the import alive and plugins attach
const _L = L;
void _L;

