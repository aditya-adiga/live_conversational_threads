"""
Simulacra Level Detection Service
Week 11: Advanced AI Analysis

Classifies conversation utterances into 4 Simulacra levels based on
Jean Baudrillard's theory, analyzing communication intent and relationship to reality.

Levels:
- Level 1: Reflection of Reality (direct factual statements)
- Level 2: Perversion of Reality (interpretations, opinions)
- Level 3: Pretense of Reality (hypotheticals masking uncertainty)
- Level 4: Pure Simulacrum (abstract concepts disconnected from reality)
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import Node, SimulacraAnalysis
from services.prompt_manager import get_prompt_manager
import anthropic
import os


class SimulacraDetector:
    """Detects and classifies Simulacra levels in conversation nodes"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.prompt_manager = get_prompt_manager()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def analyze_conversation(
        self,
        conversation_id: str,
        force_reanalysis: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze all nodes in a conversation for Simulacra levels

        Args:
            conversation_id: UUID of conversation
            force_reanalysis: Re-analyze even if already analyzed

        Returns:
            {
                "total_nodes": int,
                "analyzed": int,
                "distribution": {1: count, 2: count, 3: count, 4: count},
                "nodes": [node_results...]
            }
        """
        # Get all nodes for conversation
        result = await self.db.execute(
            select(Node).where(Node.conversation_id == uuid.UUID(conversation_id))
        )
        nodes = result.scalars().all()

        if not nodes:
            return {
                "total_nodes": 0,
                "analyzed": 0,
                "distribution": {1: 0, 2: 0, 3: 0, 4: 0},
                "nodes": []
            }

        analyzed_count = 0
        node_results = []
        distribution = {1: 0, 2: 0, 3: 0, 4: 0}

        for node in nodes:
            # Check if already analyzed
            existing = await self.db.execute(
                select(SimulacraAnalysis).where(
                    SimulacraAnalysis.node_id == node.id
                )
            )
            existing_analysis = existing.scalar_one_or_none()

            if existing_analysis and not force_reanalysis:
                # Use existing analysis
                level = existing_analysis.level
                confidence = existing_analysis.confidence
                reasoning = existing_analysis.reasoning
                examples = json.loads(existing_analysis.examples) if existing_analysis.examples else []
            else:
                # Perform new analysis
                analysis = await self._analyze_node(node)
                level = analysis["level"]
                confidence = analysis["confidence"]
                reasoning = analysis["reasoning"]
                examples = analysis["examples"]

                # Save or update analysis
                if existing_analysis:
                    existing_analysis.level = level
                    existing_analysis.confidence = confidence
                    existing_analysis.reasoning = reasoning
                    existing_analysis.examples = json.dumps(examples)
                    existing_analysis.analyzed_at = datetime.utcnow()
                else:
                    new_analysis = SimulacraAnalysis(
                        id=uuid.uuid4(),
                        node_id=node.id,
                        conversation_id=uuid.UUID(conversation_id),
                        level=level,
                        confidence=confidence,
                        reasoning=reasoning,
                        examples=json.dumps(examples),
                        analyzed_at=datetime.utcnow()
                    )
                    self.db.add(new_analysis)

                await self.db.commit()

            analyzed_count += 1
            distribution[level] += 1

            node_results.append({
                "node_id": str(node.id),
                "node_name": node.node_name,
                "level": level,
                "confidence": confidence,
                "reasoning": reasoning,
                "examples": examples
            })

        return {
            "total_nodes": len(nodes),
            "analyzed": analyzed_count,
            "distribution": distribution,
            "nodes": node_results
        }

    async def _analyze_node(self, node: Node) -> Dict[str, Any]:
        """
        Analyze a single node for Simulacra level using LLM

        Returns:
            {
                "level": 1-4,
                "confidence": 0.0-1.0,
                "reasoning": str,
                "examples": [str]
            }
        """
        # Get the prompt template
        prompt_text = self.prompt_manager.render_prompt(
            "simulacra_detection",
            {
                "node_name": node.node_name or "Untitled",
                "node_summary": node.node_summary or "",
                "keywords": ", ".join(node.keywords or [])
            }
        )

        # Call LLM for analysis
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": prompt_text
                }]
            )

            response_text = message.content[0].text

            # Parse JSON response
            result = json.loads(response_text)

            return {
                "level": result.get("level", 2),
                "confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", "Unable to determine"),
                "examples": result.get("examples", [])
            }

        except Exception as e:
            print(f"Error analyzing node {node.id}: {e}")
            # Return default level 2 on error
            return {
                "level": 2,
                "confidence": 0.3,
                "reasoning": f"Analysis failed: {str(e)}",
                "examples": []
            }

    async def get_conversation_results(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get existing Simulacra analysis results for a conversation"""
        # Get all analyses for conversation
        result = await self.db.execute(
            select(SimulacraAnalysis, Node).join(
                Node, SimulacraAnalysis.node_id == Node.id
            ).where(
                SimulacraAnalysis.conversation_id == uuid.UUID(conversation_id)
            )
        )
        rows = result.all()

        if not rows:
            return {
                "total_nodes": 0,
                "analyzed": 0,
                "distribution": {1: 0, 2: 0, 3: 0, 4: 0},
                "nodes": []
            }

        distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        node_results = []

        for analysis, node in rows:
            distribution[analysis.level] += 1

            node_results.append({
                "node_id": str(node.id),
                "node_name": node.node_name,
                "level": analysis.level,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "examples": json.loads(analysis.examples) if analysis.examples else [],
                "analyzed_at": analysis.analyzed_at.isoformat()
            })

        return {
            "total_nodes": len(node_results),
            "analyzed": len(node_results),
            "distribution": distribution,
            "nodes": node_results
        }

    async def get_node_simulacra(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get Simulacra analysis for a specific node"""
        result = await self.db.execute(
            select(SimulacraAnalysis).where(
                SimulacraAnalysis.node_id == uuid.UUID(node_id)
            )
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            return None

        return {
            "level": analysis.level,
            "confidence": analysis.confidence,
            "reasoning": analysis.reasoning,
            "examples": json.loads(analysis.examples) if analysis.examples else [],
            "analyzed_at": analysis.analyzed_at.isoformat()
        }
