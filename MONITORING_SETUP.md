# Monitoring & Alerting Setup Guide

**Production Deployment**: Essential monitoring and alerting configuration

## Overview

This guide covers setting up comprehensive monitoring for Live Conversational Threads in production, including error tracking, performance monitoring, cost alerts, and log aggregation.

## Table of Contents

1. [Error Tracking (Sentry)](#1-error-tracking-sentry)
2. [Performance Monitoring](#2-performance-monitoring)
3. [Cost Tracking Alerts](#3-cost-tracking-alerts)
4. [Log Aggregation](#4-log-aggregation)
5. [Health Checks](#5-health-checks)
6. [Alerting Rules](#6-alerting-rules)
7. [Dashboard Setup](#7-dashboard-setup)

---

## 1. Error Tracking (Sentry)

### Backend Setup (Python/FastAPI)

```bash
# Install Sentry SDK
cd lct_python_backend
pip install sentry-sdk[fastapi]
```

**Add to `backend.py`:**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
    environment=os.getenv("ENVIRONMENT", "development"),
    release=os.getenv("GIT_COMMIT", "unknown"),
)
```

### Frontend Setup (React)

```bash
# Install Sentry SDK
cd lct_app
npm install --save @sentry/react
```

**Add to `src/main.jsx`:**

```javascript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay(),
  ],
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  environment: import.meta.env.VITE_ENVIRONMENT || "development",
});
```

### Environment Variables

```bash
# .env
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=production
GIT_COMMIT=$(git rev-parse HEAD)
```

---

## 2. Performance Monitoring

### Built-in Benchmarking

Use the included `performance_benchmark.py`:

```bash
cd lct_python_backend
python performance_benchmark.py
```

This provides:
- Database query performance
- LLM API call latency
- Data processing times
- Feature-specific benchmarks

### Custom Performance Tracking

**Add to backend endpoints:**

```python
import time

@lct_app.middleware("http")
async def track_performance(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    response.headers["X-Process-Time"] = str(duration)

    # Log slow requests
    if duration > 5.0:  # 5 seconds
        print(f"[SLOW REQUEST] {request.url.path} took {duration:.2f}s")

    return response
```

### Prometheus Metrics (Optional)

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

# Add to backend.py after app creation
Instrumentator().instrument(app).expose(app)
```

Access metrics at: `http://localhost:8000/metrics`

---

## 3. Cost Tracking Alerts

### Backend Configuration

**Add to `backend.py`:**

```python
from datetime import datetime, timedelta

# Daily cost threshold (USD)
DAILY_COST_THRESHOLD = float(os.getenv("DAILY_COST_THRESHOLD", "50.0"))

async def check_daily_costs():
    """Check if daily costs exceed threshold"""
    today = datetime.now().date()

    # Query api_calls_log for today's costs
    result = await db.execute(
        text("""
            SELECT SUM(cost_usd) as daily_cost
            FROM api_calls_log
            WHERE DATE(timestamp) = :today
        """),
        {"today": today}
    )

    daily_cost = result.scalar() or 0.0

    if daily_cost > DAILY_COST_THRESHOLD:
        # Send alert
        await send_cost_alert(daily_cost, DAILY_COST_THRESHOLD)

    return daily_cost
```

### Email Alerts

```python
import smtplib
from email.message import EmailMessage

async def send_cost_alert(current_cost: float, threshold: float):
    """Send email alert when cost threshold exceeded"""

    msg = EmailMessage()
    msg['Subject'] = f'[LCT] Cost Alert: ${current_cost:.2f} exceeds threshold'
    msg['From'] = os.getenv("ALERT_EMAIL_FROM")
    msg['To'] = os.getenv("ALERT_EMAIL_TO")

    msg.set_content(f"""
    Daily Cost Alert

    Current daily cost: ${current_cost:.2f}
    Threshold: ${threshold:.2f}
    Overage: ${current_cost - threshold:.2f}

    Please review API usage in the Cost Dashboard.
    """)

    # Send email
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), 587) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        smtp.send_message(msg)
```

### Slack Alerts (Alternative)

```python
import httpx

async def send_slack_alert(message: str):
    """Send alert to Slack webhook"""

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return

    payload = {
        "text": f"🚨 LCT Alert: {message}"
    }

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload)
```

---

## 4. Log Aggregation

### Structured Logging

**Add to `backend.py`:**

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
```

### Log Rotation

```bash
# Install logrotate config
sudo tee /etc/logrotate.d/lct <<EOF
/var/log/lct/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload lct-backend
    endscript
}
EOF
```

---

## 5. Health Checks

### Backend Health Endpoint

```python
@lct_app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring

    Returns:
        - status: "healthy" or "unhealthy"
        - checks: Individual component health
        - version: Application version
    """
    checks = {}

    # Check database
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Check Anthropic API key
    checks["anthropic_api"] = "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing"

    # Overall status
    status = "healthy" if all(v == "healthy" or v == "configured" for v in checks.values()) else "unhealthy"

    return {
        "status": status,
        "checks": checks,
        "version": os.getenv("GIT_COMMIT", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Uptime Monitoring

Use external services:
- **UptimeRobot**: Free plan monitors every 5 minutes
- **Pingdom**: More advanced monitoring
- **StatusCake**: Alternative option

Configure to check: `https://api.yourdomain.com/health`

Alert if:
- Status code != 200
- Response time > 5 seconds
- Status field != "healthy"

---

## 6. Alerting Rules

### Critical Alerts (PagerDuty/SMS)

```yaml
alerts:
  - name: api_down
    condition: health_check_failed for 5 minutes
    severity: critical
    channel: pagerduty

  - name: database_connection_failure
    condition: database check = unhealthy
    severity: critical
    channel: pagerduty

  - name: error_rate_spike
    condition: error_rate > 10% for 5 minutes
    severity: critical
    channel: pagerduty
```

### Warning Alerts (Email/Slack)

```yaml
alerts:
  - name: high_daily_cost
    condition: daily_cost > threshold
    severity: warning
    channel: email, slack

  - name: slow_api_response
    condition: p95_latency > 5000ms
    severity: warning
    channel: slack

  - name: high_memory_usage
    condition: memory > 80%
    severity: warning
    channel: slack
```

---

## 7. Dashboard Setup

### Grafana Dashboard (Recommended)

**Install Grafana:**

```bash
# Add Grafana repository
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"

# Install
sudo apt-get update
sudo apt-get install grafana

# Start
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

Access: `http://localhost:3000` (default user: admin/admin)

**Dashboard Panels:**

1. **API Performance**
   - Response time (p50, p95, p99)
   - Requests per second
   - Error rate

2. **Cost Tracking**
   - Daily cost trend
   - Cost by feature
   - Cost per conversation

3. **Database**
   - Query duration
   - Connection pool usage
   - Active connections

4. **System Metrics**
   - CPU usage
   - Memory usage
   - Disk I/O

### Custom Cost Dashboard

The application includes a built-in Cost Dashboard at `/cost-dashboard`. This provides:
- Total cost overview
- Cost by feature (Simulacra, Bias, Frame)
- Cost by model (Claude 3.5 Sonnet)
- Recent API calls

---

## Quick Start Checklist

### Minimum Monitoring (Day 1)

- [x] Sentry error tracking (backend + frontend)
- [x] Health check endpoint (`/health`)
- [x] Uptime monitoring (UptimeRobot)
- [ ] Cost alert email
- [ ] Log to file with rotation

### Production Monitoring (Week 1)

- [ ] Prometheus + Grafana
- [ ] Structured JSON logging
- [ ] PagerDuty integration
- [ ] Daily cost report emails
- [ ] Performance baselines established

### Advanced Monitoring (Month 1)

- [ ] Custom Grafana dashboards
- [ ] APM (Application Performance Monitoring)
- [ ] Real User Monitoring (RUM)
- [ ] Distributed tracing
- [ ] Anomaly detection

---

## Environment Variables Summary

```bash
# Error Tracking
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=production

# Alerts
DAILY_COST_THRESHOLD=50.0
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_TO=admin@yourdomain.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# SMTP (for email alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-password

# PagerDuty (optional)
PAGERDUTY_API_KEY=...
PAGERDUTY_SERVICE_ID=...
```

---

## Testing Your Monitoring

### 1. Test Error Tracking

```python
# Trigger test error
@lct_app.get("/test-error")
async def test_error():
    raise Exception("Test error for Sentry")
```

Visit: `http://localhost:8000/test-error`
Check: Sentry dashboard should show the error

### 2. Test Health Check

```bash
curl http://localhost:8000/health
```

Should return JSON with status and checks

### 3. Test Performance Benchmark

```bash
cd lct_python_backend
python performance_benchmark.py
```

Should print performance report

### 4. Test Cost Alert

```python
# Manually trigger cost check
asyncio.run(check_daily_costs())
```

---

## Common Issues

### Issue: Sentry not capturing errors

**Solution:**
- Check `SENTRY_DSN` is set correctly
- Verify network connectivity to sentry.io
- Check Sentry dashboard for rate limits

### Issue: Health check always returns unhealthy

**Solution:**
- Check database connection
- Verify `DATABASE_URL` environment variable
- Check firewall rules

### Issue: No metrics appearing in Grafana

**Solution:**
- Verify Prometheus is scraping `/metrics` endpoint
- Check Prometheus targets page
- Verify Grafana data source configuration

---

## Next Steps

1. **Start with Sentry**: Easiest quick win for error tracking
2. **Set up health checks**: Essential for uptime monitoring
3. **Configure cost alerts**: Prevent unexpected bills
4. **Add Grafana**: When ready for detailed monitoring

---

**Last Updated**: November 12, 2025
**Status**: Production Ready
**Estimated Setup Time**: 2-4 hours
