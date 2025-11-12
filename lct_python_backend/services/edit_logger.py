"""
Edit Logging Service
Week 10: Edit History & Training Data Export

Logs all user edits to nodes, relationships, and other entities
for training data collection and audit trail.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from models import EditsLog


class EditLogger:
    """
    Service for logging user edits to the database

    All edits are logged to the edits_log table for:
    - Training data collection
    - Audit trail
    - Analytics on user behavior
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log_edit(
        self,
        conversation_id: str,
        target_type: str,
        target_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        edit_type: str,
        user_id: str = "anonymous",
        user_comment: Optional[str] = None,
        user_confidence: float = 1.0
    ) -> str:
        """
        Log an edit to the database

        Args:
            conversation_id: UUID of conversation
            target_type: Type of target ('node', 'relationship', 'cluster', etc.)
            target_id: UUID of target entity
            field_name: Name of field edited (e.g., 'summary', 'title')
            old_value: Original value
            new_value: New value
            edit_type: Type of edit ('correction', 'addition', 'deletion', etc.)
            user_id: User who made the edit
            user_comment: Optional comment explaining the edit
            user_confidence: User's confidence in the edit (0.0-1.0)

        Returns:
            UUID of created edit log entry
        """
        edit_log = EditsLog(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            target_type=target_type,
            target_id=uuid.UUID(target_id),
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            edit_type=edit_type,
            user_id=user_id,
            user_comment=user_comment,
            user_confidence=user_confidence,
            exported_for_training=False,
            training_dataset_id=None,
            created_at=datetime.now()
        )

        self.db.add(edit_log)
        await self.db.commit()
        await self.db.refresh(edit_log)

        return str(edit_log.id)

    async def log_node_edit(
        self,
        conversation_id: str,
        node_id: str,
        changes: Dict[str, Dict[str, Any]],
        user_id: str = "anonymous",
        user_comment: Optional[str] = None
    ) -> List[str]:
        """
        Log multiple field changes to a node

        Args:
            conversation_id: UUID of conversation
            node_id: UUID of node
            changes: Dict of {field_name: {'old': old_value, 'new': new_value}}
            user_id: User who made the edit
            user_comment: Optional comment

        Returns:
            List of edit log entry UUIDs

        Example:
            await logger.log_node_edit(
                conv_id, node_id,
                {
                    'title': {'old': 'Old Title', 'new': 'New Title'},
                    'summary': {'old': 'Old summary', 'new': 'New summary'}
                }
            )
        """
        edit_ids = []

        for field_name, change in changes.items():
            edit_id = await self.log_edit(
                conversation_id=conversation_id,
                target_type='node',
                target_id=node_id,
                field_name=field_name,
                old_value=change.get('old'),
                new_value=change.get('new'),
                edit_type='correction',
                user_id=user_id,
                user_comment=user_comment
            )
            edit_ids.append(edit_id)

        return edit_ids

    async def get_edits_for_conversation(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        target_type: Optional[str] = None,
        exported_only: bool = False,
        unexported_only: bool = False
    ) -> List[EditsLog]:
        """
        Get all edits for a conversation

        Args:
            conversation_id: UUID of conversation
            limit: Maximum number of edits to return
            offset: Number of edits to skip
            target_type: Filter by target type (e.g., 'node')
            exported_only: Only return exported edits
            unexported_only: Only return unexported edits

        Returns:
            List of EditsLog records
        """
        query = select(EditsLog).where(
            EditsLog.conversation_id == uuid.UUID(conversation_id)
        )

        if target_type:
            query = query.where(EditsLog.target_type == target_type)

        if exported_only:
            query = query.where(EditsLog.exported_for_training == True)
        elif unexported_only:
            query = query.where(EditsLog.exported_for_training == False)

        query = query.order_by(EditsLog.created_at.desc())

        if offset:
            query = query.offset(offset)

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_edits_for_target(
        self,
        target_type: str,
        target_id: str,
        limit: Optional[int] = None
    ) -> List[EditsLog]:
        """
        Get all edits for a specific target entity

        Args:
            target_type: Type of target
            target_id: UUID of target
            limit: Maximum number to return

        Returns:
            List of EditsLog records ordered by time
        """
        query = select(EditsLog).where(
            EditsLog.target_type == target_type,
            EditsLog.target_id == uuid.UUID(target_id)
        ).order_by(EditsLog.created_at.desc())

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_as_exported(
        self,
        edit_ids: List[str],
        training_dataset_id: str
    ) -> int:
        """
        Mark edits as exported for training

        Args:
            edit_ids: List of edit UUIDs
            training_dataset_id: ID of training dataset

        Returns:
            Number of edits marked
        """
        count = 0
        for edit_id in edit_ids:
            result = await self.db.execute(
                select(EditsLog).where(EditsLog.id == uuid.UUID(edit_id))
            )
            edit_log = result.scalar_one_or_none()

            if edit_log:
                edit_log.exported_for_training = True
                edit_log.training_dataset_id = training_dataset_id
                count += 1

        await self.db.commit()
        return count

    async def get_edit_statistics(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics about edits for a conversation

        Args:
            conversation_id: UUID of conversation

        Returns:
            Dict with edit statistics
        """
        # Total edits
        total_result = await self.db.execute(
            select(func.count(EditsLog.id)).where(
                EditsLog.conversation_id == uuid.UUID(conversation_id)
            )
        )
        total_edits = total_result.scalar()

        # Edits by type
        type_result = await self.db.execute(
            select(
                EditsLog.target_type,
                func.count(EditsLog.id)
            ).where(
                EditsLog.conversation_id == uuid.UUID(conversation_id)
            ).group_by(EditsLog.target_type)
        )
        edits_by_type = {row[0]: row[1] for row in type_result.all()}

        # Edits by edit_type
        edit_type_result = await self.db.execute(
            select(
                EditsLog.edit_type,
                func.count(EditsLog.id)
            ).where(
                EditsLog.conversation_id == uuid.UUID(conversation_id)
            ).group_by(EditsLog.edit_type)
        )
        edits_by_edit_type = {row[0]: row[1] for row in edit_type_result.all()}

        # Export status
        exported_result = await self.db.execute(
            select(func.count(EditsLog.id)).where(
                EditsLog.conversation_id == uuid.UUID(conversation_id),
                EditsLog.exported_for_training == True
            )
        )
        exported_count = exported_result.scalar()

        return {
            "total_edits": total_edits,
            "edits_by_target_type": edits_by_type,
            "edits_by_edit_type": edits_by_edit_type,
            "exported_count": exported_count,
            "unexported_count": total_edits - exported_count,
            "export_percentage": (exported_count / total_edits * 100) if total_edits > 0 else 0
        }

    async def add_feedback(
        self,
        edit_id: str,
        feedback: str
    ) -> bool:
        """
        Add feedback to an edit log entry

        Args:
            edit_id: UUID of edit
            feedback: Feedback text

        Returns:
            True if successful
        """
        result = await self.db.execute(
            select(EditsLog).where(EditsLog.id == uuid.UUID(edit_id))
        )
        edit_log = result.scalar_one_or_none()

        if edit_log:
            # Append feedback to user_comment
            if edit_log.user_comment:
                edit_log.user_comment += f"\n\nFeedback: {feedback}"
            else:
                edit_log.user_comment = f"Feedback: {feedback}"

            await self.db.commit()
            return True

        return False
