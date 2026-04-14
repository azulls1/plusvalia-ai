// src/main.ts - Punto de entrada principal de la aplicación Angular
import './polyfills'; // importa polyfills necesarios (Zone.js, etc.)
import { bootstrapApplication } from '@angular/platform-browser'; // función para iniciar app standalone
import { provideRouter } from '@angular/router'; // proveedor de routing
import { provideHttpClient, withInterceptorsFromDi, HTTP_INTERCEPTORS } from '@angular/common/http'; // HTTP client + interceptors
import { AppComponent } from './app/app.component'; // componente raíz
import { routes } from './app/app.routes'; // definición de rutas
import { RateLimitInterceptor } from './app/guards/rate-limit.interceptor'; // interceptor de seguridad

bootstrapApplication(AppComponent, { // inicia la aplicación con el componente raíz
  providers: [ // proveedores de servicios
    provideRouter(routes), // configura el sistema de rutas
    provideHttpClient(withInterceptorsFromDi()), // habilita HttpClient con soporte para interceptors DI
    { provide: HTTP_INTERCEPTORS, useClass: RateLimitInterceptor, multi: true } // rate limiting, dedup, timeout, error sanitization
  ]
}).catch(err => console.error(err)); // captura errores de inicio

