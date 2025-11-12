# Deployment Checklist

**Live Conversational Threads**
**Version**: Weeks 1-14 Complete
**Date**: November 12, 2025

## Pre-Deployment Checklist

### ✅ Code Quality

- [x] All features implemented (Weeks 1-14)
- [x] Unit tests passing
- [x] Integration tests passing
- [x] No critical bugs
- [x] Code reviewed
- [x] Documentation complete

### ✅ Database

- [x] Migrations created
- [x] Migration tested (upgrade)
- [x] Migration tested (downgrade/rollback)
- [x] Indexes created
- [x] Constraints validated
- [ ] **TODO**: Run migration on staging
- [ ] **TODO**: Verify data integrity

### ✅ Backend

- [x] API endpoints implemented
- [x] Error handling complete
- [x] Environment variables documented
- [ ] **TODO**: API keys secured in secrets manager
- [ ] **TODO**: Rate limiting configured
- [ ] **TODO**: CORS settings for production

### ✅ Frontend

- [x] All routes configured
- [x] Navigation complete
- [x] Error handling
- [x] Loading states
- [ ] **TODO**: Build optimized for production
- [ ] **TODO**: CDN configuration

### ⚠️ Security

- [ ] **TODO**: HTTPS enabled
- [ ] **TODO**: API keys in environment variables (not hardcoded)
- [ ] **TODO**: Database credentials secured
- [ ] **TODO**: CORS configured for production domain
- [ ] **TODO**: SQL injection prevention verified
- [ ] **TODO**: XSS protection enabled

### ⚠️ Monitoring

- [ ] **TODO**: Error tracking (Sentry/similar)
- [ ] **TODO**: Performance monitoring
- [ ] **TODO**: Cost tracking dashboard
- [ ] **TODO**: Alert thresholds configured
- [ ] **TODO**: Log aggregation setup

### ⚠️ Backup & Recovery

- [ ] **TODO**: Database backup strategy
- [ ] **TODO**: Point-in-time recovery tested
- [ ] **TODO**: Disaster recovery plan documented
- [ ] **TODO**: Backup restoration tested

---

## Deployment Steps

### 1. Staging Environment

#### Backend Staging

```bash
# 1. Clone repository
git clone <repo-url>
cd live_conversational_threads/lct_python_backend

# 2. Setup Python environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with staging credentials

# 5. Run migrations
alembic upgrade head

# 6. Test connection
python -c "from database import get_session; print('DB connection OK')"

# 7. Start server (test mode)
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload

# 8. Verify health endpoint
curl http://localhost:8000/health
```

#### Frontend Staging

```bash
# 1. Navigate to frontend
cd lct_app

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with staging API URL

# 4. Build for staging
npm run build

# 5. Test build
npm run preview

# 6. Verify routes
# Visit http://localhost:4173 and test all pages
```

### 2. Database Migration (Staging)

```bash
cd lct_python_backend

# 1. Backup database
pg_dump -h localhost -U user lct_staging > backup_pre_migration.sql

# 2. Run migration
alembic upgrade head

# 3. Verify tables created
psql -h localhost -U user lct_staging -c "\dt"

# Expected tables:
# - conversations
# - nodes
# - utterances
# - relationships
# - clusters
# - simulacra_analysis (NEW)
# - bias_analysis (NEW)
# - frame_analysis (NEW)
# - edits_log
# - api_calls_log

# 4. Verify indexes
psql -h localhost -U user lct_staging -c "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';"

# 5. Test rollback (on copy)
alembic downgrade -1
alembic upgrade head
```

### 3. Integration Testing (Staging)

```bash
# Run all backend tests
cd lct_python_backend
pytest -v

# Expected: 35 passing, 6 skipped

# Run integration tests specifically
pytest tests/test_integration_all_features.py -v

# Run service tests
pytest tests/test_simulacra_detector.py -v
pytest tests/test_bias_detector.py -v
pytest tests/test_frame_detector.py -v

# Check coverage
pytest --cov=. --cov-report=term
```

### 4. Smoke Tests (Staging)

**Manual Testing Checklist**:

- [ ] Import a Google Meet transcript
- [ ] View conversation graph
- [ ] Click "Analysis 📊" dropdown
- [ ] Navigate to Speaker Analytics
- [ ] Navigate to Edit History
- [ ] Navigate to Simulacra Analysis
  - [ ] Click "Run Analysis"
  - [ ] Verify results display
  - [ ] Check node details
- [ ] Navigate to Bias Analysis
  - [ ] Click "Run Analysis"
  - [ ] Verify category distribution
  - [ ] Filter by category
  - [ ] Filter by bias type
- [ ] Navigate to Frame Analysis
  - [ ] Click "Run Analysis"
  - [ ] Verify category distribution
  - [ ] Check assumptions and implications
  - [ ] Filter by category and frame type
- [ ] Verify all navigation links work
- [ ] Test responsive design (mobile/tablet)
- [ ] Check browser console for errors

### 5. Production Deployment

#### Backend Production

```bash
# 1. Setup production environment
# (Same steps as staging, but with production credentials)

# 2. Environment variables
# .env
DATABASE_URL=postgresql://user:pass@prod-db:5432/lct_production
ANTHROPIC_API_KEY=<production-key>
BACKEND_API_URL=https://api.yourdomain.com
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 3. Run migrations
alembic upgrade head

# 4. Start server (production mode)
gunicorn backend:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Production

```bash
# 1. Configure production environment
# .env.production
VITE_BACKEND_API_URL=https://api.yourdomain.com
VITE_API_URL=https://api.yourdomain.com

# 2. Build for production
npm run build

# 3. Deploy static files
# - Upload dist/ to CDN (CloudFlare, Netlify, Vercel)
# - Or serve via nginx/Apache
```

### 6. Post-Deployment Verification

```bash
# Backend health check
curl https://api.yourdomain.com/health

# Test endpoints
curl https://api.yourdomain.com/api/conversations/

# Check logs
tail -f /var/log/lct/backend.log

# Monitor errors
# Check Sentry dashboard (if configured)
```

### 7. Rollback Plan (If Needed)

```bash
# Backend rollback
alembic downgrade -1

# Restore database from backup
psql -h localhost -U user lct_production < backup_pre_migration.sql

# Restart with previous version
git checkout <previous-tag>
uvicorn backend:app --reload

# Frontend rollback
# Re-deploy previous dist/ folder
```

---

## Performance Benchmarks

### Target Metrics

**Backend**:
- API latency p50: < 500ms
- API latency p95: < 2000ms
- Database query time: < 100ms
- Analysis time per node: 2-4 seconds

**Frontend**:
- Initial load time: < 3 seconds
- Graph render time: < 500ms
- Navigation transition: < 200ms

### Load Testing (Optional)

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test endpoint
ab -n 1000 -c 10 https://api.yourdomain.com/api/conversations/

# Expected:
# - Requests per second: > 50
# - Time per request: < 200ms
# - Failed requests: 0
```

---

## Monitoring Setup

### Recommended Tools

1. **Error Tracking**: Sentry
   - Backend: `pip install sentry-sdk`
   - Frontend: `npm install @sentry/react`

2. **Performance Monitoring**: Datadog / New Relic
   - APM for backend
   - RUM for frontend

3. **Cost Tracking**: Custom dashboard
   - Query `api_calls_log` table
   - Aggregate by day/week/month
   - Alert on threshold breaches

### Alerting Rules

```yaml
# Example alert configuration
alerts:
  - name: high_error_rate
    condition: error_rate > 5%
    severity: critical
    channel: pagerduty

  - name: high_api_cost
    condition: daily_cost > $100
    severity: warning
    channel: email, slack

  - name: slow_api_response
    condition: p95_latency > 5000ms
    severity: warning
    channel: slack

  - name: database_connection_pool_exhaustion
    condition: pool_usage > 80%
    severity: critical
    channel: pagerduty
```

---

## Security Hardening

### Backend Security

```python
# backend.py

# 1. Enable CORS for production domain only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # NOT "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 2. Add rate limiting
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/conversations/{id}/simulacra/analyze")
@limiter.limit("10/minute")  # Max 10 analyses per minute
async def analyze_simulacra(...):
    ...

# 3. Validate input
from pydantic import BaseModel, validator

class AnalysisRequest(BaseModel):
    conversation_id: str

    @validator('conversation_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID')
        return v
```

### Environment Variables

```bash
# NEVER commit these
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...

# Use secrets manager in production
# - AWS Secrets Manager
# - Google Cloud Secret Manager
# - HashiCorp Vault
```

---

## Backup Strategy

### Database Backups

```bash
# Daily full backup
0 2 * * * pg_dump -h localhost -U user lct_production > /backups/lct_$(date +\%Y\%m\%d).sql

# Compress backups
0 3 * * * gzip /backups/lct_$(date +\%Y\%m\%d).sql

# Upload to cloud storage
0 4 * * * aws s3 cp /backups/lct_$(date +\%Y\%m\%d).sql.gz s3://lct-backups/

# Retention: Keep 90 days
0 5 * * * find /backups -name "lct_*.sql.gz" -mtime +90 -delete
```

### Application Backups

```bash
# Git tags for releases
git tag -a v1.0-weeks-1-14 -m "Weeks 1-14 complete"
git push origin v1.0-weeks-1-14

# Store configuration
tar -czf config_backup.tar.gz .env* alembic.ini

# Upload to secure location
aws s3 cp config_backup.tar.gz s3://lct-backups/config/
```

---

## Cost Management

### Budget Alerts

```python
# Set daily cost threshold
DAILY_COST_THRESHOLD = 50.00  # USD

# Monitor in real-time
SELECT SUM(cost_usd) as daily_cost
FROM api_calls_log
WHERE DATE(timestamp) = CURRENT_DATE;

# Alert if exceeded
if daily_cost > DAILY_COST_THRESHOLD:
    send_alert("Daily cost threshold exceeded: ${daily_cost}")
```

### Cost Optimization Tips

1. **Cache aggressively**: Store analysis results, don't re-run
2. **Confidence threshold**: Only return high-confidence results
3. **Batch processing**: Analyze multiple nodes in single API call (future)
4. **Model selection**: Use GPT-3.5-turbo for simpler tasks (future)

---

## Success Criteria

### MVP Launch (Post-Week 14)

- [ ] All features deployed and working
- [ ] No P0 bugs
- [ ] Performance meets targets
- [ ] Documentation complete
- [ ] 10 beta users onboarded
- [ ] Cost per conversation < $3.00
- [ ] User satisfaction > 4/5

### Production Ready

- [ ] Security audit passed
- [ ] Load testing passed
- [ ] Monitoring configured
- [ ] Alerting working
- [ ] Backup/recovery tested
- [ ] Rollback plan documented
- [ ] On-call rotation established

---

## Support & Maintenance

### Regular Maintenance

**Daily**:
- Check error logs
- Monitor cost dashboard
- Review alert notifications

**Weekly**:
- Review performance metrics
- Check backup integrity
- Update dependencies (security patches)

**Monthly**:
- Review user feedback
- Optimize slow queries
- Update documentation
- Test disaster recovery

### Issue Response

**P0 (Critical)** - Respond immediately:
- System down
- Data loss
- Security breach

**P1 (High)** - Respond within 4 hours:
- Feature broken
- Analysis failing
- API errors

**P2 (Medium)** - Respond within 24 hours:
- UI bugs
- Slow performance
- Non-critical errors

**P3 (Low)** - Respond within 1 week:
- Feature requests
- Documentation updates
- Minor improvements

---

## Contact & Escalation

### Support Team
- **Email**: support@yourdomain.com
- **Slack**: #lct-support
- **On-call**: PagerDuty rotation

### Escalation Path
1. **L1 Support**: Handle common issues, follow runbooks
2. **L2 Engineering**: Debug complex issues
3. **L3 Architect**: System-wide issues, architectural decisions

---

**Checklist Last Updated**: November 12, 2025
**Version**: Weeks 1-14 Complete
**Status**: Ready for staging deployment
