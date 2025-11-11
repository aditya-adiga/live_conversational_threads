"""
Cost threshold alerts and monitoring.

This module provides:
- Alert rules for cost thresholds (daily, weekly, monthly)
- Alert delivery mechanisms (email, Slack, webhook)
- Alert history tracking
"""

import asyncio
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class AlertRule:
    """
    Configuration for a cost alert rule.

    Example:
        rule = AlertRule(
            name="high_daily_cost",
            threshold=100.0,
            threshold_type="daily",
            severity=AlertSeverity.WARNING,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
            message_template="Daily cost ${cost:.2f} exceeded threshold ${threshold:.2f}"
        )
    """
    name: str
    threshold: float  # USD
    threshold_type: str  # "daily", "weekly", "monthly", "per_conversation"
    severity: AlertSeverity
    channels: List[AlertChannel]
    message_template: str
    enabled: bool = True
    cooldown_minutes: int = 60  # Minimum time between alerts


@dataclass
class Alert:
    """An alert instance."""
    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    metadata: Dict[str, Any]


class AlertManager:
    """
    Manages cost alert rules and delivery.

    Usage:
        manager = AlertManager()
        manager.add_rule(AlertRule(...))

        # Check alerts periodically
        await manager.check_alerts(current_daily_cost=150.0)
    """

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alert_history: List[Alert] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.handlers: Dict[AlertChannel, Callable] = {}

        # Register default handlers
        self.register_handler(AlertChannel.LOG, self._log_handler)

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> None:
        """Remove an alert rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def register_handler(
        self,
        channel: AlertChannel,
        handler: Callable[[Alert], None]
    ) -> None:
        """
        Register a custom alert handler.

        Args:
            channel: Alert channel type
            handler: Async function that takes an Alert and delivers it

        Example:
            async def slack_handler(alert: Alert):
                await slack_client.post_message(alert.message)

            manager.register_handler(AlertChannel.SLACK, slack_handler)
        """
        self.handlers[channel] = handler

    async def check_alerts(
        self,
        current_daily_cost: Optional[float] = None,
        current_weekly_cost: Optional[float] = None,
        current_monthly_cost: Optional[float] = None,
        per_conversation_cost: Optional[float] = None,
        conversation_id: Optional[str] = None,
    ) -> List[Alert]:
        """
        Check all alert rules and trigger alerts if thresholds exceeded.

        Args:
            current_daily_cost: Current daily cost in USD
            current_weekly_cost: Current weekly cost in USD
            current_monthly_cost: Current monthly cost in USD
            per_conversation_cost: Cost for a specific conversation
            conversation_id: ID of conversation (for per_conversation alerts)

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.name in self.last_alert_time:
                time_since_last = datetime.now() - self.last_alert_time[rule.name]
                if time_since_last.total_seconds() < (rule.cooldown_minutes * 60):
                    continue

            # Determine current value based on threshold type
            current_value = None
            if rule.threshold_type == "daily" and current_daily_cost is not None:
                current_value = current_daily_cost
            elif rule.threshold_type == "weekly" and current_weekly_cost is not None:
                current_value = current_weekly_cost
            elif rule.threshold_type == "monthly" and current_monthly_cost is not None:
                current_value = current_monthly_cost
            elif rule.threshold_type == "per_conversation" and per_conversation_cost is not None:
                current_value = per_conversation_cost

            # Check threshold
            if current_value is not None and current_value >= rule.threshold:
                alert = self._create_alert(
                    rule=rule,
                    current_value=current_value,
                    conversation_id=conversation_id,
                )
                triggered_alerts.append(alert)

                # Deliver alert
                await self._deliver_alert(alert, rule.channels)

                # Update last alert time
                self.last_alert_time[rule.name] = datetime.now()

                # Store in history
                self.alert_history.append(alert)

        return triggered_alerts

    def _create_alert(
        self,
        rule: AlertRule,
        current_value: float,
        conversation_id: Optional[str] = None,
    ) -> Alert:
        """Create an alert instance from a rule."""
        import uuid

        message = rule.message_template.format(
            cost=current_value,
            threshold=rule.threshold,
            conversation_id=conversation_id or "N/A",
        )

        return Alert(
            id=str(uuid.uuid4()),
            rule_name=rule.name,
            severity=rule.severity,
            message=message,
            current_value=current_value,
            threshold=rule.threshold,
            timestamp=datetime.now(),
            metadata={
                "threshold_type": rule.threshold_type,
                "conversation_id": conversation_id,
            },
        )

    async def _deliver_alert(
        self,
        alert: Alert,
        channels: List[AlertChannel]
    ) -> None:
        """Deliver an alert to specified channels."""
        for channel in channels:
            handler = self.handlers.get(channel)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    print(f"Failed to deliver alert via {channel.value}: {e}")

    def _log_handler(self, alert: Alert) -> None:
        """Default handler: log to console."""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
        }

        emoji = severity_emoji.get(alert.severity, "")
        print(f"{emoji} [{alert.severity.value.upper()}] {alert.message}")

    def get_alert_history(
        self,
        limit: Optional[int] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        """
        Get alert history with optional filtering.

        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity level

        Returns:
            List of historical alerts
        """
        alerts = self.alert_history

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if limit:
            alerts = alerts[-limit:]

        return alerts


# Pre-configured alert rules

DEFAULT_ALERT_RULES = [
    AlertRule(
        name="high_daily_cost",
        threshold=100.0,
        threshold_type="daily",
        severity=AlertSeverity.WARNING,
        channels=[AlertChannel.LOG, AlertChannel.EMAIL],
        message_template="Daily cost ${cost:.2f} exceeded threshold ${threshold:.2f}",
        cooldown_minutes=60,
    ),
    AlertRule(
        name="critical_daily_cost",
        threshold=500.0,
        threshold_type="daily",
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.LOG, AlertChannel.EMAIL, AlertChannel.SLACK],
        message_template="CRITICAL: Daily cost ${cost:.2f} far exceeded threshold ${threshold:.2f}",
        cooldown_minutes=30,
    ),
    AlertRule(
        name="high_conversation_cost",
        threshold=10.0,
        threshold_type="per_conversation",
        severity=AlertSeverity.WARNING,
        channels=[AlertChannel.LOG],
        message_template="Conversation {conversation_id} cost ${cost:.2f} exceeded threshold ${threshold:.2f}",
        cooldown_minutes=0,  # Alert on every occurrence
    ),
    AlertRule(
        name="high_weekly_cost",
        threshold=500.0,
        threshold_type="weekly",
        severity=AlertSeverity.WARNING,
        channels=[AlertChannel.LOG, AlertChannel.EMAIL],
        message_template="Weekly cost ${cost:.2f} exceeded threshold ${threshold:.2f}",
        cooldown_minutes=360,  # 6 hours
    ),
]


def create_default_alert_manager() -> AlertManager:
    """Create an AlertManager with default rules."""
    manager = AlertManager()

    for rule in DEFAULT_ALERT_RULES:
        manager.add_rule(rule)

    return manager


# Example handler implementations

async def email_alert_handler(alert: Alert) -> None:
    """
    Example email alert handler.

    In production, replace with actual email service (SendGrid, SES, etc.)
    """
    # TODO: Implement actual email sending
    print(f"[EMAIL] Would send email: {alert.message}")


async def slack_alert_handler(alert: Alert) -> None:
    """
    Example Slack alert handler.

    In production, use Slack SDK or webhook.
    """
    # TODO: Implement Slack webhook
    print(f"[SLACK] Would send Slack message: {alert.message}")


async def webhook_alert_handler(alert: Alert) -> None:
    """
    Example webhook alert handler.

    In production, send HTTP POST to configured webhook URL.
    """
    # TODO: Implement webhook POST
    import json

    payload = {
        "id": alert.id,
        "rule_name": alert.rule_name,
        "severity": alert.severity.value,
        "message": alert.message,
        "current_value": alert.current_value,
        "threshold": alert.threshold,
        "timestamp": alert.timestamp.isoformat(),
        "metadata": alert.metadata,
    }

    print(f"[WEBHOOK] Would POST: {json.dumps(payload, indent=2)}")
