// src/app/app.component.ts - Componente raíz de la aplicación
import { Component } from '@angular/core'; // decorador Component de Angular
import { RouterOutlet } from '@angular/router'; // directiva para mostrar rutas

@Component({
    selector: 'app-root', // componente standalone (no requiere NgModule)
    imports: [RouterOutlet], // importa RouterOutlet para el routing
    template: `<router-outlet></router-outlet>`, // template inline con outlet para rutas
    styles: [] // sin estilos específicos
})
export class AppComponent { // clase del componente raíz
  title = 'geo-app'; // propiedad título de la aplicación
}

