# Backup & Recovery Strategy — geo-app

## Data Tiers

### Tier 1: Critical (Supabase Managed)
- **Tables**: iainmobiliaria_predictions, iainmobiliaria_comparables, iainmobiliaria_amenities
- **Backup**: Supabase automatic daily backups (managed)
- **Retention**: 7 days (Supabase Pro plan)
- **Recovery**: Supabase Dashboard → Database → Backups → Restore

### Tier 2: ML Models
- **Files**: `ml_model/models/plusvalia_model_*.pkl`
- **Backup**: Model files are versioned with timestamps
- **Strategy**: Keep last 5 model versions on disk
- **Recovery**: Retrain with `/train` endpoint or load previous .pkl

### Tier 3: Configuration
- **Files**: `.env`, `docker-compose.production.yml`, `monitoring/*.yml`
- **Backup**: Version controlled in Git
- **Recovery**: `git checkout` to restore any configuration

## Recovery Procedures

### Full Database Restore
1. Go to Supabase Dashboard → Database → Backups
2. Select the backup point
3. Click "Restore" → confirms destructive operation
4. Wait for restore to complete (~5-15 min)
5. Restart backend: `docker service update --force geo-app_backend-api`
6. Verify: `curl http://localhost:8000/stats`

### ML Model Rollback
1. List available models: `ls -la ml_model/models/`
2. Identify the previous working model
3. Update startup to load specific model, or:
4. Retrain: `curl -X POST http://localhost:8000/train -d '{"force_retrain": true}'`

### Configuration Recovery
1. `git log --oneline -- docker-compose.production.yml`
2. `git checkout <commit-hash> -- docker-compose.production.yml`
3. Redeploy: `docker stack deploy -c docker-compose.production.yml geo-app`

## Testing Backups
- Monthly: Verify Supabase backup exists and is recent
- Quarterly: Test restore to staging environment
- After model retrain: Verify new model produces reasonable predictions
