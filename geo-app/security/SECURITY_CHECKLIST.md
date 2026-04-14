# Security Checklist — geo-app (InmoGeo MVP)

> Last updated: 2026-03-23
> Owner: Security Team / DevOps Lead

---

## Pre-Deploy Checklist

Complete **every** item before any production deployment:

- [ ] **1. No secrets in source code** — Verify `.env` files are in `.gitignore` and not committed. Run `git log --all -p -- '*.env'` to confirm no historical leaks.
- [ ] **2. Environment variables configured** — All values in `.env.example` have corresponding real values set in the deployment environment (hosting panel, Docker secrets, etc.).
- [ ] **3. Service role key restricted** — `SUPABASE_SERVICE_ROLE_KEY` is ONLY used server-side (python_services). It must NEVER appear in frontend code or browser-accessible files.
- [ ] **4. Supabase anon key scoped** — The anon key used in the frontend has RLS policies enforcing read-only access to public data only.
- [ ] **5. RLS enabled on ALL tables** — Run `scripts_sql/17_reenable_rls_ml_tables.sql` and verify with `SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'iainmobiliaria_%';`
- [ ] **6. Security headers active** — Test with https://securityheaders.com/ — target grade A or A+.
- [ ] **7. HTTPS enforced** — All HTTP traffic redirects to HTTPS (301). HSTS header present with `max-age >= 31536000`.
- [ ] **8. Dependency audit clean** — Run `security/dependency-audit.sh`. No critical or high vulnerabilities in production dependencies.
- [ ] **9. File upload validation** — Only CSV files accepted, max 5MB, MIME type validated server-side and client-side.
- [ ] **10. n8n webhooks secured** — Webhook URLs use authentication tokens or IP allowlists. No unauthenticated public endpoints.
- [ ] **11. Database password strength** — Minimum 20 characters, mixed case, numbers, symbols. No dictionary words.
- [ ] **12. API rate limiting active** — Both client-side interceptor and server-side middleware enforce request limits.
- [ ] **13. Error messages sanitized** — No stack traces, internal paths, or database errors exposed to end users.
- [ ] **14. Logging configured** — Logs written to file (not stdout in production). No sensitive data (passwords, tokens) in logs.
- [ ] **15. CORS configured** — Only allow requests from known origins (your frontend domain).

---

## Credential Rotation Procedure

Rotate credentials on this schedule or immediately after any suspected breach:

| Credential | Rotation Frequency | How to Rotate |
|---|---|---|
| Supabase anon key | Every 90 days | Supabase Dashboard > Settings > API > Regenerate |
| Supabase service role key | Every 90 days | Same as above — update python_services/.env |
| PostgreSQL password | Every 90 days | `ALTER ROLE postgres.iagenteksupabase WITH PASSWORD 'new-password';` then update .env |
| INEGI API token | Every 180 days | Request new token from INEGI portal |
| n8n webhook URLs | After any breach | Regenerate webhook IDs in n8n workflow editor |

### Steps After Rotation:
1. Update the `.env` file on the deployment server (NOT in the repo).
2. Restart the affected services (python_services, n8n).
3. Verify the application works with new credentials.
4. Invalidate/delete the old credentials if possible.
5. Document the rotation in the security log.

---

## Incident Response Steps

If a security breach is suspected:

### 1. Contain (0–15 minutes)
- Immediately rotate ALL credentials listed above.
- Disable the Supabase service role key.
- Set n8n workflows to inactive.
- If the database is compromised, revoke public access at the firewall level.

### 2. Assess (15–60 minutes)
- Check Supabase logs: Dashboard > Logs > API / Auth / Database.
- Review n8n execution history for unauthorized calls.
- Check python_services logs at `logs/app.log`.
- Determine what data was accessed or modified.

### 3. Eradicate (1–4 hours)
- Identify the vulnerability that was exploited.
- Patch the vulnerability (code fix, configuration change).
- Scan the codebase with `git log --diff-filter=A -- '*.env' '*.key' '*.pem'` for accidental secret commits.
- Run `pip-audit` and `npm audit` for dependency vulnerabilities.

### 4. Recover (4–24 hours)
- Deploy the patched version.
- Re-enable services one at a time, monitoring for anomalies.
- Restore data from backup if necessary (Supabase point-in-time recovery).
- Verify RLS policies are active on all tables.

### 5. Post-Incident (24–72 hours)
- Write a post-mortem document.
- Update this checklist with lessons learned.
- Notify stakeholders per applicable regulations.
- Schedule a review meeting.

---

## Security Contacts

| Role | Name | Email | Phone |
|---|---|---|---|
| Project Lead | [YOUR NAME] | [email] | [phone] |
| DevOps / Infra | [YOUR NAME] | [email] | [phone] |
| Supabase Admin | [YOUR NAME] | [email] | [phone] |
| External Security | [CONSULTANT] | [email] | [phone] |

---

## References

- [OWASP Top 10 (2021)](https://owasp.org/www-project-top-ten/)
- [Supabase Security Best Practices](https://supabase.com/docs/guides/platform/going-into-prod)
- [Angular Security Guide](https://angular.io/guide/security)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
