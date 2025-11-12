"""
Security Configuration and Hardening
Production Tool: Security best practices and middleware

Add this to backend.py for production deployment
"""

from fastapi import HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from typing import Callable
import time


# ============================================================================
# CORS Configuration
# ============================================================================

def configure_cors(app, environment="development"):
    """
    Configure CORS based on environment

    Usage in backend.py:
        from security_config import configure_cors
        configure_cors(app, environment="production")
    """

    if environment == "production":
        # Production: Strict CORS - only allow specific domain
        allowed_origins = [
            os.getenv("FRONTEND_URL", "https://yourdomain.com"),
        ]
    elif environment == "staging":
        # Staging: Allow staging domain
        allowed_origins = [
            os.getenv("FRONTEND_URL", "https://staging.yourdomain.com"),
            "http://localhost:3000",  # For testing
        ]
    else:
        # Development: Allow localhost
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",  # Vite default
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    print(f"[SECURITY] CORS configured for {environment} with origins: {allowed_origins}")


# ============================================================================
# Trusted Host Middleware
# ============================================================================

def configure_trusted_hosts(app, environment="development"):
    """
    Configure trusted hosts to prevent Host header attacks

    Usage:
        configure_trusted_hosts(app, environment="production")
    """

    if environment == "production":
        allowed_hosts = [
            os.getenv("BACKEND_DOMAIN", "api.yourdomain.com"),
            "api.yourdomain.com",
        ]
    elif environment == "staging":
        allowed_hosts = [
            "staging-api.yourdomain.com",
            "localhost",
        ]
    else:
        # Development: Allow all
        allowed_hosts = ["*"]

    if allowed_hosts != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
        print(f"[SECURITY] Trusted hosts configured: {allowed_hosts}")


# ============================================================================
# Rate Limiting Middleware
# ============================================================================

class RateLimitMiddleware:
    """
    Simple in-memory rate limiting

    For production, use Redis-based rate limiting (fastapi-limiter)
    """

    def __init__(self, app: Callable, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count)]}

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host

        # Clean old entries
        current_time = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if current_time - ts < self.window_seconds
            ]

        # Count requests in window
        if client_ip in self.requests:
            request_count = sum(count for _, count in self.requests[client_ip])
        else:
            request_count = 0

        # Check rate limit
        if request_count >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds."
            )

        # Add this request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append((current_time, 1))

        response = await call_next(request)
        return response


# ============================================================================
# Security Headers Middleware
# ============================================================================

async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses

    Usage in backend.py:
        from security_config import add_security_headers
        app.middleware("http")(add_security_headers)
    """
    response = await call_next(request)

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    # Strict Transport Security (HTTPS only)
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# ============================================================================
# Input Validation
# ============================================================================

def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format to prevent injection"""
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False


def sanitize_string(text: str, max_length: int = 10000) -> str:
    """Basic string sanitization"""
    if not text:
        return ""

    # Truncate
    text = text[:max_length]

    # Remove null bytes
    text = text.replace("\x00", "")

    return text.strip()


# ============================================================================
# API Key Validation (if needed)
# ============================================================================

async def validate_api_key(request: Request, call_next):
    """
    Optional API key validation middleware

    Set API_KEY_REQUIRED=true in environment to enable

    Usage:
        app.middleware("http")(validate_api_key)
    """

    if os.getenv("API_KEY_REQUIRED", "false").lower() == "true":
        # Exempt health check endpoint
        if request.url.path == "/health":
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        expected_key = os.getenv("API_KEY")

        if not expected_key:
            print("[WARNING] API_KEY_REQUIRED is true but API_KEY not set!")
            return await call_next(request)

        if api_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key"
            )

    return await call_next(request)


# ============================================================================
# Configuration Helper
# ============================================================================

def configure_security(app, environment="development"):
    """
    Apply all security configurations

    Usage in backend.py:
        from security_config import configure_security
        configure_security(app, environment="production")
    """

    print(f"\n[SECURITY] Configuring security for {environment} environment")

    # 1. CORS
    configure_cors(app, environment)

    # 2. Trusted hosts
    configure_trusted_hosts(app, environment)

    # 3. GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    print("[SECURITY] GZip compression enabled")

    # 4. Security headers
    app.middleware("http")(add_security_headers)
    print("[SECURITY] Security headers middleware enabled")

    # 5. Rate limiting (if needed)
    if environment == "production":
        # In production, use Redis-based rate limiting
        # app.middleware("http")(RateLimitMiddleware(app, max_requests=100, window_seconds=60))
        print("[SECURITY] Note: Consider Redis-based rate limiting for production")

    # 6. Session middleware (if using sessions)
    secret_key = os.getenv("SESSION_SECRET_KEY", "development-secret-key-change-in-production")
    if environment == "production" and secret_key == "development-secret-key-change-in-production":
        print("[WARNING] Using default session secret key! Set SESSION_SECRET_KEY in production!")

    print("[SECURITY] Security configuration complete\n")


# ============================================================================
# Security Checklist
# ============================================================================

def print_security_checklist():
    """Print security checklist for deployment"""
    checklist = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                    SECURITY DEPLOYMENT CHECKLIST                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

    Environment Variables:
    ☐ SESSION_SECRET_KEY is set (not default)
    ☐ ANTHROPIC_API_KEY is secured (not in code)
    ☐ DATABASE_URL uses secure connection
    ☐ FRONTEND_URL matches production domain
    ☐ ENVIRONMENT is set to "production"

    Network Security:
    ☐ HTTPS enabled (SSL certificate)
    ☐ CORS configured for production domain only
    ☐ Firewall rules configured
    ☐ Database not publicly accessible

    Application Security:
    ☐ All dependencies up to date
    ☐ No default/weak passwords
    ☐ Rate limiting enabled
    ☐ API key validation (if needed)
    ☐ Input validation on all endpoints

    Monitoring:
    ☐ Error tracking (Sentry/similar)
    ☐ Access logs enabled
    ☐ Cost alerts configured
    ☐ Performance monitoring

    Backup & Recovery:
    ☐ Database backups configured
    ☐ Backup restoration tested
    ☐ Disaster recovery plan documented

    ════════════════════════════════════════════════════════════════════════
    """
    print(checklist)


if __name__ == "__main__":
    print("Live Conversational Threads - Security Configuration")
    print_security_checklist()
