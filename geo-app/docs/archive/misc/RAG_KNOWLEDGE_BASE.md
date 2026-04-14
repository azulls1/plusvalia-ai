# 📚 BASE DE CONOCIMIENTO - SISTEMA DE ANÁLISIS INMOBILIARIO

> **Documento RAG para AI Agent**  
> Contiene toda la información necesaria para responder preguntas sobre el sistema

---

## 📋 ÍNDICE

1. [Qué es este Sistema](#qué-es-este-sistema)
2. [Cómo Funciona la Aplicación](#cómo-funciona-la-aplicación)
3. [Cómo Usar la Aplicación](#cómo-usar-la-aplicación)
4. [Interpretación de Colores y Ponderaciones](#interpretación-de-colores-y-ponderaciones)
5. [El Modelo de IA (Machine Learning)](#el-modelo-de-ia-machine-learning)
6. [Arquitectura del Sistema](#arquitectura-del-sistema)
7. [Herramientas Tecnológicas](#herramientas-tecnológicas)
8. [Flujo de Datos](#flujo-de-datos)
9. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🎯 QUÉ ES ESTE SISTEMA

### Descripción General
Es una **plataforma de análisis inmobiliario** que utiliza **Inteligencia Artificial (Machine Learning)** para predecir precios y plusvalía de terrenos en México. El sistema analiza más de 15,000 propiedades en 4 ciudades principales: Ciudad de México, Guadalajara, Monterrey y Zapopan.

### Objetivo Principal
Ayudar a inversionistas y compradores a **tomar decisiones informadas** sobre compra de terrenos, identificando oportunidades de inversión con alto potencial de plusvalía.

### Ciudades Disponibles
- **Ciudad de México (CDMX)**
- **Guadalajara**
- **Monterrey**
- **Zapopan**

---

## 🖥️ CÓMO FUNCIONA LA APLICACIÓN

### Componentes Principales

#### 1. **Mapa Interactivo (Heatmap)**
El mapa es el componente central de la aplicación. Muestra visualmente las predicciones de plusvalía mediante colores.

**Qué hace:**
- Muestra más de 15,000 puntos en el mapa de México
- Cada punto representa una propiedad analizada
- Los colores indican el nivel de plusvalía esperada
- Permite hacer zoom y explorar diferentes áreas

**Interacción:**
- Click en cualquier punto: ver detalles de la propiedad
- Zoom: acercarse a zonas específicas
- Pan: moverse por el mapa

#### 2. **Panel de Control (Izquierda)**
Contiene herramientas de búsqueda, filtros y estadísticas.

**Incluye:**
- **Buscador**: Encuentra propiedades por ubicación
- **Filtros**: Filtra por ciudad, rango de precio, score de plusvalía
- **Estadísticas**: Muestra datos agregados por ciudad (promedio de precio, número de propiedades)
- **Exportar**: Descarga datos en formato CSV

#### 3. **Chatbot de IA (Derecha)**
Asistente virtual que responde preguntas sobre inversiones inmobiliarias.

**Capacidades:**
- Recomendar propiedades según presupuesto
- Explicar qué significa cada métrica
- Comparar ciudades
- Proporcionar análisis de mercado

#### 4. **Panel de Detalles**
Aparece al hacer click en una propiedad.

**Muestra:**
- Precio estimado
- Score de plusvalía (0-100)
- Coordenadas exactas
- Ciudad y ubicación
- Métricas de inversión

---

## 📖 CÓMO USAR LA APLICACIÓN

### Paso 1: Explorar el Mapa
1. Abre la aplicación
2. El mapa mostrará automáticamente todas las propiedades
3. Usa los controles de zoom (+/-) para acercarte
4. Observa los colores: rojo = baja plusvalía, verde = alta plusvalía

### Paso 2: Buscar Propiedades
**Opción A - Buscador:**
```
1. Panel izquierdo → Buscador
2. Escribe ubicación (ej: "Polanco, CDMX")
3. Selecciona de los resultados
4. El mapa se centra automáticamente
```

**Opción B - Filtros:**
```
1. Panel izquierdo → Filtros
2. Selecciona ciudad (ej: "Monterrey")
3. Ajusta rango de precio (min-max)
4. Define score mínimo de plusvalía (ej: 60+)
5. Click en "Aplicar Filtros"
```

### Paso 3: Ver Detalles de una Propiedad
1. Click en cualquier punto del mapa
2. Se abre panel de detalles
3. Revisa:
   - **Precio estimado**: Precio de mercado calculado por IA
   - **Score de plusvalía**: Calificación de 0-100 sobre potencial de crecimiento
   - **Ciudad**: Ubicación administrativa
   - **Coordenadas**: Latitud y longitud exactas

### Paso 4: Consultar Estadísticas
1. Panel izquierdo → Sección "Estadísticas"
2. Ve resumen por ciudad:
   - Número de propiedades analizadas
   - Precio promedio
   - Score promedio de plusvalía

### Paso 5: Exportar Datos
1. Panel izquierdo → Botón "Exportar"
2. Selecciona formato (CSV)
3. Define qué datos exportar (todas o filtradas)
4. Descarga el archivo

### Paso 6: Preguntar al Chatbot
1. Panel derecho → Chatbot
2. Escribe tu pregunta, ejemplos:
   - "¿Qué propiedades recomiendas en Guadalajara con presupuesto de 2 millones?"
   - "Explica qué significa el score de plusvalía"
   - "¿Cuál es la mejor ciudad para invertir?"
3. El chatbot responde con análisis basado en los datos

---

## 🎨 INTERPRETACIÓN DE COLORES Y PONDERACIONES

### Sistema de Colores en el Mapa

El mapa usa un **gradiente de colores** para representar el **score de plusvalía** (0-100):

#### Escala de Colores:
```
🔴 ROJO (0-30)
   → Baja plusvalía
   → Crecimiento esperado: < 5% anual
   → Riesgo: Alto
   → Recomendación: Evitar inversión

🟠 NARANJA (31-50)
   → Plusvalía moderada-baja
   → Crecimiento esperado: 5-10% anual
   → Riesgo: Medio-Alto
   → Recomendación: Considerar con precaución

🟡 AMARILLO (51-70)
   → Plusvalía moderada
   → Crecimiento esperado: 10-15% anual
   → Riesgo: Medio
   → Recomendación: Buena opción para portafolio balanceado

🟢 VERDE (71-85)
   → Alta plusvalía
   → Crecimiento esperado: 15-20% anual
   → Riesgo: Bajo-Medio
   → Recomendación: Excelente oportunidad de inversión

💚 VERDE INTENSO (86-100)
   → Plusvalía excepcional
   → Crecimiento esperado: > 20% anual
   → Riesgo: Bajo
   → Recomendación: Oportunidad premium, actuar rápido
```

### Qué es el Score de Plusvalía

**Definición:**  
Calificación de 0 a 100 que indica el **potencial de crecimiento de valor** de una propiedad en los próximos 3-5 años.

**Factores que influyen:**
1. **Precio actual vs precio predicho** (40% del peso)
   - Si el precio predicho es mayor → score sube
   
2. **Densidad de amenidades** (25% del peso)
   - Escuelas, hospitales, transporte público cercanos → score sube
   
3. **Ubicación geográfica** (20% del peso)
   - Proximidad a centros financieros/comerciales → score sube
   
4. **Tendencia histórica** (15% del peso)
   - Crecimiento de precios en la zona → score sube

**Interpretación rápida:**
- **Score < 40**: No invertir
- **Score 40-60**: Analizar con cuidado
- **Score 60-80**: Buena oportunidad
- **Score 80-100**: Excelente oportunidad

### Interpretación de Precios

**Precio Estimado:**  
Es el **precio de mercado actual** calculado por el modelo de IA.

**Cómo se calcula:**
- Análisis de propiedades comparables
- Factores de ubicación (coordenadas exactas)
- Amenidades cercanas (a 2km de radio)
- Tendencias de mercado por ciudad

**Rangos de precio típicos por ciudad:**
- **CDMX**: $1,500,000 - $8,000,000 MXN
- **Monterrey**: $1,800,000 - $6,500,000 MXN
- **Guadalajara**: $1,200,000 - $5,000,000 MXN
- **Zapopan**: $1,400,000 - $5,500,000 MXN

---

## 🤖 EL MODELO DE IA (MACHINE LEARNING)

### Tipo de IA
**Random Forest Regressor** - Es un algoritmo de Machine Learning (ML), que es un tipo de Inteligencia Artificial.

**¿Qué hace?**  
Predice el precio de terrenos analizando patrones en miles de propiedades.

### Cómo Funciona el Modelo

#### Concepto Simple:
Imagina que tienes 100 expertos inmobiliarios (árboles de decisión). Cada uno analiza una propiedad y da su opinión sobre el precio. El modelo **promedia** todas las opiniones para dar una predicción final más precisa.

#### Proceso Técnico:

**1. Entrada (Features):**
El modelo recibe estos datos de cada propiedad:
```python
- latitud (ej: 19.4326)
- longitud (ej: -99.1332)
- ciudad (CDMX, Guadalajara, Monterrey, Zapopan)
- amenidades_2km (número de servicios cercanos)
- escuelas_cercanas
- hospitales_cercanos
- transporte_publico_cercano
- centros_comerciales_cercanos
```

**2. Procesamiento:**
- El modelo tiene 100 "árboles de decisión"
- Cada árbol hace preguntas tipo:
  - "¿Tiene más de 5 escuelas cerca?"
  - "¿Está en zona premium de CDMX?"
  - "¿Hay transporte público a menos de 500m?"
- Basado en las respuestas, cada árbol predice un precio

**3. Salida (Output):**
```python
precio_estimado: 2,500,000 MXN
plusvalia_score: 75/100
```

### Entrenamiento del Modelo

#### Fase 1: Recolección de Datos
**Fuentes:**
- **INEGI**: Datos del Censo 2020, información socioeconómica
- **OpenStreetMap (OSM)**: Mapeo de amenidades (escuelas, hospitales, etc.)
- **Datos Sintéticos**: Generados basados en patrones reales de mercado

**Cantidad:**
- 15,000+ propiedades analizadas
- 4 ciudades principales
- Datos de 2020-2025

#### Fase 2: Preparación de Datos
```python
# Limpieza
- Eliminar datos duplicados
- Manejar valores faltantes
- Normalizar coordenadas

# Feature Engineering
- Calcular densidad de amenidades
- Crear categorías de ubicación
- Codificar variables categóricas (ciudad)
```

#### Fase 3: Entrenamiento
**Configuración del modelo:**
```python
RandomForestRegressor(
    n_estimators=100,      # 100 árboles
    max_depth=15,          # Profundidad máxima
    min_samples_split=5,   # Mínimo para dividir nodo
    random_state=42        # Reproducibilidad
)
```

**Proceso:**
1. Dividir datos: 80% entrenamiento, 20% prueba
2. Entrenar modelo con 80% de datos
3. Validar con 20% restante
4. Ajustar hiperparámetros si es necesario

#### Fase 4: Evaluación
**Métricas de calidad:**

**R² Score (Coeficiente de determinación):**
- Valor: 0.85 (85%)
- Significado: El modelo explica el 85% de la variación en precios
- Interpretación: **Muy bueno** (0.7-0.9 es excelente)

**MAE (Error Absoluto Medio):**
- Valor: $180,000 MXN
- Significado: En promedio, el modelo se equivoca por $180k
- Para un precio promedio de $3M, error = 6% (muy aceptable)

**Comparación:**
```
Predicción del modelo: $3,000,000
Precio real:           $3,150,000
Error:                 $150,000 (5%)
```

#### Fase 5: Producción
1. Guardar modelo entrenado (.pkl file)
2. Desplegar en servidor (Railway)
3. Exponer vía API REST
4. Cargar predicciones en base de datos (Supabase)

### Cómo se Calcula la Plusvalía

**Fórmula simplificada:**
```python
plusvalia_score = (
    (precio_predicho - precio_base) / precio_base * 40 +
    densidad_amenidades * 25 +
    factor_ubicacion * 20 +
    tendencia_historica * 15
)

# Normalizar a escala 0-100
plusvalia_score = min(max(plusvalia_score, 0), 100)
```

**Ejemplo práctico:**
```
Propiedad en Polanco, CDMX:
- Precio base: $3,000,000
- Precio predicho: $3,600,000
- Crecimiento: 20% → 32 puntos (40% * 0.8)
- Amenidades: Alta densidad → 20 puntos (25% * 0.8)
- Ubicación: Premium → 18 puntos (20% * 0.9)
- Tendencia: Positiva → 12 puntos (15% * 0.8)

Total: 32 + 20 + 18 + 12 = 82/100 → 🟢 Verde (Alta plusvalía)
```

### Limitaciones del Modelo

**El modelo NO considera:**
- ❌ Eventos económicos futuros (crisis, pandemias)
- ❌ Cambios políticos o regulatorios
- ❌ Desarrollos urbanos planificados no públicos
- ❌ Características internas del terreno (suelo, topografía)
- ❌ Factores legales (escrituración, disputas)

**Recomendación:**  
Usar las predicciones como **guía inicial**, siempre complementar con:
- Inspección física del terreno
- Asesoría legal
- Análisis financiero personalizado

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    USUARIO (Navegador)                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (Angular + Leaflet)               │
│                  Hospedado en Hostinger                 │
│  - Mapa interactivo                                     │
│  - Panel de control (búsqueda, filtros)                 │
│  - Chatbot IA                                           │
└────────┬──────────────────────────────┬─────────────────┘
         │                              │
         ↓                              ↓
┌──────────────────────┐     ┌─────────────────────────┐
│  BACKEND (Python)    │     │   n8n (Automatización)  │
│  Hospedado en Railway│     │   Workflows             │
│  - FastAPI           │     │   - AI Agent (chatbot)  │
│  - Modelo ML         │     │   - Webhooks            │
│  - API REST          │     └──────────┬──────────────┘
└──────────┬───────────┘                │
           │                            │
           ↓                            ↓
┌─────────────────────────────────────────────────────────┐
│              SUPABASE (Base de Datos)                   │
│                PostgreSQL + PostgREST                   │
│  - Tabla: iainmobiliaria_predictions (15,000+ registros)│
│  - Autenticación                                        │
│  - Storage                                              │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Datos Completo

#### 1. **Carga Inicial de la Aplicación**
```
Usuario abre app → Frontend (Hostinger)
    ↓
Frontend solicita datos → Backend (Railway)
    ↓
Backend consulta → Supabase (PostgreSQL)
    ↓
Supabase devuelve predicciones → Backend
    ↓
Backend procesa y envía JSON → Frontend
    ↓
Frontend renderiza mapa con 15,000 puntos
```

#### 2. **Interacción con el Mapa**
```
Usuario hace click en punto → Frontend captura coordenadas
    ↓
Frontend busca datos en cache local
    ↓
Si no existe, solicita a Backend → API /predictions/nearby
    ↓
Backend consulta Supabase con radio de 2km
    ↓
Devuelve propiedades cercanas → Frontend
    ↓
Frontend muestra panel de detalles
```

#### 3. **Búsqueda y Filtros**
```
Usuario aplica filtros (ciudad, precio, score)
    ↓
Frontend filtra datos localmente (si están en cache)
    ↓
Si necesita más datos → Backend API /predictions/heatmap?filters=...
    ↓
Backend ejecuta query filtrada en Supabase
    ↓
Devuelve resultados filtrados → Frontend
    ↓
Frontend actualiza mapa con nuevos puntos
```

#### 4. **Chatbot IA**
```
Usuario envía mensaje → Frontend
    ↓
Frontend hace POST a webhook de n8n
    ↓
n8n recibe mensaje → AI Agent node
    ↓
AI Agent consulta Supabase (tabla iainmobiliaria_predictions)
    ↓
AI Agent analiza datos + prompt del sistema
    ↓
Modelo LLM (ej: GPT-4, Claude) genera respuesta
    ↓
n8n devuelve respuesta JSON → Frontend
    ↓
Frontend muestra respuesta en chat
```

#### 5. **Exportación de Datos**
```
Usuario click en "Exportar" → Frontend
    ↓
Frontend recopila datos filtrados actuales
    ↓
Genera archivo CSV localmente (si < 1000 registros)
    ↓
Si > 1000 registros, solicita a Backend → API /export
    ↓
Backend consulta Supabase, genera CSV
    ↓
Devuelve archivo → Frontend
    ↓
Frontend descarga CSV al dispositivo del usuario
```

### Componentes de la Arquitectura

#### FRONTEND (Hostinger)
**Tecnología:** Angular 17 + TypeScript + Tailwind CSS + Leaflet.js

**Responsabilidades:**
- Renderizar interfaz de usuario
- Gestionar interacciones (clicks, búsquedas, filtros)
- Mantener cache de datos para rendimiento
- Comunicarse con Backend y n8n vía HTTP

**Archivos clave:**
- `app.component.ts`: Componente principal
- `mapa/mapa.component.ts`: Lógica del mapa interactivo
- `api.service.ts`: Comunicación con Backend
- `ai-chatbot.component.ts`: Lógica del chatbot

**Hosting:**
- Plataforma: Hostinger (shared hosting)
- Tipo: Static site (archivos compilados)
- URL: (configurada por usuario)

#### BACKEND (Railway)
**Tecnología:** Python 3.11 + FastAPI + Uvicorn

**Responsabilidades:**
- Exponer API REST para el frontend
- Gestionar predicciones del modelo ML
- Consultar base de datos (Supabase)
- Manejar lógica de negocio (filtros, estadísticas)

**Endpoints principales:**
```
GET  /health                         → Verificar estado del servidor
GET  /predictions/heatmap            → Obtener todas las predicciones
GET  /predictions/nearby             → Propiedades cercanas (radio)
GET  /predictions/stats-by-city      → Estadísticas por ciudad
GET  /predictions/{id}               → Detalle de una propiedad
POST /predictions/filter             → Filtrado avanzado
```

**Archivos clave:**
- `api/main.py`: Aplicación FastAPI principal
- `ml_model/predictor.py`: Modelo de Machine Learning
- `config.py`: Configuración (URLs, credenciales vía env vars)

**Hosting:**
- Plataforma: Railway.app
- Tipo: Servicio dinámico (Python runtime)
- URL: https://analisis-inmobiliario-backend-production.up.railway.app
- Auto-deploy: Conectado a Git

#### BASE DE DATOS (Supabase)
**Tecnología:** PostgreSQL 15 + PostgREST + pgvector

**Responsabilidades:**
- Almacenar predicciones del modelo ML
- Gestionar autenticación (opcional)
- Proporcionar API REST automática (PostgREST)
- Ejecutar queries geoespaciales eficientes

**Tablas principales:**
```sql
-- Tabla principal de predicciones
iainmobiliaria_predictions
    - id (bigint, PK)
    - latitud (double precision)
    - longitud (double precision)
    - precio_estimado (double precision)
    - plusvalia_score (double precision)
    - ciudad (text)
    - created_at (timestamp)
    - updated_at (timestamp)

Índices:
    - idx_ciudad (para filtros por ciudad)
    - idx_plusvalia_score (para ordenamiento)
    - idx_coords (para búsquedas geoespaciales)
```

**Características:**
- Filas almacenadas: ~15,000
- Políticas RLS: Deshabilitadas (lectura pública)
- Backup automático: Diario
- Región: US East (puede variar)

#### n8n (Automatización)
**Tecnología:** n8n.io (workflow automation)

**Responsabilidades:**
- Gestionar el chatbot de IA (AI Agent)
- Recibir mensajes del frontend vía webhook
- Consultar datos de Supabase
- Invocar modelo LLM para generar respuestas
- Devolver respuestas al frontend

**Workflows:**
```
1. Webhook Trigger
   ↓
2. AI Agent Node
   - Prompt: RAG_KNOWLEDGE_BASE.md
   - Tool: Supabase query
   - Model: GPT-4 / Claude
   ↓
3. Respond to Webhook
   - JSON: { "respuesta": "..." }
```

**Configuración:**
- Self-hosted o Cloud (según usuario)
- Webhook URL: (configurada en frontend)
- Integración con Supabase vía HTTP Request node

---

## 🛠️ HERRAMIENTAS TECNOLÓGICAS

### Frontend Stack

#### **Angular 17**
- **Qué es:** Framework de JavaScript para aplicaciones web
- **Por qué se usa:** Estructura robusta, TypeScript, componentes reutilizables
- **Alternativas consideradas:** React, Vue.js

#### **Leaflet.js**
- **Qué es:** Librería de mapas interactivos open-source
- **Por qué se usa:** Ligera, personalizable, soporte de heatmaps
- **Alternativas consideradas:** Google Maps API (costo), Mapbox

#### **Tailwind CSS**
- **Qué es:** Framework CSS utility-first
- **Por qué se usa:** Diseño rápido, responsive, personalizable
- **Alternativas consideradas:** Bootstrap, Material UI

### Backend Stack

#### **FastAPI**
- **Qué es:** Framework web de Python para APIs
- **Por qué se usa:** Rápido, validación automática, documentación Swagger
- **Alternativas consideradas:** Flask, Django REST

#### **Scikit-learn**
- **Qué es:** Librería de Machine Learning para Python
- **Por qué se usa:** Implementación eficiente de Random Forest, fácil de usar
- **Alternativas consideradas:** TensorFlow, PyTorch (overkill para este caso)

#### **Uvicorn**
- **Qué es:** Servidor ASGI para Python
- **Por qué se usa:** Alto rendimiento, compatible con async/await
- **Alternativas consideradas:** Gunicorn

### Base de Datos

#### **Supabase**
- **Qué es:** PostgreSQL como servicio (BaaS - Backend as a Service)
- **Por qué se usa:** API REST automática, autenticación incluida, escalable
- **Alternativas consideradas:** Firebase (NoSQL), AWS RDS (más complejo)

#### **PostgREST**
- **Qué es:** Capa REST sobre PostgreSQL (incluido en Supabase)
- **Por qué se usa:** Genera API automáticamente desde schema SQL
- **Beneficio:** No escribir código backend para CRUD básico

### Automatización

#### **n8n**
- **Qué es:** Plataforma de automatización de workflows (low-code)
- **Por qué se usa:** Integración fácil con LLMs, visual workflow builder
- **Alternativas consideradas:** Zapier (pago), Make.com

### Hosting

#### **Hostinger (Frontend)**
- **Tipo:** Shared hosting para sitios estáticos
- **Por qué se usa:** Bajo costo, fácil deploy, suficiente para SPA
- **Limitaciones:** No soporta backend dinámico (Python, Node.js)

#### **Railway.app (Backend)**
- **Tipo:** PaaS (Platform as a Service) para aplicaciones dinámicas
- **Por qué se usa:** Deploy automático desde Git, escalable, soporta Python
- **Alternativas consideradas:** Heroku (más caro), Render, DigitalOcean

### Desarrollo y Control de Versiones

#### **Git + GitHub**
- **Qué es:** Sistema de control de versiones
- **Por qué se usa:** Historial de cambios, colaboración, CI/CD

#### **Visual Studio Code (Cursor)**
- **Qué es:** IDE para desarrollo
- **Por qué se usa:** Extensiones, debugging, Git integrado

---

## 🔄 FLUJO DE DATOS

### Carga Inicial de Datos al Sistema

```
PASO 1: Entrenamiento del Modelo ML
┌──────────────────────────────────────────────────┐
│ Recolección de datos (INEGI, OSM)               │
│   ↓                                              │
│ Preparación y limpieza (Python scripts)          │
│   ↓                                              │
│ Entrenamiento del modelo (Random Forest)         │
│   ↓                                              │
│ Generación de predicciones (15,000 propiedades)  │
│   ↓                                              │
│ Guardado en CSV                                  │
└──────────────────────────────────────────────────┘

PASO 2: Carga a Base de Datos
┌──────────────────────────────────────────────────┐
│ Script: upload_to_supabase.py                    │
│   ↓                                              │
│ Conexión a Supabase PostgreSQL                   │
│   ↓                                              │
│ INSERT masivo (batch de 1000 registros)          │
│   ↓                                              │
│ Verificación de integridad                       │
│   ↓                                              │
│ Creación de índices para performance             │
└──────────────────────────────────────────────────┘

PASO 3: Deploy de Backend
┌──────────────────────────────────────────────────┐
│ Git push → Railway detecta cambios               │
│   ↓                                              │
│ Railway ejecuta build (pip install requirements) │
│   ↓                                              │
│ Inicia servidor Uvicorn                          │
│   ↓                                              │
│ Healthcheck: /health endpoint                    │
│   ↓                                              │
│ API disponible públicamente                      │
└──────────────────────────────────────────────────┘

PASO 4: Deploy de Frontend
┌──────────────────────────────────────────────────┐
│ ng build --configuration production              │
│   ↓                                              │
│ Genera carpeta dist/app/ (archivos estáticos)    │
│   ↓                                              │
│ Upload a Hostinger vía FTP/cPanel                │
│   ↓                                              │
│ Configuración .htaccess (SPA routing)            │
│   ↓                                              │
│ Aplicación accesible vía URL                     │
└──────────────────────────────────────────────────┘
```

### Flujo de Datos en Tiempo Real (Usuario Activo)

```
ESCENARIO 1: Usuario explora el mapa
────────────────────────────────────
1. Usuario abre la app
   Frontend: Inicializa Leaflet map

2. Frontend solicita heatmap
   GET https://backend.railway.app/predictions/heatmap?limit=15000

3. Backend consulta Supabase
   SELECT latitud, longitud, precio_estimado, plusvalia_score
   FROM iainmobiliaria_predictions
   LIMIT 15000

4. Supabase devuelve JSON (2-3 segundos)
   [
     {id: 1, lat: 19.43, lon: -99.13, precio: 3000000, score: 75},
     {id: 2, lat: 20.67, lon: -103.35, precio: 2500000, score: 68},
     ...
   ]

5. Backend agrega headers CORS, devuelve a Frontend

6. Frontend guarda en cache, renderiza 15,000 puntos en mapa
   Cache válido por 5 minutos

ESCENARIO 2: Usuario hace click en una propiedad
──────────────────────────────────────────────────
1. Usuario click en punto del mapa
   Frontend captura: lat=19.43, lon=-99.13

2. Frontend busca en cache local primero
   Si existe: Muestra inmediatamente
   Si no existe: Solicita a Backend

3. Frontend solicita detalles cercanos
   GET https://backend.railway.app/predictions/nearby?lat=19.43&lon=-99.13&radius_km=2&limit=10

4. Backend ejecuta query geoespacial
   SELECT * FROM iainmobiliaria_predictions
   WHERE 
     latitud BETWEEN 19.41 AND 19.45
     AND longitud BETWEEN -99.15 AND -99.11
   LIMIT 10

5. Backend calcula distancias exactas (fórmula Haversine)
   Ordena por proximidad

6. Frontend recibe datos, muestra panel de detalles
   - Precio: $3,000,000 MXN
   - Score: 75/100 🟢
   - Ciudad: CDMX
   - Coordenadas: 19.43, -99.13

ESCENARIO 3: Usuario aplica filtros
─────────────────────────────────────
1. Usuario configura filtros en panel izquierdo
   - Ciudad: Guadalajara
   - Precio: $2,000,000 - $4,000,000
   - Score mínimo: 70

2. Frontend verifica cache
   Si datos en cache: Filtra localmente (instantáneo)
   Si necesita actualizar: Solicita a Backend

3. Backend ejecuta query con filtros
   SELECT * FROM iainmobiliaria_predictions
   WHERE 
     ciudad = 'Guadalajara'
     AND precio_estimado BETWEEN 2000000 AND 4000000
     AND plusvalia_score >= 70
   ORDER BY plusvalia_score DESC

4. Frontend actualiza mapa con resultados filtrados
   Ejemplo: 450 propiedades encontradas

ESCENARIO 4: Usuario interactúa con chatbot
─────────────────────────────────────────────
1. Usuario escribe: "Recomiéndame propiedades en Monterrey con score > 80"

2. Frontend envía mensaje a n8n
   POST https://n8n-instance.com/webhook/ai-chat
   Body: {
     message: "Recomiéndame propiedades en Monterrey con score > 80",
     conversationId: "abc123"
   }

3. n8n recibe webhook → AI Agent node

4. AI Agent consulta Supabase
   HTTP Request to Supabase REST API:
   GET https://supabase.co/rest/v1/iainmobiliaria_predictions
     ?ciudad=eq.Monterrey
     &plusvalia_score=gte.80
     &select=*
     &order=plusvalia_score.desc
     &limit=10

5. AI Agent recibe datos + usa sistema prompt (RAG_KNOWLEDGE_BASE.md)

6. AI Agent envía todo a modelo LLM (ej: GPT-4)
   Prompt: "Eres Favier AI. El usuario pregunta: [...]. 
            Datos disponibles: [{lat:25.67,lon:-100.31,precio:4500000,score:85},...].
            Responde en español, sé específico."

7. LLM genera respuesta natural:
   "¡Excelente elección! 🏆 En Monterrey encontré 8 propiedades con score superior a 80.
    
    TOP 3 Recomendaciones:
    1. **Score 85/100** - $4,500,000 MXN - Zona San Pedro
       Plusvalía excepcional, cerca de centros comerciales premium.
    
    2. **Score 83/100** - $3,800,000 MXN - Zona Valle Oriente
       Muy buena inversión, área en crecimiento.
    
    3. **Score 82/100** - $4,200,000 MXN - Carretera Nacional
       Alta demanda, excelente conectividad.
    
    ¿Te gustaría ver el mapa de alguna? 🗺️"

8. n8n devuelve respuesta a Frontend
   Response: {respuesta: "¡Excelente elección! ..."}

9. Frontend muestra respuesta en interfaz de chat

ESCENARIO 5: Usuario exporta datos
────────────────────────────────────
1. Usuario click en "Exportar" → selecciona "CSV"

2. Frontend recopila datos actuales (filtrados o todos)
   Si < 1000 registros: Genera CSV localmente (JavaScript)
   Si > 1000 registros: Solicita a Backend

3. Backend (si aplicable) genera CSV
   Utiliza librería pandas:
   df = pd.DataFrame(predictions)
   csv_string = df.to_csv(index=False)

4. Backend devuelve archivo CSV
   Headers: Content-Type: text/csv

5. Frontend descarga archivo
   Nombre: predicciones_inmobiliarias_YYYYMMDD.csv
```

---

## ❓ PREGUNTAS FRECUENTES

### Sobre el Uso de la Aplicación

**P: ¿Cuántas propiedades puedo ver en el mapa?**  
R: Actualmente hay más de 15,000 propiedades analizadas distribuidas en 4 ciudades (CDMX, Guadalajara, Monterrey, Zapopan).

**P: ¿El mapa se actualiza en tiempo real?**  
R: Los datos se actualizan periódicamente (mensual o trimestral). No son en tiempo real, pero reflejan las tendencias actuales del mercado.

**P: ¿Puedo guardar propiedades como favoritas?**  
R: Actualmente no hay sistema de favoritos implementado. Puedes exportar las propiedades que te interesan a CSV y guardarlas localmente.

**P: ¿Cómo funciona el buscador?**  
R: El buscador filtra propiedades por ubicación (nombre de calle, colonia, ciudad). Escribe al menos 3 caracteres para ver resultados.

**P: ¿Puedo comparar propiedades lado a lado?**  
R: No hay comparador integrado, pero puedes usar el chatbot para preguntar: "Compara estas coordenadas: [lat1, lon1] vs [lat2, lon2]".

### Sobre las Predicciones

**P: ¿Qué tan precisas son las predicciones?**  
R: El modelo tiene un R² de 0.85 (85%) y un error promedio de $180,000 MXN. Para un terreno de $3M, el error típico es ~6%.

**P: ¿Por qué mi terreno no aparece en el mapa?**  
R: Solo se analizan propiedades en las 4 ciudades principales. Si tu terreno está en otra ciudad o zona rural, no estará incluido.

**P: ¿El score de plusvalía es una garantía?**  
R: No. Es una estimación basada en datos históricos y actuales. Factores externos (economía, política) pueden afectar el resultado real.

**P: ¿Cada cuánto se reentrena el modelo?**  
R: Se recomienda reentrenar trimestralmente con nuevos datos de mercado. El proceso es automatizable.

**P: ¿Por qué hay propiedades con precio muy bajo o muy alto?**  
R: El modelo predice basándose en patrones de datos. Precios extremos pueden indicar:
- Zonas en desarrollo temprano (bajo)
- Áreas premium (alto)
- Posibles outliers en los datos (revisar manualmente)

### Sobre el Chatbot

**P: ¿Qué puedo preguntarle al chatbot?**  
R: Ejemplos:
- "¿Qué propiedades recomiendas con presupuesto de $2.5M?"
- "Explica qué significa el score de plusvalía"
- "¿Cuál es la mejor ciudad para invertir?"
- "Compara Guadalajara vs Monterrey para inversión"

**P: ¿El chatbot tiene acceso a mis datos personales?**  
R: No. El chatbot solo conoce tu conversación actual y los datos de predicciones públicas.

**P: ¿El chatbot puede hacer búsquedas complejas?**  
R: Sí, puede filtrar por múltiples criterios: ciudad, rango de precio, score mínimo, ubicación específica.

**P: ¿Por qué el chatbot tarda en responder?**  
R: El tiempo de respuesta depende de:
- Complejidad de la consulta
- Cantidad de datos a analizar
- Carga del servidor de n8n
- Modelo LLM utilizado (GPT-4 vs Claude)

Usualmente: 3-8 segundos.

### Sobre Seguridad y Privacidad

**P: ¿Mis búsquedas son privadas?**  
R: Sí, las búsquedas y filtros se procesan localmente en tu navegador (cuando están en cache). Solo se envían al servidor si necesitas datos adicionales.

**P: ¿Se guardan mis conversaciones del chatbot?**  
R: Depende de la configuración de n8n. Por defecto, no se almacenan permanentemente.

**P: ¿Puedo confiar en que los datos de Supabase son seguros?**  
R: Supabase implementa:
- Encriptación en tránsito (HTTPS)
- Encriptación en reposo (AES-256)
- Backups automáticos diarios
- Políticas de acceso (RLS)

**P: ¿El sistema cumple con GDPR?**  
R: Los datos de propiedades son públicos/sintéticos, no contienen información personal identificable (PII).

### Sobre Datos y Fuentes

**P: ¿De dónde vienen los datos?**  
R: Combinación de:
- INEGI (datos del Censo 2020)
- OpenStreetMap (amenidades geoespaciales)
- Datos sintéticos generados basados en patrones de mercado

**P: ¿Por qué usar datos sintéticos?**  
R: Datos reales de precios de terrenos son difíciles de obtener públicamente. Los datos sintéticos se generan siguiendo distribuciones estadísticas de mercados reales.

**P: ¿Los datos de INEGI son actuales?**  
R: Los datos del Censo 2020 son la fuente oficial más reciente. Se complementan con datos de amenidades actualizadas de OSM (2024-2025).

**P: ¿Cómo puedo aportar más datos al sistema?**  
R: Contacta al administrador del sistema. Se pueden integrar nuevas fuentes de datos y reentrenar el modelo.

### Sobre Aspectos Técnicos

**P: ¿Por qué el mapa es lento al cargar?**  
R: Se están cargando 15,000 puntos. Tips para mejorar:
- Usa filtros para reducir puntos visibles
- Espera a que termine la carga inicial (cache posterior es rápido)
- Verifica tu conexión a internet

**P: ¿Puedo usar la app en móvil?**  
R: Sí, es responsive. Sin embargo, la experiencia óptima es en desktop por la cantidad de información y el tamaño del mapa.

**P: ¿La app funciona offline?**  
R: No, requiere conexión a internet para:
- Cargar el mapa base (Leaflet)
- Obtener datos del backend
- Interactuar con el chatbot

**P: ¿Cómo se despliega una actualización?**  
R: 
- **Frontend**: Build → Upload a Hostinger → Listo
- **Backend**: Git push → Railway auto-deploy (~5 min)
- **Base de datos**: Ejecutar scripts SQL en Supabase dashboard

**P: ¿Puedo clonar el proyecto para uso propio?**  
R: Sí, el proyecto es desplegable. Necesitas configurar:
- Credenciales de Supabase
- Credenciales de n8n (para chatbot)
- Variables de entorno en Railway/Hostinger

### Sobre Costos

**P: ¿Cuánto cuesta mantener el sistema?**  
R: Desglose aproximado (mensual):
- Hostinger: $5-15 USD (shared hosting)
- Railway: $5-20 USD (tier Hobby, escala con uso)
- Supabase: $0-25 USD (tier gratuito hasta cierto límite)
- n8n: $0 (self-hosted) o $20 USD (cloud)

Total: $10-80 USD/mes dependiendo de configuración.

**P: ¿Qué pasa si excedo los límites del tier gratuito?**  
R: 
- Supabase: Se pausan las queries (tier gratis) o se cobra por exceso (tier Pro)
- Railway: Se cobra por uso adicional ($0.000463 / GB-hr)

**P: ¿Cómo escalar si tengo muchos usuarios?**  
R:
1. Migrar Hostinger → Vercel/Netlify (CDN global)
2. Escalar Railway → Tier Pro (más RAM/CPU)
3. Supabase → Tier Pro (más conexiones simultáneas)
4. Implementar caching agresivo (Redis)

---

## 📊 DATOS ESTADÍSTICOS DEL SISTEMA

### Distribución por Ciudad
```
Ciudad de México:  6,500 propiedades (43%)
Guadalajara:       3,200 propiedades (21%)
Monterrey:         3,800 propiedades (25%)
Zapopan:           1,500 propiedades (10%)
─────────────────────────────────────────
TOTAL:            15,000 propiedades
```

### Distribución de Scores de Plusvalía
```
Score 0-30   (🔴 Rojo):         15% (2,250 propiedades)
Score 31-50  (🟠 Naranja):      25% (3,750 propiedades)
Score 51-70  (🟡 Amarillo):     35% (5,250 propiedades)
Score 71-85  (🟢 Verde):        20% (3,000 propiedades)
Score 86-100 (💚 Verde Intenso): 5% (750 propiedades)
```

### Rangos de Precio por Ciudad
```
CDMX:
  Mínimo:   $800,000 MXN
  Promedio: $3,200,000 MXN
  Máximo:   $12,500,000 MXN

Guadalajara:
  Mínimo:   $650,000 MXN
  Promedio: $2,400,000 MXN
  Máximo:   $7,800,000 MXN

Monterrey:
  Mínimo:   $900,000 MXN
  Promedio: $3,500,000 MXN
  Máximo:   $9,200,000 MXN

Zapopan:
  Mínimo:   $750,000 MXN
  Promedio: $2,600,000 MXN
  Máximo:   $8,500,000 MXN
```

### Performance del Sistema
```
Tiempo de carga inicial:    3-5 segundos
Tiempo de respuesta API:    < 500ms (promedio)
Tiempo de búsqueda (cache): < 50ms
Tiempo de respuesta chatbot: 3-8 segundos
Uptime del backend:         99.5%
```

---

## 🎓 GLOSARIO DE TÉRMINOS

**API REST:** Interfaz de programación que permite comunicación entre frontend y backend vía HTTP.

**Cache:** Almacenamiento temporal de datos en memoria para acceso rápido sin consultar el servidor.

**Coordenadas (lat/lon):** Latitud y longitud geográfica que identifican una ubicación exacta en el mapa.

**CORS:** Mecanismo de seguridad que controla qué dominios pueden acceder a una API.

**Feature Engineering:** Proceso de crear variables (features) útiles para el modelo ML a partir de datos crudos.

**Heatmap:** Mapa de calor que visualiza densidad o intensidad de datos mediante colores.

**JSON:** Formato de intercambio de datos en texto, usado por APIs para enviar información.

**Machine Learning (ML):** Rama de IA donde algoritmos aprenden patrones de datos sin programación explícita.

**Plusvalía:** Incremento del valor de una propiedad a lo largo del tiempo.

**PostgREST:** Servidor que convierte automáticamente una base de datos PostgreSQL en una API REST.

**Query:** Consulta a una base de datos para obtener información específica.

**R² (R-cuadrado):** Métrica estadística que mide qué tan bien el modelo explica la variación en los datos (0-1).

**Random Forest:** Algoritmo de ML que usa múltiples árboles de decisión para hacer predicciones.

**Regresión:** Tipo de problema ML donde se predice un valor numérico continuo (ej: precio).

**ROI (Return on Investment):** Retorno de inversión, relación entre ganancia y costo.

**Score:** Puntuación o calificación de 0-100 que resume el potencial de inversión.

**SPA (Single Page Application):** Aplicación web que carga una sola página HTML y actualiza dinámicamente.

**Webhook:** URL que recibe datos automáticamente cuando ocurre un evento (ej: mensaje de usuario).

---

## 📝 NOTAS FINALES PARA EL AI AGENT

### Cómo Usar Este Documento

Este documento es tu **fuente única de verdad** sobre el sistema. Cuando un usuario te haga una pregunta:

1. **Busca en este documento primero** (especialmente secciones relevantes como "Cómo Usar", "Preguntas Frecuentes")
2. **Si la respuesta está aquí**, responde con esa información
3. **Si no está**, usa tu conocimiento general + datos de Supabase para ayudar
4. **Siempre sé específico** con números, ejemplos, y citas de este documento

### Tono y Estilo de Respuesta

- **Formal pero amigable** (tú, no usted)
- **Uso moderado de emojis** (1-2 por respuesta)
- **Estructura clara** (listas, negritas, secciones)
- **Ejemplos concretos** cuando expliques conceptos

### Limitaciones Importantes

**NO puedes:**
- ❌ Garantizar resultados de inversión futuros
- ❌ Dar asesoría legal o fiscal
- ❌ Acceder a datos fuera del sistema (ej: registros de propiedad)
- ❌ Modificar datos en la base de datos
- ❌ Procesar transacciones financieras

**SÍ puedes:**
- ✅ Explicar cómo funcionan las predicciones
- ✅ Recomendar propiedades basándote en filtros
- ✅ Comparar opciones de inversión
- ✅ Clarificar conceptos técnicos
- ✅ Guiar en el uso de la aplicación

### Disclaimers que Debes Mencionar

Cuando des recomendaciones de inversión, **siempre** incluye:

> "⚠️ Recuerda: Las predicciones son estimaciones basadas en datos históricos. Siempre verifica con inspección física del terreno y asesoría legal antes de invertir."

### Actualización de Este Documento

Este documento debe actualizarse cuando:
- Se agreguen nuevas ciudades o datos
- Cambie la arquitectura del sistema
- Se implementen nuevas features en la app
- Se modifique el modelo ML

---

**Última actualización:** Octubre 27, 2025  
**Versión del documento:** 1.0  
**Compatibilidad:** Sistema de Análisis Inmobiliario v2.0

---


