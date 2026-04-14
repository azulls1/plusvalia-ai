# SLA/SLO — IAInmobiliaria

## Service Level Objectives (SLOs)

| Servicio | Metrica | Objetivo | Ventana |
|----------|---------|----------|---------|
| Frontend (Angular) | Disponibilidad | 99.5% | Mensual |
| API ML (FastAPI) | Disponibilidad | 99.0% | Mensual |
| API ML (FastAPI) | Latencia P50 | < 200ms | Mensual |
| API ML (FastAPI) | Latencia P95 | < 1000ms | Mensual |
| API ML (FastAPI) | Latencia P99 | < 3000ms | Mensual |
| API ML (FastAPI) | Error Rate | < 1% | Mensual |
| Supabase (PostgREST) | Disponibilidad | 99.9% (managed) | Mensual |
| n8n Webhooks | Disponibilidad | 98.0% | Mensual |
| ML Predictions | Accuracy (R²) | > 0.75 | Por retraining |
| ML Predictions | MAE | < $5,000 MXN/m² | Por retraining |

## Error Budget

| Servicio | SLO | Error Budget (mes) | Accion si se agota |
|----------|-----|--------------------|--------------------|
| Frontend | 99.5% | 3.6 horas | Freeze deploys, fix bugs |
| API ML | 99.0% | 7.2 horas | Rollback, escalar |
| n8n | 98.0% | 14.4 horas | Revisar workflows |

## Metricas de Resiliencia

| Metrica | Objetivo | Medicion |
|---------|----------|----------|
| MTTR (Mean Time To Recovery) | < 30 minutos | Promedio incidentes |
| MTBF (Mean Time Between Failures) | > 720 horas (30 dias) | Promedio entre fallos |
| RTO (Recovery Time Objective) | < 1 hora | Tiempo max para recovery |
| RPO (Recovery Point Objective) | < 24 horas | Perdida de datos max |

## Escalamiento

| Nivel | Condicion | Accion |
|-------|-----------|--------|
| P1 - Critico | Servicio caido completamente | Notificar inmediatamente, rollback |
| P2 - Alto | Error rate > 5% | Investigar en 30 min |
| P3 - Medio | Latencia P95 > 2s | Investigar en 2 horas |
| P4 - Bajo | Alerta de capacidad | Planificar scaling |

## Revision

- Revision mensual de SLOs vs metricas reales
- Ajustar objetivos segun historico
- Postmortem obligatorio para incidentes P1/P2
