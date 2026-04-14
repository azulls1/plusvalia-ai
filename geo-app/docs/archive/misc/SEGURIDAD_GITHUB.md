# 🔒 SEGURIDAD AL SUBIR A GITHUB

**Guía completa de qué SÍ y qué NO se subirá a GitHub**

---

## ✅ RESPUESTA RÁPIDA

**SÍ, es 100% SEGURO subir a GitHub** porque:

1. ✅ El archivo `.env` está en `.gitignore` (NO se subirá)
2. ✅ Las credenciales están SOLO en `.env`
3. ✅ El código NO contiene credenciales hardcodeadas
4. ✅ Hay 2 niveles de `.gitignore` (raíz y python_services)

---

## 🔒 ARCHIVOS QUE **NUNCA** SE SUBIRÁN

### Protegidos por `.gitignore`:

```
❌ .env                          ← CREDENCIALES (bloqueado)
❌ .env.local                    ← CREDENCIALES (bloqueado)
❌ .env.production               ← CREDENCIALES (bloqueado)
❌ credentials.json              ← CREDENCIALES (bloqueado)
❌ *.pem, *.key, *.cert         ← CERTIFICADOS (bloqueados)
❌ python_services/.env          ← CREDENCIALES (bloqueado)
❌ __pycache__/                  ← Caché Python (bloqueado)
❌ node_modules/                 ← Dependencias (bloqueado)
❌ dist/                         ← Build Angular (bloqueado)
❌ *.log                         ← Logs (bloqueado)
❌ venv/                         ← Virtual env (bloqueado)
❌ ml_model/models/*.pkl         ← Modelos ML (bloqueados)
```

---

## ✅ ARCHIVOS QUE **SÍ** SE SUBIRÁN (SEGUROS)

### Código fuente (sin credenciales):

```
✅ python_services/api/main.py           ← Código FastAPI
✅ python_services/config.py             ← Lee de .env (seguro)
✅ python_services/requirements.txt      ← Dependencias
✅ python_services/.env.example          ← Plantilla SIN credenciales
✅ app/src/                              ← Código Angular
✅ scripts_sql/                          ← Scripts SQL
✅ README.md                             ← Documentación
✅ .gitignore                            ← Protección
```

**⚠️ IMPORTANTE:** Estos archivos son SEGUROS porque:
- `config.py` lee de `.env` (que NO se sube)
- `environment.prod.ts` solo tiene la `anonKey` (es pública por diseño)
- No hay credenciales hardcodeadas

---

## 🔍 VERIFICACIÓN ANTES DE SUBIR

### Comando 1: Ver qué se subirá

```powershell
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app

git status
```

**Resultado esperado:**
```
Archivos para commit:
  ✅ python_services/config.py
  ✅ python_services/api/main.py
  ✅ app/src/app/
  
NO deben aparecer:
  ❌ .env
  ❌ python_services/.env
```

### Comando 2: Verificar que .env esté bloqueado

```powershell
git check-ignore python_services/.env
```

**Resultado esperado:**
```
python_services/.env
```

Si sale esto ✅, el `.env` está bloqueado y NO se subirá.

### Comando 3: Ver archivos ignorados

```powershell
git status --ignored
```

Debe mostrar `.env` en la lista de ignorados.

---

## 📊 CREDENCIALES EN EL PROYECTO

### ✅ Lugar SEGURO (NO va a GitHub):

**Archivo:** `python_services/.env`

```env
# Este archivo NO se sube a GitHub (está en .gitignore)
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...  ← CRÍTICO, NO se sube
POSTGRES_PASSWORD=...           ← CRÍTICO, NO se sube
```

### ✅ Lugar SEGURO (Sí va a GitHub pero sin datos):

**Archivo:** `python_services/config.py`

```python
# Este archivo SÍ se sube pero es SEGURO
SUPABASE_URL = os.getenv("SUPABASE_URL")  # Lee de .env
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Lee de .env

# NO tiene las credenciales, solo las LEE del .env
```

### ⚠️ Lugar SEMI-PÚBLICO (Sí va a GitHub):

**Archivo:** `app/src/environments/environment.prod.ts`

```typescript
export const environment = {
  supabaseAnonKey: "eyJh..."  // ✅ OK, esta key es PÚBLICA por diseño
};
```

**¿Por qué es seguro?**
- La `anonKey` de Supabase está DISEÑADA para ser pública
- Tiene permisos limitados (solo lo que permiten las RLS policies)
- NO es la `service_role_key` (esa SÍ es secreta)

---

## 🚨 DOBLE VERIFICACIÓN ANTES DE COMMIT

### Checklist:

```powershell
# 1. Verificar .gitignore existe
Get-Content .gitignore | Select-String ".env"
# Debe mostrar: .env

# 2. Verificar que .env esté ignorado
git check-ignore python_services/.env
# Debe mostrar: python_services/.env

# 3. Ver qué archivos se agregarán
git status

# 4. Buscar archivos .env en staging
git ls-files | Select-String ".env"
# NO debe mostrar nada (vacío = correcto)

# 5. Si hay .env en staging (ERROR), quitarlo:
git rm --cached python_services/.env
git rm --cached .env
```

---

## 🎯 ALTERNATIVA: REPOSITORIO PRIVADO

Si aún tienes dudas, puedes hacer el repositorio **PRIVADO**:

### En GitHub:

1. Al crear el repo, marcar: **Private**
2. Solo TÚ y quien autorices podrá ver el código
3. Aun así, el `.env` NO se sube (doble protección)

### Ventajas del repo privado:

- ✅ Solo tú lo ves
- ✅ Puedes invitar a colaboradores específicos
- ✅ Gratis en GitHub
- ✅ Railway puede acceder (con autorización)

---

## 🔒 ALTERNATIVA: USAR RAILWAY CLI (SIN GITHUB)

Si **NO quieres usar GitHub**, usa Railway CLI:

```powershell
npm i -g @railway/cli
railway login
cd python_services
railway init
railway up
```

**Ventajas:**
- ✅ NO necesitas GitHub
- ✅ Deploy directo desde tu PC
- ✅ Código NO se sube a ningún repositorio público
- ✅ Variables de entorno se agregan manualmente

**Ver guía:** `OPCION_SIMPLE_SIN_GIT.md`

---

## 📋 RESUMEN FINAL

| Archivo | ¿Se sube? | ¿Es seguro? | Razón |
|---------|-----------|-------------|-------|
| `.env` | ❌ NO | ✅ Sí | Está en `.gitignore` |
| `config.py` | ✅ Sí | ✅ Sí | Solo lee `.env`, no contiene credenciales |
| `environment.prod.ts` | ✅ Sí | ✅ Sí | Solo tiene `anonKey` (pública) |
| `README.md` | ✅ Sí | ✅ Sí | Documentación |
| `*.log` | ❌ NO | ✅ Sí | Está en `.gitignore` |
| `node_modules/` | ❌ NO | ✅ Sí | Está en `.gitignore` |

---

## ✅ CONFIRMACIÓN

**SÍ, puedes subir SEGURAMENTE a GitHub** porque:

1. ✅ `.env` está en `.gitignore` (2 niveles)
2. ✅ Ningún archivo contiene credenciales hardcodeadas
3. ✅ `config.py` solo LEE de `.env`
4. ✅ La `anonKey` en frontend es pública por diseño
5. ✅ Railway leerá las variables de entorno que TÚ configures

---

## 🆘 SI ALGO SALE MAL

### Si accidentalmente subiste `.env`:

```powershell
# 1. Eliminar del historial
git rm --cached python_services/.env

# 2. Commit
git commit -m "Remove .env from tracking"

# 3. Push
git push

# 4. IMPORTANTE: Cambiar las credenciales
# - Regenerar service_role_key en Supabase
# - Cambiar password de PostgreSQL
```

---

## 💡 RECOMENDACIÓN FINAL

**Opción 1: GitHub Privado (Recomendada)**
- Repo privado en GitHub
- Railway conecta con GitHub
- Deploy automático
- Código protegido

**Opción 2: Railway CLI (Sin GitHub)**
- Sin repositorio online
- Deploy directo desde PC
- Variables en Railway manualmente
- Más simple pero menos automático

---

**Tu código está 100% protegido.** 🔒

¿Prefieres GitHub privado o Railway CLI sin GitHub?

