"""
FastAPI middleware for request instrumentation and metrics.

This module provides:
- Request/response timing
- Endpoint usage tracking
- Error rate monitoring
- Integration with Prometheus metrics (optional)
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime


class InstrumentationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to instrument HTTP requests.

    Tracks:
    - Request latency
    - Status codes
    - Endpoint usage
    - Error rates

    Usage:
        from fastapi import FastAPI
        from instrumentation.middleware import InstrumentationMiddleware

        app = FastAPI()
        app.add_middleware(InstrumentationMiddleware)
    """

    def __init__(self, app, enable_logging: bool = True):
        super().__init__(app)
        self.enable_logging = enable_logging
        self.request_count = {}
        self.request_latency = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and measure metrics."""
        start_time = time.time()
        path = request.url.path

        # Execute request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Log error
            if self.enable_logging:
                print(f"Error processing {path}: {e}")
            # Re-raise to let error handlers deal with it
            raise

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Track metrics
        self._track_request(path, status_code, latency_ms)

        # Add custom headers
        response.headers["X-Request-Duration-Ms"] = str(latency_ms)

        # Log if enabled
        if self.enable_logging:
            self._log_request(request, status_code, latency_ms)

        return response

    def _track_request(self, path: str, status_code: int, latency_ms: int):
        """Track request metrics in memory."""
        # Count requests per endpoint
        key = f"{path}:{status_code}"
        self.request_count[key] = self.request_count.get(key, 0) + 1

        # Track latency (simple moving average)
        if path not in self.request_latency:
            self.request_latency[path] = []
        self.request_latency[path].append(latency_ms)

        # Keep only last 100 latencies per path
        if len(self.request_latency[path]) > 100:
            self.request_latency[path] = self.request_latency[path][-100:]

    def _log_request(self, request: Request, status_code: int, latency_ms: int):
        """Log request details."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        method = request.method
        path = request.url.path

        # Color code by status
        if status_code < 300:
            color = "\033[92m"  # Green
        elif status_code < 400:
            color = "\033[93m"  # Yellow
        else:
            color = "\033[91m"  # Red
        reset = "\033[0m"

        print(f"[{timestamp}] {method} {path} {color}{status_code}{reset} - {latency_ms}ms")

    def get_metrics(self):
        """Get current metrics."""
        return {
            "request_count": self.request_count,
            "request_latency": self.request_latency,
        }


# Prometheus integration (optional)

try:
    from prometheus_client import Counter, Histogram, Gauge

    # Define Prometheus metrics
    api_request_count = Counter(
        'api_requests_total',
        'Total API requests',
        ['endpoint', 'method', 'status']
    )

    api_request_latency = Histogram(
        'api_request_latency_seconds',
        'API request latency',
        ['endpoint', 'method']
    )

    api_cost = Counter(
        'api_cost_usd_total',
        'Total API cost in USD',
        ['model', 'endpoint']
    )

    api_tokens = Counter(
        'api_tokens_total',
        'Total tokens used',
        ['model', 'endpoint', 'token_type']
    )

    active_requests = Gauge(
        'api_active_requests',
        'Number of active requests',
        ['endpoint']
    )

    PROMETHEUS_AVAILABLE = True

except ImportError:
    PROMETHEUS_AVAILABLE = False
    api_request_count = None
    api_request_latency = None
    api_cost = None
    api_tokens = None
    active_requests = None


class PrometheusInstrumentationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Prometheus metrics collection.

    Requires prometheus_client to be installed.

    Usage:
        from fastapi import FastAPI
        from instrumentation.middleware import PrometheusInstrumentationMiddleware

        app = FastAPI()
        if PROMETHEUS_AVAILABLE:
            app.add_middleware(PrometheusInstrumentationMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and update Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)

        start_time = time.time()
        path = request.url.path
        method = request.method

        # Increment active requests
        active_requests.labels(endpoint=path).inc()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Decrement active requests
            active_requests.labels(endpoint=path).dec()
            raise
        finally:
            # Measure latency
            latency = time.time() - start_time

        # Decrement active requests
        active_requests.labels(endpoint=path).dec()

        # Update metrics
        api_request_count.labels(
            endpoint=path,
            method=method,
            status=status_code
        ).inc()

        api_request_latency.labels(
            endpoint=path,
            method=method
        ).observe(latency)

        return response


# Helper functions for tracking LLM costs in Prometheus

def track_llm_cost_prometheus(
    model: str,
    endpoint: str,
    cost_usd: float,
    input_tokens: int,
    output_tokens: int,
):
    """
    Track LLM cost and token usage in Prometheus.

    Args:
        model: Model name
        endpoint: Endpoint/feature name
        cost_usd: Cost in USD
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    if not PROMETHEUS_AVAILABLE:
        return

    # Track cost
    api_cost.labels(model=model, endpoint=endpoint).inc(cost_usd)

    # Track tokens
    api_tokens.labels(model=model, endpoint=endpoint, token_type="input").inc(input_tokens)
    api_tokens.labels(model=model, endpoint=endpoint, token_type="output").inc(output_tokens)
