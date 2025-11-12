"""
Cognitive Bias Detection Service
Week 12: Advanced AI Analysis

Identifies 25+ types of cognitive biases and logical fallacies in conversation nodes.

Categories:
- Confirmation Biases: Seeking information that confirms existing beliefs
- Memory Biases: Distortions in how we recall information
- Social Biases: Influence of group dynamics and social pressure
- Decision-Making Biases: Systematic errors in judgment
- Attribution Biases: How we explain behavior and events
- Logical Fallacies: Errors in reasoning and argumentation
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Node, BiasAnalysis
from services.prompt_manager import get_prompt_manager
import anthropic
import os


# Comprehensive bias taxonomy
BIAS_CATEGORIES = {
    "confirmation": {
        "name": "Confirmation Biases",
        "description": "Seeking information that confirms existing beliefs",
        "biases": [
            "confirmation_bias",
            "cherry_picking",
            "motivated_reasoning",
            "belief_perseverance"
        ]
    },
    "memory": {
        "name": "Memory Biases",
        "description": "Distortions in how we recall information",
        "biases": [
            "hindsight_bias",
            "availability_heuristic",
            "recency_bias",
            "false_memory"
        ]
    },
    "social": {
        "name": "Social Biases",
        "description": "Influence of group dynamics and social pressure",
        "biases": [
            "groupthink",
            "authority_bias",
            "bandwagon_effect",
            "halo_effect",
            "in_group_bias"
        ]
    },
    "decision": {
        "name": "Decision-Making Biases",
        "description": "Systematic errors in judgment",
        "biases": [
            "anchoring",
            "sunk_cost_fallacy",
            "status_quo_bias",
            "optimism_bias",
            "planning_fallacy"
        ]
    },
    "attribution": {
        "name": "Attribution Biases",
        "description": "How we explain behavior and events",
        "biases": [
            "fundamental_attribution_error",
            "self_serving_bias",
            "just_world_hypothesis"
        ]
    },
    "logical": {
        "name": "Logical Fallacies",
        "description": "Errors in reasoning and argumentation",
        "biases": [
            "slippery_slope",
            "straw_man",
            "false_dichotomy",
            "ad_hominem",
            "appeal_to_emotion",
            "hasty_generalization"
        ]
    }
}


class BiasDetector:
    """Detects and classifies cognitive biases in conversation nodes"""

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
        Analyze all nodes in a conversation for cognitive biases

        Args:
            conversation_id: UUID of conversation
            force_reanalysis: Re-analyze even if already analyzed

        Returns:
            {
                "total_nodes": int,
                "analyzed": int,
                "nodes_with_biases": int,
                "bias_count": int,
                "by_category": {category: count},
                "by_bias": {bias_name: count},
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
                "nodes_with_biases": 0,
                "bias_count": 0,
                "by_category": {},
                "by_bias": {},
                "nodes": []
            }

        analyzed_count = 0
        nodes_with_biases = 0
        total_bias_count = 0
        by_category = {}
        by_bias = {}
        node_results = []

        for node in nodes:
            # Check if already analyzed
            existing = await self.db.execute(
                select(BiasAnalysis).where(
                    BiasAnalysis.node_id == node.id
                )
            )
            existing_analyses = existing.scalars().all()

            if existing_analyses and not force_reanalysis:
                # Use existing analyses
                biases = [
                    {
                        "bias_type": a.bias_type,
                        "category": a.category,
                        "severity": a.severity,
                        "confidence": a.confidence,
                        "description": a.description,
                        "evidence": json.loads(a.evidence) if a.evidence else []
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
                biases = await self._analyze_node(node, conversation_id)

                # Save analyses
                for bias in biases:
                    new_analysis = BiasAnalysis(
                        id=uuid.uuid4(),
                        node_id=node.id,
                        conversation_id=uuid.UUID(conversation_id),
                        bias_type=bias["bias_type"],
                        category=bias["category"],
                        severity=bias["severity"],
                        confidence=bias["confidence"],
                        description=bias["description"],
                        evidence=json.dumps(bias["evidence"]),
                        analyzed_at=datetime.utcnow()
                    )
                    self.db.add(new_analysis)

                await self.db.commit()

            analyzed_count += 1

            if biases:
                nodes_with_biases += 1
                total_bias_count += len(biases)

                # Count by category and bias type
                for bias in biases:
                    category = bias["category"]
                    bias_type = bias["bias_type"]

                    by_category[category] = by_category.get(category, 0) + 1
                    by_bias[bias_type] = by_bias.get(bias_type, 0) + 1

            node_results.append({
                "node_id": str(node.id),
                "node_name": node.node_name,
                "bias_count": len(biases),
                "biases": biases
            })

        return {
            "total_nodes": len(nodes),
            "analyzed": analyzed_count,
            "nodes_with_biases": nodes_with_biases,
            "bias_count": total_bias_count,
            "by_category": by_category,
            "by_bias": by_bias,
            "nodes": node_results
        }

    async def _analyze_node(
        self,
        node: Node,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single node for cognitive biases using LLM

        Returns:
            [{
                "bias_type": str,
                "category": str,
                "severity": 0.0-1.0,
                "confidence": 0.0-1.0,
                "description": str,
                "evidence": [str]
            }]
        """
        # Get the prompt template
        prompt_text = self.prompt_manager.render_prompt(
            "bias_detection",
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

            # Return list of detected biases
            return result.get("biases", [])

        except Exception as e:
            print(f"Error analyzing node {node.id} for biases: {e}")
            # Return empty list on error
            return []

    async def get_conversation_results(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get existing bias analysis results for a conversation"""
        # Get all analyses for conversation
        result = await self.db.execute(
            select(BiasAnalysis, Node).join(
                Node, BiasAnalysis.node_id == Node.id
            ).where(
                BiasAnalysis.conversation_id == uuid.UUID(conversation_id)
            )
        )
        rows = result.all()

        if not rows:
            return {
                "total_nodes": 0,
                "analyzed": 0,
                "nodes_with_biases": 0,
                "bias_count": 0,
                "by_category": {},
                "by_bias": {},
                "nodes": []
            }

        # Group by node
        nodes_dict = {}
        by_category = {}
        by_bias = {}

        for analysis, node in rows:
            node_id = str(node.id)

            if node_id not in nodes_dict:
                nodes_dict[node_id] = {
                    "node_id": node_id,
                    "node_name": node.node_name,
                    "bias_count": 0,
                    "biases": []
                }

            bias_data = {
                "bias_type": analysis.bias_type,
                "category": analysis.category,
                "severity": analysis.severity,
                "confidence": analysis.confidence,
                "description": analysis.description,
                "evidence": json.loads(analysis.evidence) if analysis.evidence else [],
                "analyzed_at": analysis.analyzed_at.isoformat()
            }

            nodes_dict[node_id]["biases"].append(bias_data)
            nodes_dict[node_id]["bias_count"] += 1

            # Count by category and bias
            by_category[analysis.category] = by_category.get(analysis.category, 0) + 1
            by_bias[analysis.bias_type] = by_bias.get(analysis.bias_type, 0) + 1

        node_results = list(nodes_dict.values())
        nodes_with_biases = len([n for n in node_results if n["bias_count"] > 0])

        return {
            "total_nodes": len(set(str(node.id) for _, node in rows)),
            "analyzed": len(node_results),
            "nodes_with_biases": nodes_with_biases,
            "bias_count": len(rows),
            "by_category": by_category,
            "by_bias": by_bias,
            "nodes": node_results
        }

    async def get_node_biases(self, node_id: str) -> List[Dict[str, Any]]:
        """Get bias analyses for a specific node"""
        result = await self.db.execute(
            select(BiasAnalysis).where(
                BiasAnalysis.node_id == uuid.UUID(node_id)
            )
        )
        analyses = result.scalars().all()

        return [
            {
                "bias_type": a.bias_type,
                "category": a.category,
                "severity": a.severity,
                "confidence": a.confidence,
                "description": a.description,
                "evidence": json.loads(a.evidence) if a.evidence else [],
                "analyzed_at": a.analyzed_at.isoformat()
            }
            for a in analyses
        ]


def get_bias_info(bias_type: str) -> Dict[str, Any]:
    """Get metadata for a specific bias type"""
    bias_metadata = {
        # Confirmation Biases
        "confirmation_bias": {
            "name": "Confirmation Bias",
            "category": "confirmation",
            "description": "Seeking information that confirms existing beliefs while ignoring contradictory evidence"
        },
        "cherry_picking": {
            "name": "Cherry Picking",
            "category": "confirmation",
            "description": "Selecting only data that supports a position while ignoring contradictory data"
        },
        "motivated_reasoning": {
            "name": "Motivated Reasoning",
            "category": "confirmation",
            "description": "Reasoning to reach a desired conclusion rather than following evidence"
        },
        "belief_perseverance": {
            "name": "Belief Perseverance",
            "category": "confirmation",
            "description": "Maintaining beliefs despite contradictory evidence"
        },

        # Memory Biases
        "hindsight_bias": {
            "name": "Hindsight Bias",
            "category": "memory",
            "description": "Believing past events were more predictable than they actually were"
        },
        "availability_heuristic": {
            "name": "Availability Heuristic",
            "category": "memory",
            "description": "Overestimating likelihood of events based on their memorability"
        },
        "recency_bias": {
            "name": "Recency Bias",
            "category": "memory",
            "description": "Giving undue weight to recent events over historical data"
        },
        "false_memory": {
            "name": "False Memory",
            "category": "memory",
            "description": "Remembering events differently than they occurred"
        },

        # Social Biases
        "groupthink": {
            "name": "Groupthink",
            "category": "social",
            "description": "Desire for harmony leading to poor decision-making"
        },
        "authority_bias": {
            "name": "Authority Bias",
            "category": "social",
            "description": "Overvaluing opinions of authority figures"
        },
        "bandwagon_effect": {
            "name": "Bandwagon Effect",
            "category": "social",
            "description": "Adopting beliefs because many others hold them"
        },
        "halo_effect": {
            "name": "Halo Effect",
            "category": "social",
            "description": "Positive impression in one area influencing opinion in other areas"
        },
        "in_group_bias": {
            "name": "In-Group Bias",
            "category": "social",
            "description": "Favoring members of one's own group over outsiders"
        },

        # Decision-Making Biases
        "anchoring": {
            "name": "Anchoring Bias",
            "category": "decision",
            "description": "Over-relying on first piece of information encountered"
        },
        "sunk_cost_fallacy": {
            "name": "Sunk Cost Fallacy",
            "category": "decision",
            "description": "Continuing investment based on past costs rather than future value"
        },
        "status_quo_bias": {
            "name": "Status Quo Bias",
            "category": "decision",
            "description": "Preferring current state over change"
        },
        "optimism_bias": {
            "name": "Optimism Bias",
            "category": "decision",
            "description": "Overestimating likelihood of positive outcomes"
        },
        "planning_fallacy": {
            "name": "Planning Fallacy",
            "category": "decision",
            "description": "Underestimating time, costs, and risks of future actions"
        },

        # Attribution Biases
        "fundamental_attribution_error": {
            "name": "Fundamental Attribution Error",
            "category": "attribution",
            "description": "Overemphasizing personality-based explanations while underemphasizing situational factors"
        },
        "self_serving_bias": {
            "name": "Self-Serving Bias",
            "category": "attribution",
            "description": "Attributing successes to self and failures to external factors"
        },
        "just_world_hypothesis": {
            "name": "Just World Hypothesis",
            "category": "attribution",
            "description": "Believing the world is fundamentally fair and people get what they deserve"
        },

        # Logical Fallacies
        "slippery_slope": {
            "name": "Slippery Slope",
            "category": "logical",
            "description": "Assuming one action will lead to a chain of negative consequences"
        },
        "straw_man": {
            "name": "Straw Man",
            "category": "logical",
            "description": "Misrepresenting someone's argument to make it easier to attack"
        },
        "false_dichotomy": {
            "name": "False Dichotomy",
            "category": "logical",
            "description": "Presenting only two options when more exist"
        },
        "ad_hominem": {
            "name": "Ad Hominem",
            "category": "logical",
            "description": "Attacking the person rather than their argument"
        },
        "appeal_to_emotion": {
            "name": "Appeal to Emotion",
            "category": "logical",
            "description": "Manipulating emotions rather than using valid reasoning"
        },
        "hasty_generalization": {
            "name": "Hasty Generalization",
            "category": "logical",
            "description": "Drawing broad conclusions from limited evidence"
        }
    }

    return bias_metadata.get(bias_type, {
        "name": bias_type.replace("_", " ").title(),
        "category": "unknown",
        "description": "Unknown bias type"
    })
