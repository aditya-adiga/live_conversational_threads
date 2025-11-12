"""
Training Data Export Service
Week 10: Edit History & Training Data Export

Exports edit logs in formats suitable for AI model fine-tuning.
Supports JSONL (OpenAI), CSV, and Markdown formats.
"""

import json
import csv
from typing import List, Dict, Any, Optional
from io import StringIO
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from models import EditsLog, Node, Conversation


class TrainingDataExporter:
    """
    Service for exporting edit logs as training data

    Supports multiple formats:
    - JSONL: For OpenAI fine-tuning
    - CSV: For analysis in spreadsheets
    - Markdown: For human review
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def export_conversation_edits(
        self,
        conversation_id: str,
        format: str = "jsonl",
        unexported_only: bool = False
    ) -> str:
        """
        Export all edits for a conversation

        Args:
            conversation_id: UUID of conversation
            format: Export format ('jsonl', 'csv', 'markdown')
            unexported_only: Only export edits not yet exported

        Returns:
            Exported data as string
        """
        # Get edits
        query = select(EditsLog).where(
            EditsLog.conversation_id == uuid.UUID(conversation_id)
        )

        if unexported_only:
            query = query.where(EditsLog.exported_for_training == False)

        query = query.order_by(EditsLog.created_at)

        result = await self.db.execute(query)
        edits = list(result.scalars().all())

        # Get conversation name
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
        )
        conversation = conv_result.scalar_one_or_none()
        conv_name = conversation.conversation_name if conversation else "Unknown"

        # Export based on format
        if format == "jsonl":
            return await self._export_jsonl(edits, conversation_id, conv_name)
        elif format == "csv":
            return await self._export_csv(edits, conversation_id, conv_name)
        elif format == "markdown":
            return await self._export_markdown(edits, conversation_id, conv_name)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def _export_jsonl(
        self,
        edits: List[EditsLog],
        conversation_id: str,
        conv_name: str
    ) -> str:
        """
        Export edits in JSONL format for OpenAI fine-tuning

        Format:
        {
          "messages": [
            {"role": "system", "content": "You are analyzing conversation transcripts..."},
            {"role": "user", "content": "Original AI output: [text]"},
            {"role": "assistant", "content": "User correction: [text]"}
          ],
          "metadata": {...}
        }
        """
        lines = []

        system_message = (
            "You are analyzing conversation transcripts and generating summaries, "
            "titles, and keywords. Learn from user corrections to improve accuracy."
        )

        for edit in edits:
            # Get node details if this is a node edit
            node_context = await self._get_node_context(edit.target_id) if edit.target_type == 'node' else None

            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": system_message
                }
            ]

            # User message with original AI output
            if node_context:
                user_content = f"Context: {node_context.get('utterances_preview', 'N/A')}\n\n"
            else:
                user_content = ""

            user_content += f"Original {edit.field_name}: {edit.old_value or '(empty)'}"
            messages.append({
                "role": "user",
                "content": user_content
            })

            # Assistant message with user correction
            messages.append({
                "role": "assistant",
                "content": f"Corrected {edit.field_name}: {edit.new_value or '(empty)'}"
            })

            # Build training example
            example = {
                "messages": messages,
                "metadata": {
                    "conversation_id": conversation_id,
                    "conversation_name": conv_name,
                    "edit_id": str(edit.id),
                    "edit_type": edit.edit_type,
                    "target_type": edit.target_type,
                    "target_id": str(edit.target_id),
                    "field_name": edit.field_name,
                    "timestamp": edit.created_at.isoformat() if edit.created_at else None,
                    "user_id": edit.user_id,
                    "user_comment": edit.user_comment,
                    "user_confidence": edit.user_confidence
                }
            }

            lines.append(json.dumps(example))

        return "\n".join(lines)

    async def _export_csv(
        self,
        edits: List[EditsLog],
        conversation_id: str,
        conv_name: str
    ) -> str:
        """
        Export edits in CSV format for analysis

        Columns:
        - edit_id, conversation_id, conversation_name, timestamp
        - target_type, target_id, field_name
        - old_value, new_value
        - edit_type, user_id, user_comment, user_confidence
        - exported_for_training
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'edit_id', 'conversation_id', 'conversation_name', 'timestamp',
            'target_type', 'target_id', 'field_name',
            'old_value', 'new_value',
            'edit_type', 'user_id', 'user_comment', 'user_confidence',
            'exported_for_training', 'training_dataset_id'
        ])

        # Rows
        for edit in edits:
            writer.writerow([
                str(edit.id),
                conversation_id,
                conv_name,
                edit.created_at.isoformat() if edit.created_at else '',
                edit.target_type,
                str(edit.target_id),
                edit.field_name,
                edit.old_value or '',
                edit.new_value or '',
                edit.edit_type,
                edit.user_id,
                edit.user_comment or '',
                edit.user_confidence,
                edit.exported_for_training,
                edit.training_dataset_id or ''
            ])

        return output.getvalue()

    async def _export_markdown(
        self,
        edits: List[EditsLog],
        conversation_id: str,
        conv_name: str
    ) -> str:
        """
        Export edits in Markdown format for human review

        Format:
        # Edit History: {conversation_name}

        ## Edit 1: {field_name} - {timestamp}

        **Type:** {edit_type}
        **Target:** {target_type} / {target_id}
        **User:** {user_id}

        **Original:**
        ```
        {old_value}
        ```

        **Corrected:**
        ```
        {new_value}
        ```

        **Comment:** {user_comment}

        ---
        """
        lines = [
            f"# Edit History: {conv_name}",
            "",
            f"**Conversation ID:** `{conversation_id}`",
            f"**Total Edits:** {len(edits)}",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]

        for i, edit in enumerate(edits, 1):
            lines.extend([
                f"## Edit {i}: {edit.field_name} - {edit.created_at.strftime('%Y-%m-%d %H:%M:%S') if edit.created_at else 'N/A'}",
                "",
                f"**Type:** {edit.edit_type}",
                f"**Target:** {edit.target_type} / `{edit.target_id}`",
                f"**User:** {edit.user_id}",
                f"**Confidence:** {edit.user_confidence}",
                ""
            ])

            # Old value
            lines.extend([
                "**Original:**",
                "```",
                edit.old_value or "(empty)",
                "```",
                ""
            ])

            # New value
            lines.extend([
                "**Corrected:**",
                "```",
                edit.new_value or "(empty)",
                "```",
                ""
            ])

            # Comment
            if edit.user_comment:
                lines.extend([
                    f"**Comment:** {edit.user_comment}",
                    ""
                ])

            # Export status
            if edit.exported_for_training:
                lines.extend([
                    f"**Exported:** Yes (Dataset: `{edit.training_dataset_id}`)",
                    ""
                ])

            lines.extend([
                "---",
                ""
            ])

        return "\n".join(lines)

    async def _get_node_context(self, node_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get context about a node for training data

        Args:
            node_id: UUID of node

        Returns:
            Dict with node context (utterances preview, etc.)
        """
        try:
            result = await self.db.execute(
                select(Node).where(Node.id == node_id)
            )
            node = result.scalar_one_or_none()

            if not node:
                return None

            # Get utterances preview (first 200 chars of summary)
            summary_preview = node.summary[:200] + "..." if node.summary and len(node.summary) > 200 else node.summary

            return {
                "node_name": node.node_name,
                "summary": node.summary,
                "utterances_preview": summary_preview,
                "key_points": node.key_points or []
            }
        except Exception as e:
            print(f"[WARNING] Failed to get node context: {e}")
            return None

    async def generate_dataset_id(self, conversation_id: str) -> str:
        """
        Generate a unique training dataset ID

        Args:
            conversation_id: UUID of conversation

        Returns:
            Dataset ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conv_short = str(conversation_id)[:8]
        return f"training_{conv_short}_{timestamp}"
