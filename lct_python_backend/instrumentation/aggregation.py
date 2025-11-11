"""
Cost aggregation and reporting utilities.

This module provides:
- Daily/weekly/monthly cost rollups
- Cost aggregation by model, endpoint, conversation
- Background job for automatic aggregation
- Cost analytics and reporting
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CostAggregation:
    """Aggregated cost data for a time period."""
    period_start: datetime
    period_end: datetime
    total_cost: float
    total_tokens: int
    total_calls: int
    cost_by_model: Dict[str, float]
    cost_by_endpoint: Dict[str, float]
    calls_by_model: Dict[str, int]
    calls_by_endpoint: Dict[str, int]
    tokens_by_model: Dict[str, int]
    avg_cost_per_call: float
    avg_tokens_per_call: float


@dataclass
class ConversationCost:
    """Cost breakdown for a single conversation."""
    conversation_id: str
    total_cost: float
    total_tokens: int
    total_calls: int
    cost_by_endpoint: Dict[str, float]
    cost_by_model: Dict[str, float]
    first_call: datetime
    last_call: datetime


class CostAggregator:
    """
    Aggregates and analyzes API cost data.

    Usage:
        aggregator = CostAggregator(db_connection)

        # Get daily aggregation
        daily = await aggregator.aggregate_daily(date.today())

        # Get cost by conversation
        conv_cost = await aggregator.get_conversation_cost("conv-123")
    """

    def __init__(self, db=None):
        """
        Initialize aggregator with database connection.

        Args:
            db: Database connection/session
        """
        self.db = db

    async def aggregate_daily(
        self,
        target_date: date,
    ) -> CostAggregation:
        """
        Aggregate costs for a specific day.

        Args:
            target_date: Date to aggregate

        Returns:
            CostAggregation object with daily totals
        """
        period_start = datetime.combine(target_date, datetime.min.time())
        period_end = datetime.combine(target_date, datetime.max.time())

        return await self._aggregate_period(period_start, period_end)

    async def aggregate_weekly(
        self,
        week_start: date,
    ) -> CostAggregation:
        """
        Aggregate costs for a week.

        Args:
            week_start: Start date of week (Monday)

        Returns:
            CostAggregation object with weekly totals
        """
        period_start = datetime.combine(week_start, datetime.min.time())
        period_end = period_start + timedelta(days=7)

        return await self._aggregate_period(period_start, period_end)

    async def aggregate_monthly(
        self,
        year: int,
        month: int,
    ) -> CostAggregation:
        """
        Aggregate costs for a month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            CostAggregation object with monthly totals
        """
        period_start = datetime(year, month, 1)

        # Calculate end of month
        if month == 12:
            period_end = datetime(year + 1, 1, 1)
        else:
            period_end = datetime(year, month + 1, 1)

        return await self._aggregate_period(period_start, period_end)

    async def _aggregate_period(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> CostAggregation:
        """
        Aggregate costs for an arbitrary time period.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            CostAggregation object
        """
        if self.db is None:
            # Return empty aggregation if no database
            return CostAggregation(
                period_start=period_start,
                period_end=period_end,
                total_cost=0.0,
                total_tokens=0,
                total_calls=0,
                cost_by_model={},
                cost_by_endpoint={},
                calls_by_model={},
                calls_by_endpoint={},
                tokens_by_model={},
                avg_cost_per_call=0.0,
                avg_tokens_per_call=0.0,
            )

        # Query database for logs in this period
        from models import APICallLog
        from sqlalchemy import select, func
        from sqlalchemy.ext.asyncio import AsyncSession

        if isinstance(self.db, AsyncSession):
            # Query all logs in period
            stmt = select(APICallLog).where(
                APICallLog.timestamp >= period_start,
                APICallLog.timestamp < period_end,
                APICallLog.success == True,
            )

            result = await self.db.execute(stmt)
            logs = result.scalars().all()

            # Aggregate data
            total_cost = 0.0
            total_tokens = 0
            total_calls = len(logs)

            cost_by_model = defaultdict(float)
            cost_by_endpoint = defaultdict(float)
            calls_by_model = defaultdict(int)
            calls_by_endpoint = defaultdict(int)
            tokens_by_model = defaultdict(int)

            for log in logs:
                total_cost += log.cost_usd
                total_tokens += log.total_tokens

                cost_by_model[log.model] += log.cost_usd
                cost_by_endpoint[log.endpoint] += log.cost_usd

                calls_by_model[log.model] += 1
                calls_by_endpoint[log.endpoint] += 1

                tokens_by_model[log.model] += log.total_tokens

            avg_cost_per_call = total_cost / total_calls if total_calls > 0 else 0.0
            avg_tokens_per_call = total_tokens / total_calls if total_calls > 0 else 0.0

            return CostAggregation(
                period_start=period_start,
                period_end=period_end,
                total_cost=total_cost,
                total_tokens=total_tokens,
                total_calls=total_calls,
                cost_by_model=dict(cost_by_model),
                cost_by_endpoint=dict(cost_by_endpoint),
                calls_by_model=dict(calls_by_model),
                calls_by_endpoint=dict(calls_by_endpoint),
                tokens_by_model=dict(tokens_by_model),
                avg_cost_per_call=avg_cost_per_call,
                avg_tokens_per_call=avg_tokens_per_call,
            )

        # Fallback: return empty aggregation
        return CostAggregation(
            period_start=period_start,
            period_end=period_end,
            total_cost=0.0,
            total_tokens=0,
            total_calls=0,
            cost_by_model={},
            cost_by_endpoint={},
            calls_by_model={},
            calls_by_endpoint={},
            tokens_by_model={},
            avg_cost_per_call=0.0,
            avg_tokens_per_call=0.0,
        )

    async def get_conversation_cost(
        self,
        conversation_id: str,
    ) -> ConversationCost:
        """
        Get cost breakdown for a specific conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            ConversationCost object
        """
        if self.db is None:
            raise ValueError("Database connection required for conversation cost lookup")

        from models import APICallLog
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        import uuid

        conv_uuid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id

        if isinstance(self.db, AsyncSession):
            stmt = select(APICallLog).where(
                APICallLog.conversation_id == conv_uuid,
                APICallLog.success == True,
            ).order_by(APICallLog.timestamp)

            result = await self.db.execute(stmt)
            logs = result.scalars().all()

            if not logs:
                raise ValueError(f"No API calls found for conversation {conversation_id}")

            # Aggregate
            total_cost = 0.0
            total_tokens = 0
            total_calls = len(logs)

            cost_by_endpoint = defaultdict(float)
            cost_by_model = defaultdict(float)

            first_call = logs[0].timestamp
            last_call = logs[-1].timestamp

            for log in logs:
                total_cost += log.cost_usd
                total_tokens += log.total_tokens
                cost_by_endpoint[log.endpoint] += log.cost_usd
                cost_by_model[log.model] += log.cost_usd

            return ConversationCost(
                conversation_id=conversation_id,
                total_cost=total_cost,
                total_tokens=total_tokens,
                total_calls=total_calls,
                cost_by_endpoint=dict(cost_by_endpoint),
                cost_by_model=dict(cost_by_model),
                first_call=first_call,
                last_call=last_call,
            )

    async def get_top_conversations_by_cost(
        self,
        limit: int = 10,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> List[Tuple[str, float]]:
        """
        Get most expensive conversations.

        Args:
            limit: Number of conversations to return
            period_start: Optional start date filter
            period_end: Optional end date filter

        Returns:
            List of (conversation_id, total_cost) tuples
        """
        if self.db is None:
            return []

        from models import APICallLog
        from sqlalchemy import select, func
        from sqlalchemy.ext.asyncio import AsyncSession

        if isinstance(self.db, AsyncSession):
            stmt = select(
                APICallLog.conversation_id,
                func.sum(APICallLog.cost_usd).label("total_cost")
            ).where(
                APICallLog.success == True,
                APICallLog.conversation_id.isnot(None)
            ).group_by(
                APICallLog.conversation_id
            ).order_by(
                func.sum(APICallLog.cost_usd).desc()
            ).limit(limit)

            if period_start:
                stmt = stmt.where(APICallLog.timestamp >= period_start)
            if period_end:
                stmt = stmt.where(APICallLog.timestamp < period_end)

            result = await self.db.execute(stmt)
            rows = result.all()

            return [(str(row.conversation_id), float(row.total_cost)) for row in rows]

        return []

    async def get_cost_trend(
        self,
        days: int = 30,
    ) -> List[Tuple[date, float]]:
        """
        Get daily cost trend for the past N days.

        Args:
            days: Number of days to look back

        Returns:
            List of (date, cost) tuples
        """
        trend = []

        for i in range(days):
            target_date = date.today() - timedelta(days=i)
            daily_agg = await self.aggregate_daily(target_date)
            trend.append((target_date, daily_agg.total_cost))

        # Reverse to get chronological order
        trend.reverse()

        return trend


class CostReporter:
    """Generate cost reports and summaries."""

    def __init__(self, aggregator: CostAggregator):
        self.aggregator = aggregator

    async def generate_daily_report(self, target_date: date) -> str:
        """
        Generate a human-readable daily cost report.

        Args:
            target_date: Date to report on

        Returns:
            Formatted report string
        """
        agg = await self.aggregator.aggregate_daily(target_date)

        report = f"""
# Daily Cost Report - {target_date.strftime('%Y-%m-%d')}

## Summary
- Total Cost: ${agg.total_cost:.2f}
- Total API Calls: {agg.total_calls:,}
- Total Tokens: {agg.total_tokens:,}
- Avg Cost/Call: ${agg.avg_cost_per_call:.4f}
- Avg Tokens/Call: {agg.avg_tokens_per_call:.0f}

## Cost by Model
"""
        for model, cost in sorted(agg.cost_by_model.items(), key=lambda x: x[1], reverse=True):
            calls = agg.calls_by_model.get(model, 0)
            tokens = agg.tokens_by_model.get(model, 0)
            report += f"- {model}: ${cost:.2f} ({calls} calls, {tokens:,} tokens)\n"

        report += "\n## Cost by Endpoint\n"
        for endpoint, cost in sorted(agg.cost_by_endpoint.items(), key=lambda x: x[1], reverse=True):
            calls = agg.calls_by_endpoint.get(endpoint, 0)
            report += f"- {endpoint}: ${cost:.2f} ({calls} calls)\n"

        return report

    async def generate_monthly_summary(self, year: int, month: int) -> str:
        """Generate monthly cost summary."""
        agg = await self.aggregator.aggregate_monthly(year, month)

        report = f"""
# Monthly Cost Summary - {year}-{month:02d}

## Overview
- Total Cost: ${agg.total_cost:.2f}
- Total API Calls: {agg.total_calls:,}
- Total Tokens: {agg.total_tokens:,}

## Top Models by Cost
"""
        for model, cost in sorted(agg.cost_by_model.items(), key=lambda x: x[1], reverse=True)[:5]:
            report += f"- {model}: ${cost:.2f}\n"

        report += "\n## Top Endpoints by Cost\n"
        for endpoint, cost in sorted(agg.cost_by_endpoint.items(), key=lambda x: x[1], reverse=True)[:5]:
            report += f"- {endpoint}: ${cost:.2f}\n"

        return report


# Background job for automatic aggregation

async def run_daily_aggregation_job(
    db,
    alert_manager,
):
    """
    Background job that runs daily aggregation and checks alerts.

    This should be scheduled to run daily (e.g., via cron or background task).

    Args:
        db: Database connection
        alert_manager: AlertManager instance
    """
    aggregator = CostAggregator(db)

    # Aggregate yesterday's costs
    yesterday = date.today() - timedelta(days=1)
    daily_agg = await aggregator.aggregate_daily(yesterday)

    # Check alerts
    today_agg = await aggregator.aggregate_daily(date.today())
    await alert_manager.check_alerts(current_daily_cost=today_agg.total_cost)

    # Log aggregation results
    print(f"Daily aggregation complete for {yesterday}")
    print(f"Total cost: ${daily_agg.total_cost:.2f}")
    print(f"Total calls: {daily_agg.total_calls}")

    return daily_agg
