# Instrumentation & Cost Tracking

**Version:** 1.0
**Status:** Implemented (Week 2)
**Last Updated:** 2025-11-11

## Overview

The instrumentation module provides comprehensive API call logging, cost tracking, and performance monitoring for LLM API usage in the Live Conversational Threads platform.

### Features

- **Automatic Cost Calculation**: Tracks token usage and calculates costs for OpenAI and Anthropic models
- **API Call Logging**: Logs all LLM API calls to the `api_calls_log` database table
- **Cost Aggregation**: Daily, weekly, and monthly cost rollups
- **Alert System**: Configurable cost threshold alerts
- **Performance Metrics**: Request latency, token usage, and error rates
- **REST API**: Endpoints for querying costs and generating reports

---

## Quick Start

### 1. Basic Usage with Decorator

The `@track_api_call` decorator automatically logs API calls and calculates costs:

```python
from instrumentation import track_api_call
import openai

@track_api_call("generate_clusters")
async def generate_clusters(conversation_id: str, utterances: List[Utterance]):
    """Generate initial topic clusters from utterances."""

    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Analyze this transcript..."},
            {"role": "user", "content": transcript_text}
        ],
        temperature=0.5,
    )

    return response

# The decorator automatically:
# 1. Measures latency
# 2. Extracts token counts from response
# 3. Calculates cost based on model pricing
# 4. Logs to api_calls_log table
```

### 2. Setting Up Database Connection

Connect the instrumentation system to your database:

```python
from instrumentation import set_db_connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Create async engine
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/lct")

# Create session
async with AsyncSession(engine) as session:
    set_db_connection(session)
```

### 3. Adding FastAPI Middleware

Add instrumentation middleware to your FastAPI app:

```python
from fastapi import FastAPI
from instrumentation import InstrumentationMiddleware

app = FastAPI()

# Add instrumentation middleware
app.add_middleware(InstrumentationMiddleware, enable_logging=True)
```

### 4. Including Cost Tracking API

Include the cost tracking API endpoints:

```python
from cost_api import router as cost_router

app.include_router(cost_router)

# Endpoints will be available at:
# - GET /api/costs/daily
# - GET /api/costs/weekly
# - GET /api/costs/monthly
# - GET /api/costs/conversation/{id}
# - GET /api/costs/trend
# - GET /api/costs/top-conversations
# - GET /api/costs/report/daily
# - GET /api/costs/report/monthly
```

---

## Cost Calculation

### Supported Models

The system supports pricing for:

**OpenAI Models:**
- GPT-4: $0.03/1K input, $0.06/1K output
- GPT-4-Turbo: $0.01/1K input, $0.03/1K output
- GPT-3.5-Turbo: $0.0005/1K input, $0.0015/1K output

**Anthropic Models:**
- Claude 3 Opus: $0.015/1K input, $0.075/1K output
- Claude 3 Sonnet: $0.003/1K input, $0.015/1K output
- Claude 3 Haiku: $0.00025/1K input, $0.00125/1K output

### Manual Cost Calculation

```python
from instrumentation import calculate_cost, estimate_cost

# Calculate cost from token counts
cost = calculate_cost(
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500
)
print(f"Cost: ${cost:.4f}")  # Cost: $0.0600

# Estimate cost from text
estimated = estimate_cost(
    model="gpt-4",
    input_text="Analyze this long transcript...",
    estimated_output_tokens=1000
)
print(f"Estimated cost: ${estimated:.4f}")
```

### Cost Breakdown

```python
from instrumentation import calculate_cost_breakdown

input_cost, output_cost, total_cost = calculate_cost_breakdown(
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500
)

print(f"Input: ${input_cost:.4f}")   # $0.0300
print(f"Output: ${output_cost:.4f}")  # $0.0300
print(f"Total: ${total_cost:.4f}")    # $0.0600
```

---

## Alert System

### Setting Up Alerts

```python
from instrumentation import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertChannel,
)

# Create alert manager
manager = AlertManager()

# Add custom alert rule
rule = AlertRule(
    name="high_daily_cost",
    threshold=100.0,
    threshold_type="daily",
    severity=AlertSeverity.WARNING,
    channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
    message_template="Daily cost ${cost:.2f} exceeded threshold ${threshold:.2f}",
    cooldown_minutes=60,
)

manager.add_rule(rule)
```

### Checking Alerts

```python
# Check alerts with current costs
alerts = await manager.check_alerts(
    current_daily_cost=150.0,
    current_weekly_cost=800.0,
)

for alert in alerts:
    print(f"{alert.severity.value}: {alert.message}")
```

### Custom Alert Handlers

```python
import aiohttp

async def slack_webhook_handler(alert):
    """Send alert to Slack via webhook."""
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    payload = {
        "text": f"🚨 {alert.message}",
        "username": "Cost Alert Bot",
    }

    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)

# Register handler
manager.register_handler(AlertChannel.SLACK, slack_webhook_handler)
```

### Default Alert Rules

The system includes pre-configured alerts:

1. **high_daily_cost**: Warns when daily cost exceeds $100
2. **critical_daily_cost**: Critical alert at $500/day
3. **high_conversation_cost**: Warns when a single conversation costs > $10
4. **high_weekly_cost**: Warns when weekly cost exceeds $500

---

## Cost Aggregation

### Daily Aggregation

```python
from instrumentation import CostAggregator
from datetime import date

aggregator = CostAggregator(db_session)

# Get today's costs
daily = await aggregator.aggregate_daily(date.today())

print(f"Total: ${daily.total_cost:.2f}")
print(f"Calls: {daily.total_calls}")
print(f"Tokens: {daily.total_tokens:,}")

# Cost by model
for model, cost in daily.cost_by_model.items():
    print(f"  {model}: ${cost:.2f}")

# Cost by endpoint
for endpoint, cost in daily.cost_by_endpoint.items():
    print(f"  {endpoint}: ${cost:.2f}")
```

### Weekly and Monthly Aggregation

```python
from datetime import date

# Weekly aggregation (Monday start)
weekly = await aggregator.aggregate_weekly(date(2025, 11, 10))

# Monthly aggregation
monthly = await aggregator.aggregate_monthly(2025, 11)
```

### Conversation-Level Costs

```python
# Get cost breakdown for a specific conversation
conv_cost = await aggregator.get_conversation_cost("conv-uuid-123")

print(f"Conversation: {conv_cost.conversation_id}")
print(f"Total cost: ${conv_cost.total_cost:.2f}")
print(f"Duration: {conv_cost.last_call - conv_cost.first_call}")

# Cost by feature
for endpoint, cost in conv_cost.cost_by_endpoint.items():
    print(f"  {endpoint}: ${cost:.2f}")
```

### Top Conversations by Cost

```python
# Get 10 most expensive conversations
top = await aggregator.get_top_conversations_by_cost(limit=10)

for conv_id, cost in top:
    print(f"{conv_id}: ${cost:.2f}")
```

### Cost Trends

```python
# Get 30-day cost trend
trend = await aggregator.get_cost_trend(days=30)

for date, cost in trend:
    print(f"{date}: ${cost:.2f}")
```

---

## Reports

### Daily Report

```python
from instrumentation import CostReporter

reporter = CostReporter(aggregator)

# Generate markdown report
report = await reporter.generate_daily_report(date.today())
print(report)
```

**Example Output:**

```markdown
# Daily Cost Report - 2025-11-11

## Summary
- Total Cost: $45.32
- Total API Calls: 127
- Total Tokens: 234,567
- Avg Cost/Call: $0.3568
- Avg Tokens/Call: 1847

## Cost by Model
- gpt-4: $38.21 (89 calls, 198,432 tokens)
- gpt-3.5-turbo: $7.11 (38 calls, 36,135 tokens)

## Cost by Endpoint
- generate_clusters: $25.67 (45 calls)
- detect_cognitive_bias: $12.34 (32 calls)
- generate_summaries: $7.31 (50 calls)
```

### Monthly Summary

```python
# Generate monthly summary
summary = await reporter.generate_monthly_summary(2025, 11)
print(summary)
```

---

## REST API Endpoints

### GET /api/costs/daily

Get daily cost aggregation.

**Query Parameters:**
- `target_date` (optional): Date in YYYY-MM-DD format (default: today)

**Response:**
```json
{
  "period_start": "2025-11-11T00:00:00",
  "period_end": "2025-11-11T23:59:59",
  "total_cost": 45.32,
  "total_tokens": 234567,
  "total_calls": 127,
  "cost_by_model": {
    "gpt-4": 38.21,
    "gpt-3.5-turbo": 7.11
  },
  "cost_by_endpoint": {
    "generate_clusters": 25.67,
    "detect_cognitive_bias": 12.34
  },
  "avg_cost_per_call": 0.3568,
  "avg_tokens_per_call": 1847
}
```

### GET /api/costs/conversation/{conversation_id}

Get cost breakdown for a specific conversation.

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_cost": 3.45,
  "total_tokens": 15234,
  "total_calls": 8,
  "cost_by_endpoint": {
    "generate_clusters": 2.10,
    "generate_summaries": 1.35
  },
  "cost_by_model": {
    "gpt-4": 3.45
  },
  "first_call": "2025-11-11T10:30:00",
  "last_call": "2025-11-11T10:35:23"
}
```

### GET /api/costs/trend

Get daily cost trend.

**Query Parameters:**
- `days` (optional): Number of days (1-365, default: 30)

**Response:**
```json
[
  {"date": "2025-10-12", "cost": 42.15},
  {"date": "2025-10-13", "cost": 38.92},
  {"date": "2025-10-14", "cost": 51.23}
]
```

### GET /api/costs/top-conversations

Get most expensive conversations.

**Query Parameters:**
- `limit` (optional): Number of results (1-100, default: 10)
- `period_start` (optional): Start date filter
- `period_end` (optional): End date filter

**Response:**
```json
[
  {"conversation_id": "uuid-1", "total_cost": 12.45},
  {"conversation_id": "uuid-2", "total_cost": 10.32}
]
```

---

## Database Schema

### api_calls_log Table

The `api_calls_log` table (defined in `models.py`) stores all LLM API call data:

```sql
CREATE TABLE api_calls_log (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    endpoint TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    latency_ms INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_api_calls_conversation ON api_calls_log(conversation_id);
CREATE INDEX idx_api_calls_timestamp ON api_calls_log(timestamp);
CREATE INDEX idx_api_calls_endpoint ON api_calls_log(endpoint);
CREATE INDEX idx_api_calls_model ON api_calls_log(model);
```

**Fields:**
- `id`: Unique identifier for the API call
- `conversation_id`: Associated conversation (nullable)
- `endpoint`: Name of the endpoint/feature (e.g., "generate_clusters")
- `model`: Model used (e.g., "gpt-4", "claude-3-sonnet")
- `input_tokens`: Number of input/prompt tokens
- `output_tokens`: Number of output/completion tokens
- `total_tokens`: Sum of input + output tokens
- `cost_usd`: Calculated cost in USD
- `latency_ms`: Request duration in milliseconds
- `timestamp`: When the API call was made
- `success`: Whether the call succeeded
- `error_message`: Error message if call failed
- `metadata`: Additional data (temperature, finish_reason, etc.)

---

## Best Practices

### 1. Always Use the Decorator

Wrap all LLM API calls with `@track_api_call`:

```python
@track_api_call("my_feature")
async def my_llm_function(conversation_id: str):
    response = await openai.ChatCompletion.create(...)
    return response
```

### 2. Set Meaningful Endpoint Names

Use descriptive names that reflect the feature:

```python
@track_api_call("initial_clustering")      # Good
@track_api_call("generate")                # Too vague
@track_api_call("detect_confirmation_bias") # Good
```

### 3. Monitor Daily Costs

Set up a daily job to check costs and send reports:

```python
from instrumentation import run_daily_aggregation_job

# Run daily (e.g., via cron)
await run_daily_aggregation_job(db, alert_manager)
```

### 4. Set Conservative Alert Thresholds

Start with low thresholds and adjust based on usage:

```python
# Start conservative
AlertRule(name="daily_warning", threshold=50.0, ...)

# Adjust after 1 week of data
AlertRule(name="daily_warning", threshold=100.0, ...)
```

### 5. Archive Old Logs

Implement log archival to manage database size:

```python
# Archive logs older than 90 days to cold storage
await archive_old_logs(days=90)
```

---

## Testing

### Unit Tests

```python
# tests/test_cost_calculator.py

from instrumentation import calculate_cost, get_model_pricing

def test_gpt4_cost_calculation():
    cost = calculate_cost("gpt-4", 1000, 500)
    expected = (1000 * 0.03 / 1000) + (500 * 0.06 / 1000)
    assert abs(cost - expected) < 0.0001

def test_model_pricing_lookup():
    pricing = get_model_pricing("gpt-4")
    assert pricing is not None
    assert pricing.provider == "openai"
```

### Integration Tests

```python
# tests/test_instrumentation.py

import pytest
from instrumentation import track_api_call, get_tracker

@pytest.mark.asyncio
async def test_track_api_call_decorator():
    @track_api_call("test_endpoint")
    async def mock_llm_call(conversation_id: str):
        # Mock response
        class MockResponse:
            model = "gpt-4"
            class usage:
                prompt_tokens = 100
                completion_tokens = 50
        return MockResponse()

    await mock_llm_call(conversation_id="test-123")

    # Check in-memory logs
    tracker = get_tracker()
    logs = tracker.get_in_memory_logs()

    assert len(logs) == 1
    assert logs[0]["endpoint"] == "test_endpoint"
    assert logs[0]["total_tokens"] == 150
```

---

## Troubleshooting

### Issue: Costs Not Being Logged

**Symptoms:** API calls execute but no entries in `api_calls_log`

**Causes:**
1. Database connection not set
2. Decorator not applied to function
3. Response format not recognized

**Solutions:**

```python
# 1. Verify database connection
from instrumentation import get_tracker
tracker = get_tracker()
print(tracker.db)  # Should not be None

# 2. Ensure decorator is applied
@track_api_call("my_endpoint")  # Must be present
async def my_function():
    ...

# 3. Check response format
# The decorator expects OpenAI or Anthropic response formats
# If using a custom wrapper, ensure it has these attributes:
response.model = "gpt-4"
response.usage.prompt_tokens = 100
response.usage.completion_tokens = 50
```

### Issue: Incorrect Cost Calculations

**Symptoms:** Costs don't match expected values

**Solutions:**

```python
# 1. Verify model name matches pricing table
from instrumentation import get_model_pricing

pricing = get_model_pricing("your-model-name")
if pricing is None:
    print("Model not in pricing table!")

# 2. Check token counts
print(f"Input: {response.usage.prompt_tokens}")
print(f"Output: {response.usage.completion_tokens}")

# 3. Manually calculate expected cost
from instrumentation import calculate_cost_breakdown
input_cost, output_cost, total = calculate_cost_breakdown(
    "gpt-4", 1000, 500
)
print(f"Expected: ${total:.4f}")
```

### Issue: High Memory Usage

**Symptoms:** Application memory grows over time

**Cause:** In-memory log buffer not being flushed

**Solution:**

```python
# Ensure database connection is set
# so logs are written to DB instead of memory
set_db_connection(session)

# Or manually clear in-memory logs
tracker = get_tracker()
tracker.call_logs.clear()
```

---

## Performance Considerations

### Decorator Overhead

The `@track_api_call` decorator adds minimal overhead:
- Time measurement: < 1ms
- Cost calculation: < 1ms
- Database write: 5-20ms (async)

Total overhead: ~20ms per API call (negligible compared to LLM latency)

### Database Query Optimization

For large-scale deployments:

1. **Partition the `api_calls_log` table by month:**
```sql
CREATE TABLE api_calls_log_2025_11 PARTITION OF api_calls_log
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

2. **Use materialized views for common aggregations:**
```sql
CREATE MATERIALIZED VIEW daily_costs AS
SELECT date_trunc('day', timestamp) as day,
       SUM(cost_usd) as total_cost,
       COUNT(*) as total_calls
FROM api_calls_log
GROUP BY day;

-- Refresh daily
REFRESH MATERIALIZED VIEW daily_costs;
```

---

## Prometheus Integration (Optional)

If Prometheus is available, the system automatically exports metrics:

```python
from instrumentation import PrometheusInstrumentationMiddleware

app.add_middleware(PrometheusInstrumentationMiddleware)

# Metrics available at /metrics
# - api_requests_total
# - api_request_latency_seconds
# - api_cost_usd_total
# - api_tokens_total
# - api_active_requests
```

---

## Future Enhancements

- [ ] Add support for more LLM providers (Cohere, AI21, etc.)
- [ ] Implement cost forecasting based on trends
- [ ] Add budget enforcement (reject calls when budget exceeded)
- [ ] Support for prompt caching cost tracking
- [ ] Real-time cost dashboard (WebSocket updates)
- [ ] Cost optimization recommendations

---

## References

- [Week 2 Roadmap](../docs/ROADMAP.md#week-2-instrumentation--cost-tracking)
- [Database Schema](DATABASE_MIGRATIONS.md)
- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
