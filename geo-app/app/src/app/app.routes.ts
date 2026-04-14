// src/app/app.routes.ts - Definición de rutas de la aplicación
import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/mapa', pathMatch: 'full' },
  {
    path: 'mapa',
    loadComponent: () =>
      import('./pages/mapa/mapa.component').then(m => m.MapaComponent),
  },
  { path: '**', redirectTo: '/mapa' },
];

