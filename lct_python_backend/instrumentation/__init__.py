"""
Instrumentation package for API call tracking and cost monitoring.

This package provides:
- Cost calculation for OpenAI and Anthropic models
- Decorators for automatic API call logging
- Cost threshold alerts
- Daily/weekly cost aggregation
- FastAPI middleware for request instrumentation
"""

from .cost_calculator import (
    calculate_cost,
    get_model_pricing,
    estimate_cost,
    calculate_cost_breakdown,
)
from .decorators import (
    track_api_call,
    APICallTracker,
    set_db_connection,
    get_tracker,
)
from .alerts import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertChannel,
    create_default_alert_manager,
)
from .aggregation import (
    CostAggregator,
    CostReporter,
    CostAggregation,
    ConversationCost,
)
from .middleware import (
    InstrumentationMiddleware,
    PrometheusInstrumentationMiddleware,
    PROMETHEUS_AVAILABLE,
)

__all__ = [
    # Cost calculation
    'calculate_cost',
    'get_model_pricing',
    'estimate_cost',
    'calculate_cost_breakdown',
    # Decorators
    'track_api_call',
    'APICallTracker',
    'set_db_connection',
    'get_tracker',
    # Alerts
    'AlertManager',
    'AlertRule',
    'AlertSeverity',
    'AlertChannel',
    'create_default_alert_manager',
    # Aggregation
    'CostAggregator',
    'CostReporter',
    'CostAggregation',
    'ConversationCost',
    # Middleware
    'InstrumentationMiddleware',
    'PrometheusInstrumentationMiddleware',
    'PROMETHEUS_AVAILABLE',
]
