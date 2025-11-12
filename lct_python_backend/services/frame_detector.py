"""
Implicit Frame Detection Service
Week 13: Advanced AI Analysis

Detects hidden worldviews, normative assumptions, and underlying frameworks
that shape how participants interpret and discuss topics.

Frame Categories:
- Economic Frames: Market-based, socialist, growth-oriented
- Moral/Ethical Frames: Utilitarian, deontological, virtue ethics
- Political Frames: Progressive, conservative, libertarian
- Scientific Frames: Reductionist, holistic, empiricist
- Cultural Frames: Individualist, collectivist, hierarchical
- Temporal Frames: Short-term, long-term, cyclical
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Node, FrameAnalysis
from services.prompt_manager import get_prompt_manager
import anthropic
import os


# Frame taxonomy
FRAME_CATEGORIES = {
    "economic": {
        "name": "Economic Frames",
        "description": "Assumptions about markets, value, and resource allocation",
        "frames": [
            "market_fundamentalism",
            "socialist_framework",
            "growth_imperative",
            "scarcity_mindset",
            "abundance_mindset",
            "zero_sum_thinking"
        ]
    },
    "moral": {
        "name": "Moral/Ethical Frames",
        "description": "Underlying ethical principles and value systems",
        "frames": [
            "utilitarian",
            "deontological",
            "virtue_ethics",
            "care_ethics",
            "rights_based",
            "consequentialist"
        ]
    },
    "political": {
        "name": "Political Frames",
        "description": "Assumptions about power, governance, and social organization",
        "frames": [
            "progressive",
            "conservative",
            "libertarian",
            "authoritarian",
            "egalitarian",
            "meritocratic"
        ]
    },
    "scientific": {
        "name": "Scientific/Epistemological Frames",
        "description": "Assumptions about knowledge, causality, and understanding",
        "frames": [
            "reductionist",
            "holistic",
            "empiricist",
            "rationalist",
            "constructivist",
            "deterministic"
        ]
    },
    "cultural": {
        "name": "Cultural Frames",
        "description": "Assumptions about identity, community, and social relations",
        "frames": [
            "individualist",
            "collectivist",
            "hierarchical",
            "egalitarian_cultural",
            "universalist",
            "particularist"
        ]
    },
    "temporal": {
        "name": "Temporal Frames",
        "description": "Assumptions about time, change, and progress",
        "frames": [
            "short_term_focus",
            "long_term_thinking",
            "cyclical_view",
            "linear_progress",
            "status_quo_permanence",
            "radical_change"
        ]
    }
}


class FrameDetector:
    """Detects implicit frames and underlying assumptions in conversation nodes"""

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
        Analyze all nodes in a conversation for implicit frames

        Returns:
            {
                "total_nodes": int,
                "analyzed": int,
                "nodes_with_frames": int,
                "frame_count": int,
                "by_category": {category: count},
                "by_frame": {frame_type: count},
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
                "nodes_with_frames": 0,
                "frame_count": 0,
                "by_category": {},
                "by_frame": {},
                "nodes": []
            }

        analyzed_count = 0
        nodes_with_frames = 0
        total_frame_count = 0
        by_category = {}
        by_frame = {}
        node_results = []

        for node in nodes:
            # Check if already analyzed
            existing = await self.db.execute(
                select(FrameAnalysis).where(
                    FrameAnalysis.node_id == node.id
                )
            )
            existing_analyses = existing.scalars().all()

            if existing_analyses and not force_reanalysis:
                # Use existing analyses
                frames = [
                    {
                        "frame_type": a.frame_type,
                        "category": a.category,
                        "strength": a.strength,
                        "confidence": a.confidence,
                        "description": a.description,
                        "evidence": json.loads(a.evidence) if a.evidence else [],
                        "assumptions": json.loads(a.assumptions) if a.assumptions else [],
                        "implications": a.implications
                    }
                    for a in existing_analyses
                ]
            else:
                # Delete old analyses if re-analyzing
                if existing_analyses:
                    for analysis in existing_analyses:
                        await self.db.delete(analysis)
                    await self.db.commit()

                # Perform new analysis
                frames = await self._analyze_node(node, conversation_id)

                # Save analyses
                for frame in frames:
                    new_analysis = FrameAnalysis(
                        id=uuid.uuid4(),
                        node_id=node.id,
                        conversation_id=uuid.UUID(conversation_id),
                        frame_type=frame["frame_type"],
                        category=frame["category"],
                        strength=frame["strength"],
                        confidence=frame["confidence"],
                        description=frame["description"],
                        evidence=json.dumps(frame["evidence"]),
                        assumptions=json.dumps(frame["assumptions"]),
                        implications=frame["implications"],
                        analyzed_at=datetime.utcnow()
                    )
                    self.db.add(new_analysis)

                await self.db.commit()

            analyzed_count += 1

            if frames:
                nodes_with_frames += 1
                total_frame_count += len(frames)

                # Count by category and frame type
                for frame in frames:
                    category = frame["category"]
                    frame_type = frame["frame_type"]

                    by_category[category] = by_category.get(category, 0) + 1
                    by_frame[frame_type] = by_frame.get(frame_type, 0) + 1

            node_results.append({
                "node_id": str(node.id),
                "node_name": node.node_name,
                "frame_count": len(frames),
                "frames": frames
            })

        return {
            "total_nodes": len(nodes),
            "analyzed": analyzed_count,
            "nodes_with_frames": nodes_with_frames,
            "frame_count": total_frame_count,
            "by_category": by_category,
            "by_frame": by_frame,
            "nodes": node_results
        }

    async def _analyze_node(
        self,
        node: Node,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single node for implicit frames using LLM

        Returns:
            [{
                "frame_type": str,
                "category": str,
                "strength": 0.0-1.0,
                "confidence": 0.0-1.0,
                "description": str,
                "evidence": [str],
                "assumptions": [str],
                "implications": str
            }]
        """
        # Get the prompt template
        prompt_text = self.prompt_manager.render_prompt(
            "frame_detection",
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
                max_tokens=2048,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt_text
                }]
            )

            response_text = message.content[0].text

            # Parse JSON response
            result = json.loads(response_text)

            # Return list of detected frames
            return result.get("frames", [])

        except Exception as e:
            print(f"Error analyzing node {node.id} for frames: {e}")
            # Return empty list on error
            return []

    async def get_conversation_results(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get existing frame analysis results for a conversation"""
        # Get all analyses for conversation
        result = await self.db.execute(
            select(FrameAnalysis, Node).join(
                Node, FrameAnalysis.node_id == Node.id
            ).where(
                FrameAnalysis.conversation_id == uuid.UUID(conversation_id)
            )
        )
        rows = result.all()

        if not rows:
            return {
                "total_nodes": 0,
                "analyzed": 0,
                "nodes_with_frames": 0,
                "frame_count": 0,
                "by_category": {},
                "by_frame": {},
                "nodes": []
            }

        # Group by node
        nodes_dict = {}
        by_category = {}
        by_frame = {}

        for analysis, node in rows:
            node_id = str(node.id)

            if node_id not in nodes_dict:
                nodes_dict[node_id] = {
                    "node_id": node_id,
                    "node_name": node.node_name,
                    "frame_count": 0,
                    "frames": []
                }

            frame_data = {
                "frame_type": analysis.frame_type,
                "category": analysis.category,
                "strength": analysis.strength,
                "confidence": analysis.confidence,
                "description": analysis.description,
                "evidence": json.loads(analysis.evidence) if analysis.evidence else [],
                "assumptions": json.loads(analysis.assumptions) if analysis.assumptions else [],
                "implications": analysis.implications,
                "analyzed_at": analysis.analyzed_at.isoformat()
            }

            nodes_dict[node_id]["frames"].append(frame_data)
            nodes_dict[node_id]["frame_count"] += 1

            # Count by category and frame
            by_category[analysis.category] = by_category.get(analysis.category, 0) + 1
            by_frame[analysis.frame_type] = by_frame.get(analysis.frame_type, 0) + 1

        node_results = list(nodes_dict.values())
        nodes_with_frames = len([n for n in node_results if n["frame_count"] > 0])

        return {
            "total_nodes": len(set(str(node.id) for _, node in rows)),
            "analyzed": len(node_results),
            "nodes_with_frames": nodes_with_frames,
            "frame_count": len(rows),
            "by_category": by_category,
            "by_frame": by_frame,
            "nodes": node_results
        }

    async def get_node_frames(self, node_id: str) -> List[Dict[str, Any]]:
        """Get frame analyses for a specific node"""
        result = await self.db.execute(
            select(FrameAnalysis).where(
                FrameAnalysis.node_id == uuid.UUID(node_id)
            )
        )
        analyses = result.scalars().all()

        return [
            {
                "frame_type": a.frame_type,
                "category": a.category,
                "strength": a.strength,
                "confidence": a.confidence,
                "description": a.description,
                "evidence": json.loads(a.evidence) if a.evidence else [],
                "assumptions": json.loads(a.assumptions) if a.assumptions else [],
                "implications": a.implications,
                "analyzed_at": a.analyzed_at.isoformat()
            }
            for a in analyses
        ]


def get_frame_info(frame_type: str) -> Dict[str, Any]:
    """Get metadata for a specific frame type"""
    frame_metadata = {
        # Economic Frames
        "market_fundamentalism": {
            "name": "Market Fundamentalism",
            "category": "economic",
            "description": "Belief that market forces are the best way to organize all aspects of society"
        },
        "socialist_framework": {
            "name": "Socialist Framework",
            "category": "economic",
            "description": "Emphasis on collective ownership and equitable distribution of resources"
        },
        "growth_imperative": {
            "name": "Growth Imperative",
            "category": "economic",
            "description": "Assumption that continuous economic growth is necessary and desirable"
        },
        "scarcity_mindset": {
            "name": "Scarcity Mindset",
            "category": "economic",
            "description": "View that resources are fundamentally limited and must be competed for"
        },
        "abundance_mindset": {
            "name": "Abundance Mindset",
            "category": "economic",
            "description": "View that there is enough for everyone with proper distribution"
        },
        "zero_sum_thinking": {
            "name": "Zero-Sum Thinking",
            "category": "economic",
            "description": "Belief that one party's gain is another's loss"
        },

        # Moral/Ethical Frames
        "utilitarian": {
            "name": "Utilitarian Ethics",
            "category": "moral",
            "description": "Focus on maximizing overall good or happiness"
        },
        "deontological": {
            "name": "Deontological Ethics",
            "category": "moral",
            "description": "Emphasis on duties, rules, and principles regardless of outcomes"
        },
        "virtue_ethics": {
            "name": "Virtue Ethics",
            "category": "moral",
            "description": "Focus on character and virtues rather than rules or consequences"
        },
        "care_ethics": {
            "name": "Care Ethics",
            "category": "moral",
            "description": "Emphasis on relationships, empathy, and caring for others"
        },
        "rights_based": {
            "name": "Rights-Based Ethics",
            "category": "moral",
            "description": "Focus on individual rights and freedoms"
        },
        "consequentialist": {
            "name": "Consequentialism",
            "category": "moral",
            "description": "Judging actions solely by their outcomes"
        },

        # Political Frames
        "progressive": {
            "name": "Progressive Framework",
            "category": "political",
            "description": "Emphasis on social progress, reform, and reducing inequality"
        },
        "conservative": {
            "name": "Conservative Framework",
            "category": "political",
            "description": "Emphasis on tradition, stability, and gradual change"
        },
        "libertarian": {
            "name": "Libertarian Framework",
            "category": "political",
            "description": "Emphasis on individual liberty and minimal government intervention"
        },
        "authoritarian": {
            "name": "Authoritarian Framework",
            "category": "political",
            "description": "Emphasis on strong central authority and obedience"
        },
        "egalitarian": {
            "name": "Egalitarian Framework",
            "category": "political",
            "description": "Emphasis on equality and equal treatment"
        },
        "meritocratic": {
            "name": "Meritocratic Framework",
            "category": "political",
            "description": "Belief that success should be based on merit and ability"
        },

        # Scientific Frames
        "reductionist": {
            "name": "Reductionist Approach",
            "category": "scientific",
            "description": "Breaking down complex phenomena into simpler components"
        },
        "holistic": {
            "name": "Holistic Approach",
            "category": "scientific",
            "description": "Understanding systems as integrated wholes"
        },
        "empiricist": {
            "name": "Empiricist Approach",
            "category": "scientific",
            "description": "Emphasis on observation and evidence"
        },
        "rationalist": {
            "name": "Rationalist Approach",
            "category": "scientific",
            "description": "Emphasis on reason and logical deduction"
        },
        "constructivist": {
            "name": "Constructivist Approach",
            "category": "scientific",
            "description": "Knowledge as socially constructed"
        },
        "deterministic": {
            "name": "Deterministic View",
            "category": "scientific",
            "description": "Belief that events are causally determined"
        },

        # Cultural Frames
        "individualist": {
            "name": "Individualist Culture",
            "category": "cultural",
            "description": "Priority on individual autonomy and self-reliance"
        },
        "collectivist": {
            "name": "Collectivist Culture",
            "category": "cultural",
            "description": "Priority on group harmony and interdependence"
        },
        "hierarchical": {
            "name": "Hierarchical Structure",
            "category": "cultural",
            "description": "Acceptance of ranked social structures"
        },
        "egalitarian_cultural": {
            "name": "Egalitarian Culture",
            "category": "cultural",
            "description": "Minimizing status differences"
        },
        "universalist": {
            "name": "Universalist View",
            "category": "cultural",
            "description": "Belief in universal principles applying to everyone"
        },
        "particularist": {
            "name": "Particularist View",
            "category": "cultural",
            "description": "Emphasis on context and specific circumstances"
        },

        # Temporal Frames
        "short_term_focus": {
            "name": "Short-Term Focus",
            "category": "temporal",
            "description": "Prioritizing immediate concerns and quick results"
        },
        "long_term_thinking": {
            "name": "Long-Term Thinking",
            "category": "temporal",
            "description": "Prioritizing future impacts and sustainability"
        },
        "cyclical_view": {
            "name": "Cyclical Time View",
            "category": "temporal",
            "description": "Seeing time as cyclical with recurring patterns"
        },
        "linear_progress": {
            "name": "Linear Progress View",
            "category": "temporal",
            "description": "Belief in continuous forward progress"
        },
        "status_quo_permanence": {
            "name": "Status Quo Permanence",
            "category": "temporal",
            "description": "Assumption that current conditions will persist"
        },
        "radical_change": {
            "name": "Radical Change Frame",
            "category": "temporal",
            "description": "Expectation of transformative disruption"
        }
    }

    return frame_metadata.get(frame_type, {
        "name": frame_type.replace("_", " ").title(),
        "category": "unknown",
        "description": "Unknown frame type"
    })
