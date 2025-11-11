"""
API endpoints for graph generation and management.

Provides endpoints for:
- Generating graphs from conversations
- Retrieving graph data
- Managing nodes and edges
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
import uuid

from services import GraphGenerationService
from parsers import GoogleMeetParser


# Pydantic models for API responses

class NodeResponse(BaseModel):
    """Response model for a node."""
    id: str
    conversation_id: str
    title: str
    summary: str
    node_type: str
    level: int
    zoom_level_visible: List[int]
    utterance_ids: List[int]
    start_time: Optional[float]
    end_time: Optional[float]
    sequence_number: int
    speaker_info: dict
    keywords: List[str]
    metadata: dict

    class Config:
        from_attributes = True


class EdgeResponse(BaseModel):
    """Response model for an edge."""
    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    strength: float
    metadata: dict

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    """Response model for a complete graph."""
    conversation_id: str
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
    node_count: int
    edge_count: int
    metadata: dict


class GraphGenerationRequest(BaseModel):
    """Request model for graph generation."""
    conversation_id: str
    use_llm: bool = True
    save_to_db: bool = True


class GraphGenerationStatusResponse(BaseModel):
    """Response model for graph generation status."""
    success: bool
    conversation_id: str
    message: str
    node_count: int
    edge_count: int
    generation_time_seconds: Optional[float]
    cost_usd: Optional[float]


# Create router
router = APIRouter(prefix="/api/graph", tags=["graph"])


# Dependency to get database session
async def get_db() -> AsyncSession:
    """Get database session."""
    # TODO: Replace with actual database session
    return None


# Dependency to get LLM client
async def get_llm_client():
    """Get LLM client."""
    # TODO: Replace with actual LLM client initialization
    # For now, return None - service will use fallback
    return None


@router.post("/generate", response_model=GraphGenerationStatusResponse)
async def generate_graph(
    request: GraphGenerationRequest,
    db: AsyncSession = Depends(get_db),
    llm_client = Depends(get_llm_client),
):
    """
    Generate a conversation graph from a parsed transcript.

    This endpoint:
    1. Retrieves the conversation and its utterances from database
    2. Uses LLM to identify topic clusters at 5 zoom levels
    3. Creates nodes and edges
    4. Saves graph to database

    Args:
        request: Graph generation request
        db: Database session
        llm_client: LLM client

    Returns:
        GraphGenerationStatusResponse with status and metadata
    """
    import time
    start_time = time.time()

    conversation_id = request.conversation_id

    # Get conversation from database
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection not available"
        )

    try:
        from models import Conversation, Utterance as DBUtterance
        from sqlalchemy import select

        # Get conversation
        stmt = select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )

        # Get utterances
        stmt = select(DBUtterance).where(
            DBUtterance.conversation_id == uuid.UUID(conversation_id)
        ).order_by(DBUtterance.sequence_number)
        result = await db.execute(stmt)
        db_utterances = result.scalars().all()

        if not db_utterances:
            raise HTTPException(
                status_code=400,
                detail=f"No utterances found for conversation {conversation_id}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )

    # Convert to ParsedTranscript format
    from parsers.google_meet import ParsedTranscript, Utterance as ParserUtterance

    utterances = [
        ParserUtterance(
            speaker=u.speaker_id,
            text=u.text,
            start_time=u.timestamp_start,
            end_time=u.timestamp_end,
            timestamp_marker=u.timestamp_marker,
            sequence_number=u.sequence_number,
            metadata=u.metadata or {},
        )
        for u in db_utterances
    ]

    participants = list(set(u.speaker for u in utterances))

    transcript = ParsedTranscript(
        utterances=utterances,
        participants=participants,
        duration=utterances[-1].end_time if utterances[-1].end_time else None,
        source_file=None,
        parse_metadata={
            "utterance_count": len(utterances),
            "participant_count": len(participants),
        }
    )

    # Generate graph
    try:
        service = GraphGenerationService(
            llm_client=llm_client if request.use_llm else None,
            db=db if request.save_to_db else None,
        )

        graph = await service.generate_graph(
            conversation_id=conversation_id,
            transcript=transcript,
            save_to_db=request.save_to_db,
        )

        generation_time = time.time() - start_time

        return GraphGenerationStatusResponse(
            success=True,
            conversation_id=conversation_id,
            message=f"Successfully generated graph with {graph['node_count']} nodes and {graph['edge_count']} edges",
            node_count=graph['node_count'],
            edge_count=graph['edge_count'],
            generation_time_seconds=round(generation_time, 2),
            cost_usd=None,  # TODO: Extract from instrumentation
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate graph: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=GraphResponse)
async def get_graph(
    conversation_id: str,
    zoom_level: Optional[int] = Query(None, ge=1, le=5, description="Filter by zoom level"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the graph for a conversation.

    Args:
        conversation_id: Conversation UUID
        zoom_level: Optional zoom level filter (1-5)
        db: Database session

    Returns:
        GraphResponse with nodes and edges
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection not available"
        )

    try:
        from models import Node, Relationship
        from sqlalchemy import select

        # Get nodes
        stmt = select(Node).where(Node.conversation_id == uuid.UUID(conversation_id))

        if zoom_level:
            # Filter by zoom level using array contains
            from sqlalchemy import func
            stmt = stmt.where(func.array_position(Node.zoom_level_visible, zoom_level) != None)

        stmt = stmt.order_by(Node.sequence_number)

        result = await db.execute(stmt)
        nodes = result.scalars().all()

        if not nodes:
            raise HTTPException(
                status_code=404,
                detail=f"No nodes found for conversation {conversation_id}"
            )

        # Get edges
        node_ids = [node.id for node in nodes]

        stmt = select(Relationship).where(
            Relationship.source_node_id.in_(node_ids),
            Relationship.target_node_id.in_(node_ids),
        )

        result = await db.execute(stmt)
        edges = result.scalars().all()

        # Convert to response models
        node_responses = [
            NodeResponse(
                id=str(node.id),
                conversation_id=str(node.conversation_id),
                title=node.title,
                summary=node.summary,
                node_type=node.node_type,
                level=node.level,
                zoom_level_visible=node.zoom_level_visible or [],
                utterance_ids=node.utterance_ids or [],
                start_time=node.start_time,
                end_time=node.end_time,
                sequence_number=node.sequence_number,
                speaker_info=node.speaker_info or {},
                keywords=node.keywords or [],
                metadata=node.metadata or {},
            )
            for node in nodes
        ]

        edge_responses = [
            EdgeResponse(
                id=str(edge.id),
                source_node_id=str(edge.source_node_id),
                target_node_id=str(edge.target_node_id),
                relationship_type=edge.relationship_type,
                strength=edge.strength,
                metadata=edge.metadata or {},
            )
            for edge in edges
        ]

        return GraphResponse(
            conversation_id=conversation_id,
            nodes=node_responses,
            edges=edge_responses,
            node_count=len(node_responses),
            edge_count=len(edge_responses),
            metadata={
                "zoom_level_filter": zoom_level,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve graph: {str(e)}"
        )


@router.get("/{conversation_id}/nodes", response_model=List[NodeResponse])
async def get_nodes(
    conversation_id: str,
    zoom_level: Optional[int] = Query(None, ge=1, le=5),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all nodes for a conversation.

    Args:
        conversation_id: Conversation UUID
        zoom_level: Optional zoom level filter
        db: Database session

    Returns:
        List of NodeResponse
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        from models import Node
        from sqlalchemy import select

        stmt = select(Node).where(Node.conversation_id == uuid.UUID(conversation_id))

        if zoom_level:
            from sqlalchemy import func
            stmt = stmt.where(func.array_position(Node.zoom_level_visible, zoom_level) != None)

        stmt = stmt.order_by(Node.sequence_number)

        result = await db.execute(stmt)
        nodes = result.scalars().all()

        return [
            NodeResponse(
                id=str(node.id),
                conversation_id=str(node.conversation_id),
                title=node.title,
                summary=node.summary,
                node_type=node.node_type,
                level=node.level,
                zoom_level_visible=node.zoom_level_visible or [],
                utterance_ids=node.utterance_ids or [],
                start_time=node.start_time,
                end_time=node.end_time,
                sequence_number=node.sequence_number,
                speaker_info=node.speaker_info or {},
                keywords=node.keywords or [],
                metadata=node.metadata or {},
            )
            for node in nodes
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/edges", response_model=List[EdgeResponse])
async def get_edges(
    conversation_id: str,
    relationship_type: Optional[str] = Query(None, description="Filter by type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all edges for a conversation.

    Args:
        conversation_id: Conversation UUID
        relationship_type: Optional filter by type
        db: Database session

    Returns:
        List of EdgeResponse
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        from models import Node, Relationship
        from sqlalchemy import select

        # Get node IDs for this conversation
        stmt = select(Node.id).where(Node.conversation_id == uuid.UUID(conversation_id))
        result = await db.execute(stmt)
        node_ids = [row[0] for row in result.all()]

        if not node_ids:
            return []

        # Get edges
        stmt = select(Relationship).where(
            Relationship.source_node_id.in_(node_ids),
            Relationship.target_node_id.in_(node_ids),
        )

        if relationship_type:
            stmt = stmt.where(Relationship.relationship_type == relationship_type)

        result = await db.execute(stmt)
        edges = result.scalars().all()

        return [
            EdgeResponse(
                id=str(edge.id),
                source_node_id=str(edge.source_node_id),
                target_node_id=str(edge.target_node_id),
                relationship_type=edge.relationship_type,
                strength=edge.strength,
                metadata=edge.metadata or {},
            )
            for edge in edges
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for graph API."""
    return {
        "status": "healthy",
        "service": "graph_api",
        "timestamp": "2025-11-11T12:00:00",
    }
