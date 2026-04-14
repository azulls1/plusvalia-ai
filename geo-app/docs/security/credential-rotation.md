# Credential Rotation Guide

## API Key Rotation

1. Generate new key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Update `.env` on VPS: `API_KEY=<new_key>`
3. Update Docker secret: `echo "<new_key>" | docker secret create api_key_v2 -`
4. Restart backend: `docker compose -f docker-compose.production.yml up -d --no-deps backend-api`
5. Update any client applications using the old key

## Supabase Key Rotation

1. Access Supabase dashboard: https://iagenteksupabase.iagentek.com.mx
2. Navigate to Settings > API
3. Generate new anon/service keys
4. Update `.env` with new keys
5. Update `environment.ts` and `environment.prod.ts` with new anon key
6. Rebuild and redeploy frontend

## Rotation Schedule

| Credential | Frequency | Last Rotated |
|-----------|-----------|-------------|
| API_KEY | Every 90 days | 2026-03-25 |
| Supabase Anon Key | Every 180 days | - |
| Supabase Service Role | Every 180 days | - |
| PostgreSQL Password | Every 90 days | 2026-03-25 |

## Emergency Rotation

If a credential is compromised:
1. Immediately rotate the affected credential
2. Check audit logs for unauthorized access
3. Review `/predictions/history` for suspicious entries
4. File incident report per runbook
