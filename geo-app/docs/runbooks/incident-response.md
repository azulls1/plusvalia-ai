# Runbook: Incident Response

## 1. Deteccion

### Fuentes de alertas
- Prometheus/Grafana alertas automaticas
- Health check failures (Docker)
- Error rate spikes en logs
- Reporte de usuario

### Criterios de severidad
| Severidad | Descripcion | Ejemplo |
|-----------|-------------|---------|
| P1 | Servicio completamente caido | API no responde, frontend 5xx |
| P2 | Degradacion severa | >50% requests fallando, latencia >10s |
| P3 | Degradacion parcial | Feature especifica falla, latencia elevada |
| P4 | Issue menor | Bug cosmético, log warnings |

## 2. Respuesta Inmediata (primeros 5 minutos)

### P1/P2 — Pasos:
```bash
# 1. Verificar estado de contenedores
docker ps -a
docker logs --tail 50 geo-api

# 2. Verificar health check
curl -f http://localhost:8000/health

# 3. Verificar conectividad DB
curl -f https://iagenteksupabase.iagentek.com.mx/rest/v1/

# 4. Si contenedor caido, reiniciar
docker restart geo-api

# 5. Si persiste, rollback
bash scripts/rollback.sh <version-anterior>
```

### P3/P4 — Pasos:
```bash
# 1. Revisar logs recientes
docker logs --tail 200 --since 30m geo-api

# 2. Verificar metricas
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# 3. Identificar endpoint problematico
grep "ERROR" logs/api.log | tail -20
```

## 3. Diagnostico

### Checklist de diagnostico
- [ ] Contenedores corriendo? (`docker ps`)
- [ ] Health check pasando? (`/health`)
- [ ] Base de datos accesible? (Supabase status)
- [ ] Modelo ML cargado? (`/health` incluye model_loaded)
- [ ] Disco lleno? (`df -h`)
- [ ] Memoria agotada? (`docker stats`)
- [ ] Rate limit alcanzado? (revisar logs 429)
- [ ] Certificado SSL expirado? (`curl -vI https://...`)
- [ ] DNS resolviendo? (`nslookup domain`)

## 4. Mitigacion

### Rollback rapido
```bash
# Rollback a version anterior
bash scripts/rollback.sh v1.0.0

# Verificar despues del rollback
curl -f http://localhost:8000/health
curl -f http://localhost:8000/docs
```

### Escalar recursos
```bash
# Aumentar replicas
docker service scale geo-api=3

# Aumentar memoria
docker update --memory=4g geo-api
```

### Deshabilitar feature problematica
```bash
# Si es un endpoint especifico, deshabilitarlo temporalmente
# via variable de entorno
docker update --env-add DISABLE_PREDICTIONS=true geo-api
```

## 5. Resolucion

- Identificar root cause
- Implementar fix
- Verificar fix en staging (si aplica)
- Deploy fix
- Verificar metricas post-fix (15 min)

## 6. Post-Mortem (obligatorio para P1/P2)

### Template:
```markdown
# Post-Mortem: [Titulo del Incidente]
- Fecha: YYYY-MM-DD
- Duracion: X minutos
- Severidad: P1/P2
- Impacto: X usuarios afectados

## Timeline
- HH:MM — Deteccion
- HH:MM — Inicio respuesta
- HH:MM — Mitigacion
- HH:MM — Resolucion completa

## Root Cause
[Descripcion detallada]

## Que salio bien
- [Item]

## Que salio mal
- [Item]

## Action Items
- [ ] [Accion preventiva 1] — Owner: X — Deadline: YYYY-MM-DD
- [ ] [Accion preventiva 2] — Owner: X — Deadline: YYYY-MM-DD
```

## 7. Contactos

| Rol | Nombre | Contacto |
|-----|--------|----------|
| Lead Developer | Samael Hernandez | admin@iagentek.com.mx |
| Escalacion | Via n8n webhook alert | https://iagentekn8nwebhook.iagentek.com.mx/webhook/alertmanager |
| Monitoreo | Grafana | https://grafana.iagentek.com.mx |
| Hosting (Hostinger) | Soporte | https://www.hostinger.com/cpanel-login |
| Supabase | Status page | https://status.supabase.com |
