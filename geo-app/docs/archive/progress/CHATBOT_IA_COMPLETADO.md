# 🤖 CHATBOT DE IA INTEGRADO - COMPLETADO

## ✅ **RESUMEN**

Se ha integrado un **chatbot de IA flotante** en la aplicación que se conecta al webhook de n8n.

---

## 📂 **ARCHIVOS CREADOS/MODIFICADOS**

### **Nuevos componentes:**

1. ✅ `app/src/app/components/ai-chatbot/ai-chatbot.component.ts`
2. ✅ `app/src/app/components/ai-chatbot/ai-chatbot.component.html`
3. ✅ `app/src/app/components/ai-chatbot/ai-chatbot.component.css`

### **Archivos modificados:**

4. ✅ `app/src/app/pages/mapa/mapa.component.ts` (agregado import)
5. ✅ `app/src/app/pages/mapa/mapa.component.html` (agregado `<app-ai-chatbot>`)

---

## 🎯 **CARACTERÍSTICAS IMPLEMENTADAS**

### **1. Botón Flotante**
- 💬 Botón circular en la esquina inferior derecha
- Gradient morado/rosa
- Animación de hover
- Icono cambia al abrir/cerrar

### **2. Panel de Chat**
- 📱 Panel de 400x600px (responsive en móvil: 100% pantalla)
- 🎨 Diseño moderno con gradientes y sombras
- ⚡ Animación suave de entrada/salida
- 🔄 Botón para limpiar conversación
- ✕ Botón para cerrar

### **3. Mensajes**
- 👤 Mensajes del usuario (azul/morado, alineados a la derecha)
- 🤖 Mensajes del asistente (blanco, alineados a la izquierda)
- 🕐 Timestamp en cada mensaje
- 📜 Scroll automático al final
- ⏳ Indicador de "escribiendo..." con animación

### **4. Input**
- ✍️ Textarea con auto-resize
- ⌨️ Enter para enviar (Shift+Enter para nueva línea)
- 📤 Botón de enviar con icono
- 🚫 Deshabilitado mientras carga

### **5. Ejemplos de Preguntas**
- 💡 Se muestran solo al inicio
- 3 preguntas de ejemplo clicables:
  - "¿Dónde invertir en Guadalajara?"
  - "Terreno bajo $50k/m²"
  - "Comparar ciudades"

### **6. Integración con n8n**
- 🌐 URL: `https://iagentekn8n.iagentek.com.mx/webhook-test/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea`
- 📮 POST con body: `{"chat imput": "texto"}`
- 📥 Respuesta: `{"respuesta": "texto"}`
- ⚠️ Manejo de errores con mensaje amigable

---

## 🚀 **CÓMO PROBAR**

### **Paso 1: Iniciar el frontend**

```bash
cd geo-app/app
ng serve
```

Abre: http://localhost:4200

### **Paso 2: Probar el chatbot**

1. **Verás un botón flotante** 💬 en la esquina inferior derecha
2. **Haz click** para abrir el chat
3. **Lee el mensaje de bienvenida** del bot
4. **Prueba un ejemplo**: Click en "¿Dónde invertir en Guadalajara?"
5. **Observa**:
   - ⏳ Aparece el indicador "escribiendo..."
   - 🤖 Llega la respuesta del webhook de n8n
   - 📜 El scroll baja automáticamente

### **Paso 3: Probar preguntas propias**

```
Ejemplos de preguntas:
- "plusvalia en guadalajara"
- "mejores zonas en cdmx"
- "terreno barato"
- "compara monterrey y guadalajara"
```

---

## 🧪 **PRUEBAS DE INTEGRACIÓN**

### **Test 1: Envío básico**

**Input del usuario:**
```
plusvalia en guadalajara
```

**Request al webhook:**
```json
POST https://iagentekn8n.iagentek.com.mx/webhook-test/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea
Content-Type: application/json

{
  "chat imput": "plusvalia en guadalajara"
}
```

**Response esperada:**
```json
{
  "respuesta": "🎯 ¡Encontré excelentes oportunidades en Guadalajara!..."
}
```

**Resultado en UI:**
- ✅ Mensaje del usuario aparece en azul
- ✅ Respuesta del bot aparece en blanco
- ✅ Scroll automático al final
- ✅ Timestamp correcto

### **Test 2: Manejo de errores**

**Escenario:** Webhook no responde o error 500

**Resultado esperado:**
```
❌ Lo siento, ocurrió un error al procesar tu consulta. 
Por favor, intenta de nuevo.
```

### **Test 3: Limpieza de conversación**

1. Envía varios mensajes
2. Click en botón 🔄 (limpiar)
3. **Resultado:**
   - ✅ Todos los mensajes se borran
   - ✅ Aparece mensaje "¡Conversación reiniciada! 🔄"

---

## 🎨 **PERSONALIZACIÓN**

### **Cambiar colores del gradiente:**

```css
/* En ai-chatbot.component.css */

/* Botón flotante */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Header del chat */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Mensajes del usuario */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### **Cambiar posición del botón:**

```css
.chat-toggle-btn {
  bottom: 30px;  /* Cambiar aquí */
  right: 30px;   /* Cambiar aquí */
}
```

### **Cambiar tamaño del panel:**

```css
.chat-panel {
  width: 400px;   /* Cambiar aquí */
  height: 600px;  /* Cambiar aquí */
}
```

---

## 🔧 **CONFIGURACIÓN DEL WEBHOOK**

### **URL del webhook (actual):**
```
https://iagentekn8n.iagentek.com.mx/webhook-test/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea
```

### **Para cambiar la URL:**

Edita `ai-chatbot.component.ts` línea 22:

```typescript
private readonly WEBHOOK_URL = 'https://tu-nuevo-webhook.com/endpoint';
```

### **Formato del body:**

**IMPORTANTE:** El webhook espera `"chat imput"` (con el typo "imput" en lugar de "input").

Si necesitas cambiarlo:

```typescript
body: JSON.stringify({
  'chat imput': userMessage  // Cambiar aquí si el webhook espera otro campo
})
```

---

## 📊 **FLUJO DE DATOS**

```
Usuario escribe mensaje
    ↓
Component: ai-chatbot.component.ts
    ↓
sendMessage() agrega mensaje a messages[]
    ↓
fetch() POST al webhook de n8n
    ↓
Body: {"chat imput": "texto del usuario"}
    ↓
n8n procesa con OpenAI + Supabase
    ↓
Response: {"respuesta": "texto generado por IA"}
    ↓
Component: agrega respuesta a messages[]
    ↓
Template: renderiza nuevo mensaje
    ↓
scrollToBottom() automático
```

---

## 🐛 **TROUBLESHOOTING**

### **Problema 1: No aparece el botón flotante**

**Solución:**
- Verifica que `<app-ai-chatbot></app-ai-chatbot>` esté en `mapa.component.html`
- Verifica que `AiChatbotComponent` esté en los `imports` de `mapa.component.ts`
- Recarga la página con Ctrl+F5

### **Problema 2: Error al enviar mensaje**

**Síntomas:**
```
❌ Lo siento, ocurrió un error al procesar tu consulta.
```

**Posibles causas:**
1. Webhook de n8n está caído/inactivo
2. CORS bloqueando la petición
3. URL del webhook incorrecta
4. El webhook no retorna JSON válido

**Verificación:**
```bash
# Probar el webhook directamente con curl
curl -X POST https://iagentekn8n.iagentek.com.mx/webhook-test/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea \
  -H "Content-Type: application/json" \
  -d '{"chat imput": "test"}'
```

### **Problema 3: Respuesta vacía o "undefined"**

**Causa:** El webhook no retorna el campo `"respuesta"`

**Solución:**
Verifica en la consola del navegador (F12 → Network) la respuesta del webhook.

Si el campo es diferente, edita en `ai-chatbot.component.ts`:

```typescript
this.messages.push({
  role: 'assistant',
  content: data.respuesta || 'Sin respuesta',  // Cambiar "respuesta" si el campo es otro
  timestamp: new Date()
});
```

### **Problema 4: El chat no se ve en móvil**

**Solución:**
Ya está implementado el responsive. Verifica que no haya CSS custom que lo esté bloqueando.

---

## 🎯 **PRÓXIMAS MEJORAS (OPCIONAL)**

### **1. Historial de conversaciones**
Guardar conversaciones en localStorage para persistencia.

### **2. Markdown en respuestas**
Parsear markdown en las respuestas del AI (negritas, listas, etc.)

### **3. Botones de acción**
Si el AI sugiere una zona, agregar botón "Ver en mapa" que centre el mapa ahí.

### **4. Sugerencias inteligentes**
Mostrar sugerencias de preguntas basadas en la respuesta anterior.

### **5. Voz**
Agregar reconocimiento de voz para dictar mensajes.

---

## 📚 **DOCUMENTACIÓN RELACIONADA**

- **System Prompt para n8n:** `n8n_workflows/AI_CHAT_SYSTEM_PROMPT.md`
- **Configuración de n8n:** `n8n_workflows/05_chat_ai_workflow.md`
- **Tabla de datos:** `ai_chat_predictions` (script SQL: `scripts_sql/14_tabla_chat_ai.sql`)

---

## ✅ **ESTADO FINAL**

| Componente | Estado | Notas |
|------------|--------|-------|
| 🤖 Chatbot UI | ✅ Completado | Diseño moderno, responsive |
| 🌐 Integración n8n | ✅ Completado | Webhook configurado |
| ⚡ Manejo de errores | ✅ Completado | Mensajes amigables |
| 📱 Responsive | ✅ Completado | Funciona en móvil |
| 🎨 UX/UI | ✅ Completado | Animaciones, gradientes |
| 🧪 Testing | ⏳ Pendiente | Requiere webhook activo |

---

**¡El chatbot está listo para usarse!** 🎉

Ahora solo necesitas que el webhook de n8n esté activo y respondiendo con el formato correcto.

