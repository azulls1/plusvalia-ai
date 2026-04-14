# Guía de Instalación - Paso a Paso

Esta guía te llevará a través de la instalación completa del proyecto siguiendo el **ORDEN ESTRICTO** especificado.

## Requisitos Previos

- Acceso a terminal/consola
- Conexión a internet
- Permisos de administrador (para instalar Node.js globalmente)

---

## PASO 1: Node.js

### Windows

1. Descargar Node.js 22.14.0 o superior desde: https://nodejs.org
2. Instalar el archivo descargado
3. Verificar instalación:
```powershell
node --version  # debe mostrar v22.x.x
npm --version   # debe mostrar 10.x.x
```

### Linux/Mac (usando nvm - recomendado)

```bash
# Instalar nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Instalar Node.js 22.14.0
nvm install 22.14.0
nvm use 22.14.0

# Verificar
node --version
npm --version
```

---

## PASO 2: Instalar Angular CLI

```bash
npm install -g @angular/cli@16.2.8
```

Verificar:
```bash
ng version  # debe mostrar Angular CLI 16.2.8
```

---

## PASO 3: Instalar Dependencias del Proyecto

Navegar a la carpeta del proyecto:

```bash
cd geo-app/app
```

Instalar todas las dependencias (esto incluye Tailwind, Bootstrap, Leaflet, Supabase):

```bash
npm install
```

Este comando instalará automáticamente:
- Angular 16.2.8
- Tailwind CSS 3.x
- Bootstrap 5.3.2
- Leaflet 1.9.x + extensiones
- Supabase JS 2.x
- Y todas las dependencias listadas en `package.json`

**Tiempo estimado:** 3-5 minutos dependiendo de la conexión.

---

## PASO 4: Configurar Variables de Entorno

Las credenciales ya están configuradas en:
- `src/environments/environment.ts` (desarrollo)
- `src/environments/environment.prod.ts` (producción)

Si necesitas cambiarlas, edita estos archivos con tus propias credenciales de Supabase y n8n.

---

## PASO 5: Ejecutar en Modo Desarrollo

```bash
npm start
```

O alternativamente:

```bash
ng serve
```

La aplicación se abrirá automáticamente en: **http://localhost:4200**

Para que se abra automáticamente el navegador:

```bash
ng serve --open
```

---

## PASO 6: Verificar Funcionamiento

Una vez que la aplicación esté corriendo:

1. ✅ Verifica que el mapa se carga correctamente
2. ✅ Verifica que puedes ver el panel de controles a la izquierda
3. ✅ Intenta cargar el archivo CSV de ejemplo: `data/samples/comparables_demo.csv`
4. ✅ Verifica los controles de filtros

**Nota:** Para que los datos se muestren completamente, necesitas tener:
- Supabase configurado con las tablas correspondientes
- n8n con los webhooks configurados

Ver `docs/README_supabase.md` para más detalles.

---

## PASO 7: Build para Producción

Cuando estés listo para desplegar:

```bash
npm run build
```

Los archivos compilados estarán en: `dist/app/`

**Optimizaciones automáticas:**
- Minificación de código
- Tree-shaking (eliminación de código no usado)
- Optimización de imágenes
- Hash de archivos para caché

---

## PASO 8: Desplegar en Hostinger

### Opción A: Upload Manual

1. Comprimir el contenido de `dist/app/` en un archivo .zip
2. Acceder al panel de Hostinger
3. Ir a File Manager
4. Subir y descomprimir en `public_html/`
5. Copiar el archivo `.htaccess` a la misma ubicación

### Opción B: FTP

1. Conectar vía FTP usando credenciales de Hostinger
2. Subir todo el contenido de `dist/app/` a `public_html/`
3. Subir el archivo `.htaccess`

### Opción C: Git (si Hostinger lo soporta)

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <tu-repo>
git push -u origin main
```

Luego configurar deploy automático desde Hostinger.

---

## Solución de Problemas Comunes

### Error: "ng: command not found"

Reinstalar Angular CLI globalmente:
```bash
npm install -g @angular/cli@16.2.8
```

### Error: "Module not found"

Reinstalar dependencias:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Error en el mapa: "Map container not found"

Verificar que el div con id="map" existe en el HTML y que el componente se está inicializando correctamente.

### Problemas con Supabase: "Failed to fetch"

Verificar:
1. URL de Supabase correcta en `environment.ts`
2. Anon Key correcta
3. Políticas RLS configuradas
4. Tablas creadas en Supabase

### Problemas con n8n: "Webhook not responding"

Verificar:
1. URL base de n8n correcta
2. Webhooks activos en n8n
3. CORS configurado en n8n (permitir origen de tu dominio)

---

## Estructura de Versiones

| Componente | Versión | Motivo |
|------------|---------|--------|
| Node.js | 22.14.0+ | Última LTS con mejor performance |
| Angular | 16.2.8 | Estable, soporta standalone components |
| Tailwind | 3.x | Última versión estable |
| Bootstrap | 5.3.2 | Compatible con Tailwind |
| Leaflet | 1.9.x | Versión estable para mapas |

---

## Comandos Útiles

```bash
# Desarrollo
npm start              # Inicia servidor de desarrollo
npm run build          # Build de producción
npm run watch          # Build continuo en desarrollo
npm run lint           # Ejecuta linter

# Angular CLI
ng generate component <nombre>  # Genera nuevo componente
ng generate service <nombre>    # Genera nuevo servicio
ng serve --port 4300            # Servidor en puerto diferente
ng build --configuration production  # Build optimizado

# Depuración
ng serve --source-map          # Con source maps para debug
ng build --stats-json          # Genera estadísticas del bundle
```

---

## Próximos Pasos

1. Configurar Supabase (ver `docs/README_supabase.md`)
2. Configurar workflows de n8n
3. Cargar datos de prueba
4. Personalizar estilos según necesidades
5. Añadir más funcionalidades

---

**Documentación completa:** Ver `README.md` en la raíz del proyecto

**Soporte:** contacto@iagentek.com.mx

