# 🤖 WORKFLOW N8N - CHAT DE IA INMOBILIARIO

## **Resumen**

Este workflow permite crear un chat de IA que responde preguntas sobre inversiones inmobiliarias consultando la tabla `ai_chat_predictions` en Supabase.

---

## **Arquitectura del Workflow**

```
Usuario → Webhook (recibe pregunta)
    ↓
OpenAI Chat (interpreta pregunta + genera SQL)
    ↓
Code Node (valida y sanitiza SQL)
    ↓
Supabase (ejecuta consulta)
    ↓
OpenAI Chat (formatea respuesta)
    ↓
Webhook Response (envía respuesta)
```

---

## **Paso 1: Configuración del System Prompt**

### **En el nodo de OpenAI Chat #1 (Interpreter):**

**System Message:**

```
Eres MexInvest AI, un experto en análisis de inversión inmobiliaria en México.

TABLA DISPONIBLE: ai_chat_predictions (10,561 zonas analizadas)

COLUMNAS PRINCIPALES:
- city (Ciudad de México, Guadalajara, Monterrey, Zapopan)
- plusvalia_score (0-100, mayor = mejor inversión)
- investment_rating (Excelente, Muy Buena, Buena, Regular, Baja)
- predicted_price_m2 (precio predicho MXN/m²)
- potential_gain_pct (% ganancia esperada)
- price_vs_zone_pct (% vs promedio zona, negativo = ganga)
- growth_potential (alto, medio, bajo)
- risk_level (bajo, medio, alto)
- confidence_score (0-100, confiabilidad)
- summary, recommendation, map_url

ESTADÍSTICAS:
- Ciudad de México: 3,420 zonas (Score: 76.22, 1,844 top)
- Guadalajara: 2,964 zonas (Score: 21.57)
- Monterrey: 2,496 zonas (Score: 47.72)
- Zapopan: 1,681 zonas (Score: 46.05)

TAREAS:
1. Interpreta la pregunta del usuario
2. Genera una consulta SQL segura a ai_chat_predictions
3. Retorna SOLO el SQL (sin explicaciones)

REGLAS SQL:
- Siempre incluye: city, summary, investment_rating, map_url
- Limita resultados: LIMIT 10 (máximo 20)
- Ordena por plusvalia_score DESC cuando sea relevante
- Filtra investment_rating IN ('Excelente', 'Muy Buena') para "mejores inversiones"

EJEMPLOS:

Usuario: "¿Dónde invertir en Guadalajara?"
SQL:
SELECT city, summary, investment_rating, potential_gain_pct, confidence_score, map_url
FROM ai_chat_predictions
WHERE city = 'Guadalajara' AND investment_rating IN ('Excelente', 'Muy Buena')
ORDER BY plusvalia_score DESC
LIMIT 10;

Usuario: "Busco terreno bajo $50k/m² con alta plusvalía"
SQL:
SELECT city, summary, predicted_price_m2, plusvalia_score, potential_gain_pct, map_url
FROM ai_chat_predictions
WHERE predicted_price_m2 <= 50000 AND plusvalia_score >= 65
ORDER BY plusvalia_score DESC
LIMIT 10;

Usuario: "Compara ciudades"
SQL:
SELECT city, COUNT(*) as total_zonas, ROUND(AVG(plusvalia_score), 2) as score_promedio, 
       ROUND(AVG(predicted_price_m2), 2) as precio_promedio
FROM ai_chat_predictions
GROUP BY city
ORDER BY score_promedio DESC;
```

---

## **Paso 2: Nodo de OpenAI Chat #2 (Formatter)**

**System Message:**

```
Eres MexInvest AI. Formatea los resultados de la consulta SQL en una respuesta amigable.

FORMATO DE RESPUESTA:

Para inversiones individuales:
🏆 [Número]. [Resumen del summary]

📍 Ubicación: [city]
💰 Precio predicho: $[predicted_price_m2 formateado]/m²
⭐ Calificación: [investment_rating]
📈 Ganancia esperada: [potential_gain_pct]%
🎯 Recomendación: [recommendation]

🗺️ Ver en mapa: [map_url]

---

Para comparaciones:
📊 Análisis Comparativo de Ciudades:

🏙️ [Ciudad 1]
- Zonas analizadas: [total_zonas]
- Score promedio: [score]/100
- Precio promedio: $[precio]/m²

...

REGLAS:
1. Usa emojis para hacer la respuesta visual
2. Formatea números con comas (ej: 42,150)
3. Incluye SIEMPRE el link al mapa
4. Si no hay resultados, sugiere alternativas
5. Termina con: "¿Necesitas más información? 🏡"
6. Menciona que son predicciones ML (no garantías)

TONO: Profesional, útil, proactivo, con emojis
```

---

## **Paso 3: Configuración de Supabase**

### **Nodo de Supabase:**

**Operación:** `Execute Query`

**SQL Query:**
```javascript
{{ $json.sql_query }}
```

**Credenciales:**
- URL: Tu URL de Supabase
- Service Role Key: Tu service role key

---

## **Paso 4: Code Node (Validación SQL)**

**Opcional pero recomendado para seguridad:**

```javascript
// Validar que el SQL solo sea SELECT
const sql = $input.first().json.sql_query;

if (!sql.trim().toUpperCase().startsWith('SELECT')) {
  throw new Error('Solo se permiten consultas SELECT');
}

// Prevenir inyección SQL básica
const forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE'];
const sqlUpper = sql.toUpperCase();

for (const word of forbidden) {
  if (sqlUpper.includes(word)) {
    throw new Error(`Operación no permitida: ${word}`);
  }
}

// Limitar número de resultados
if (!sql.includes('LIMIT')) {
  sql += ' LIMIT 10';
}

return {
  json: {
    sql_query: sql,
    validated: true
  }
};
```

---

## **Workflow Completo (JSON Simplificado)**

```json
{
  "name": "Chat AI - Inversiones Inmobiliarias",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "chat-inmobiliario",
        "method": "POST",
        "responseMode": "lastNode"
      }
    },
    {
      "name": "OpenAI Interpreter",
      "type": "@n8n/n8n-nodes-langchain.chatOpenAi",
      "parameters": {
        "model": "gpt-4",
        "messages": [
          {
            "role": "system",
            "content": "[System Prompt del Paso 1]"
          },
          {
            "role": "user",
            "content": "={{ $json.body.message }}"
          }
        ]
      }
    },
    {
      "name": "Code - Validate SQL",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "[Código del Paso 4]"
      }
    },
    {
      "name": "Supabase Query",
      "type": "n8n-nodes-base.supabase",
      "parameters": {
        "operation": "executeQuery",
        "query": "={{ $json.sql_query }}"
      }
    },
    {
      "name": "OpenAI Formatter",
      "type": "@n8n/n8n-nodes-langchain.chatOpenAi",
      "parameters": {
        "model": "gpt-4",
        "messages": [
          {
            "role": "system",
            "content": "[System Prompt del Paso 2]"
          },
          {
            "role": "user",
            "content": "Formatea estos resultados: ={{ JSON.stringify($json) }}"
          }
        ]
      }
    },
    {
      "name": "Respond to Webhook",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ { response: $json.choices[0].message.content } }}"
      }
    }
  ]
}
```

---

## **Paso 5: Integración con Frontend**

### **En Angular (opcional):**

```typescript
// service para el chat
async sendMessageToAI(message: string): Promise<string> {
  const response = await fetch('https://tu-n8n.com/webhook/chat-inmobiliario', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  
  const data = await response.json();
  return data.response;
}
```

---

## **Pruebas de Funcionamiento**

### **Test 1: Pregunta básica**

**Input:**
```json
{
  "message": "¿Dónde invertir en Guadalajara?"
}
```

**Output esperado:**
```
🎯 ¡Encontré excelentes oportunidades en Guadalajara!

🏆 1. Guadalajara Norte - Score: 85/100
📍 Ubicación: Guadalajara, Jalisco
💰 Precio predicho: $42,150/m²
⭐ Calificación: Excelente
...
```

### **Test 2: Presupuesto específico**

**Input:**
```json
{
  "message": "Busco terreno bajo 40 mil pesos por m²"
}
```

**Output esperado:**
```
💰 Encontré 10 zonas bajo $40,000/m²:
...
```

### **Test 3: Comparación**

**Input:**
```json
{
  "message": "Compara CDMX vs Guadalajara"
}
```

**Output esperado:**
```
📊 Análisis Comparativo:

🏙️ Ciudad de México
- 3,420 zonas analizadas
- Score promedio: 76.22/100
...
```

---

## **Mejoras Opcionales**

### **1. Memoria de Conversación**

Agregar un nodo de `Sticky Note` o base de datos para recordar conversaciones previas del usuario.

### **2. Sugerencias Proactivas**

Si no hay resultados, el AI puede sugerir ciudades alternativas o relajar los criterios.

### **3. Notificaciones**

Agregar un nodo de Email o Slack para notificar cuando encuentre una inversión excepcional.

### **4. Rate Limiting**

Limitar a X consultas por usuario/IP por minuto para evitar abuso.

---

## **Costos Estimados (OpenAI)**

**Por consulta:**
- Interpreter (System + User): ~500 tokens (~$0.0025)
- Formatter (System + Data + Response): ~800 tokens (~$0.004)
- **Total por consulta: ~$0.0065 USD**

**Para 1,000 consultas/mes: ~$6.50 USD**

---

## **Troubleshooting**

### **Error: "Cannot read property 'sql_query'"**
- Verifica que el OpenAI Interpreter retorne el SQL correctamente
- Revisa el System Prompt (debe pedir "retorna SOLO el SQL")

### **Error: "Invalid SQL syntax"**
- Activa el Code Node de validación
- Revisa que el prompt genere SQL válido

### **Respuestas vacías:**
- Verifica que la tabla `ai_chat_predictions` tenga datos
- Ejecuta: `SELECT COUNT(*) FROM ai_chat_predictions;`

### **Respuestas lentas (>5s):**
- Usa gpt-3.5-turbo en lugar de gpt-4 (10x más rápido)
- Reduce el tamaño del System Prompt
- Agrega índices en Supabase

---

## **URLs de Referencia**

- **System Prompt completo:** `AI_CHAT_SYSTEM_PROMPT.md`
- **Tabla Supabase:** `ai_chat_predictions`
- **Función de actualización:** `refresh_ai_chat_predictions()`
- **Script SQL:** `14_tabla_chat_ai.sql`

---

**¡El chat de IA está listo para funcionar!** 🚀

