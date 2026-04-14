# Operations Runbook — geo-app

## Service Architecture
- **Frontend**: Angular 16 (static files served via CDN/Nginx)
- **Backend API**: FastAPI on port 8000 (Docker container)
- **Database**: Supabase (managed PostgreSQL + RLS)
- **Monitoring**: Prometheus + Grafana + Alertmanager
- **Proxy**: Traefik (reverse proxy + TLS)

## Health Check Endpoints
- Backend: `GET /health` → expects `{"status": "healthy"}`
- Prometheus: `GET localhost:9090/-/healthy`
- Grafana: `GET localhost:3000/api/health`

## Common Incidents

### Backend API Down (P1)
1. Check container status: `docker ps | grep backend-api`
2. Check logs: `docker logs backend-api --tail 100`
3. Check health: `curl -s http://localhost:8000/health`
4. If OOM: increase memory limit in docker-compose.production.yml
5. Restart: `docker service update --force geo-app_backend-api`
6. If persists: rollback to previous image tag

### High Latency (P2)
1. Check Grafana dashboard for API latency
2. Check Prometheus: `rate(http_request_duration_seconds_sum[5m])`
3. Common causes: large Supabase queries, model loading
4. Mitigation: clear prediction cache, restart API

### Model Prediction Errors (P2)
1. Check logs: `docker logs backend-api | grep "Error en predicción"`
2. Verify model is loaded: `curl http://localhost:8000/health | jq .model_loaded`
3. If model not loaded: check `/app/ml_model/models/` directory
4. Retrain: `POST /train {"force_retrain": true, "min_samples": 50}`

### Database Connection Issues (P1)
1. Check Supabase status page
2. Verify env vars: `docker exec backend-api env | grep SUPABASE`
3. Test connection from container: `docker exec backend-api python -c "from config import SUPABASE_URL; print(SUPABASE_URL)"`

### Alertmanager Not Sending Alerts (P3)
1. Check Alertmanager: `curl http://localhost:9093/-/healthy`
2. Check config: `docker exec alertmanager cat /etc/alertmanager/alertmanager.yml`
3. Verify webhook URL is reachable

## Escalation
- P1 (Service Down): Immediate response, <15 min
- P2 (Degraded): Response within 1 hour
- P3 (Non-critical): Next business day

## SLO Definitions
- **Availability**: 99.5% uptime (measured monthly)
- **Latency P95**: < 500ms for /health, < 2s for /predict
- **Error Rate**: < 1% of requests return 5xx
- **Recovery Time (MTTR)**: < 30 minutes for P1 incidents
