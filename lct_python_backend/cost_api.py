"""
API endpoints for cost tracking and metrics.

Provides endpoints for:
- Viewing cost aggregations (daily, weekly, monthly)
- Viewing conversation-level costs
- Viewing cost trends
- Exporting cost reports
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date, datetime, timedelta
from pydantic import BaseModel

from instrumentation import (
    CostAggregator,
    CostReporter,
    CostAggregation,
    ConversationCost,
)


# Pydantic models for API responses

class CostAggregationResponse(BaseModel):
    """Response model for cost aggregation."""
    period_start: datetime
    period_end: datetime
    total_cost: float
    total_tokens: int
    total_calls: int
    cost_by_model: dict
    cost_by_endpoint: dict
    calls_by_model: dict
    calls_by_endpoint: dict
    tokens_by_model: dict
    avg_cost_per_call: float
    avg_tokens_per_call: float

    class Config:
        from_attributes = True


class ConversationCostResponse(BaseModel):
    """Response model for conversation cost."""
    conversation_id: str
    total_cost: float
    total_tokens: int
    total_calls: int
    cost_by_endpoint: dict
    cost_by_model: dict
    first_call: datetime
    last_call: datetime

    class Config:
        from_attributes = True


class CostTrendResponse(BaseModel):
    """Response model for cost trend."""
    date: str
    cost: float


class TopConversationCostResponse(BaseModel):
    """Response model for top conversations by cost."""
    conversation_id: str
    total_cost: float


# Create router
router = APIRouter(prefix="/api/costs", tags=["costs"])


# Dependency to get database session
# This should be replaced with your actual database session dependency
async def get_db() -> AsyncSession:
    """Get database session."""
    # TODO: Replace with actual database session
    # For now, return None - the aggregator will handle gracefully
    return None


@router.get("/daily", response_model=CostAggregationResponse)
async def get_daily_cost(
    target_date: Optional[date] = Query(None, description="Date to query (default: today)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get daily cost aggregation.

    Args:
        target_date: Date to query (default: today)
        db: Database session

    Returns:
        CostAggregationResponse with daily totals
    """
    if target_date is None:
        target_date = date.today()

    aggregator = CostAggregator(db)

    try:
        agg = await aggregator.aggregate_daily(target_date)
        return CostAggregationResponse(**agg.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate daily costs: {str(e)}")


@router.get("/weekly", response_model=CostAggregationResponse)
async def get_weekly_cost(
    week_start: Optional[date] = Query(None, description="Start of week (Monday)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get weekly cost aggregation.

    Args:
        week_start: Start of week (Monday). Default: current week
        db: Database session

    Returns:
        CostAggregationResponse with weekly totals
    """
    if week_start is None:
        # Get current week's Monday
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    aggregator = CostAggregator(db)

    try:
        agg = await aggregator.aggregate_weekly(week_start)
        return CostAggregationResponse(**agg.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate weekly costs: {str(e)}")


@router.get("/monthly", response_model=CostAggregationResponse)
async def get_monthly_cost(
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    month: Optional[int] = Query(None, description="Month (1-12, default: current month)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get monthly cost aggregation.

    Args:
        year: Year (default: current year)
        month: Month (1-12, default: current month)
        db: Database session

    Returns:
        CostAggregationResponse with monthly totals
    """
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    aggregator = CostAggregator(db)

    try:
        agg = await aggregator.aggregate_monthly(year, month)
        return CostAggregationResponse(**agg.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate monthly costs: {str(e)}")


@router.get("/conversation/{conversation_id}", response_model=ConversationCostResponse)
async def get_conversation_cost(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost breakdown for a specific conversation.

    Args:
        conversation_id: Conversation UUID
        db: Database session

    Returns:
        ConversationCostResponse with cost breakdown
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection not available"
        )

    aggregator = CostAggregator(db)

    try:
        cost = await aggregator.get_conversation_cost(conversation_id)
        return ConversationCostResponse(**cost.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation cost: {str(e)}")


@router.get("/trend", response_model=List[CostTrendResponse])
async def get_cost_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get daily cost trend.

    Args:
        days: Number of days to look back (1-365)
        db: Database session

    Returns:
        List of daily costs
    """
    aggregator = CostAggregator(db)

    try:
        trend = await aggregator.get_cost_trend(days=days)
        return [
            CostTrendResponse(date=d.isoformat(), cost=c)
            for d, c in trend
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost trend: {str(e)}")


@router.get("/top-conversations", response_model=List[TopConversationCostResponse])
async def get_top_conversations_by_cost(
    limit: int = Query(10, ge=1, le=100, description="Number of conversations to return"),
    period_start: Optional[datetime] = Query(None, description="Start of period filter"),
    period_end: Optional[datetime] = Query(None, description="End of period filter"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most expensive conversations.

    Args:
        limit: Number of conversations to return (1-100)
        period_start: Optional start date filter
        period_end: Optional end date filter
        db: Database session

    Returns:
        List of conversations with costs
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection not available"
        )

    aggregator = CostAggregator(db)

    try:
        top_convs = await aggregator.get_top_conversations_by_cost(
            limit=limit,
            period_start=period_start,
            period_end=period_end,
        )
        return [
            TopConversationCostResponse(conversation_id=conv_id, total_cost=cost)
            for conv_id, cost in top_convs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top conversations: {str(e)}")


@router.get("/report/daily")
async def get_daily_report(
    target_date: Optional[date] = Query(None, description="Date to report on (default: today)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get human-readable daily cost report.

    Args:
        target_date: Date to report on (default: today)
        db: Database session

    Returns:
        Markdown-formatted report
    """
    if target_date is None:
        target_date = date.today()

    aggregator = CostAggregator(db)
    reporter = CostReporter(aggregator)

    try:
        report = await reporter.generate_daily_report(target_date)
        return {"report": report, "format": "markdown"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/report/monthly")
async def get_monthly_report(
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    month: Optional[int] = Query(None, description="Month (1-12, default: current month)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get human-readable monthly cost report.

    Args:
        year: Year (default: current year)
        month: Month (1-12, default: current month)
        db: Database session

    Returns:
        Markdown-formatted report
    """
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    aggregator = CostAggregator(db)
    reporter = CostReporter(aggregator)

    try:
        report = await reporter.generate_monthly_summary(year, month)
        return {"report": report, "format": "markdown"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for cost tracking API."""
    return {
        "status": "healthy",
        "service": "cost_tracking",
        "timestamp": datetime.now().isoformat(),
    }
