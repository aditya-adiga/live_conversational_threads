"""
Basic tests for EditLogger service
Week 10: Edit History & Training Data Export

Run with: pytest tests/test_edit_logger.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import uuid


@pytest.mark.asyncio
async def test_log_edit_basic():
    """Test basic edit logging"""
    from services.edit_logger import EditLogger

    # Mock database session
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    logger = EditLogger(mock_session)

    # Log an edit
    edit_id = await logger.log_edit(
        conversation_id="12345678-1234-1234-1234-123456789abc",
        target_type="node",
        target_id="87654321-4321-4321-4321-cba987654321",
        field_name="summary",
        old_value="Old summary",
        new_value="New summary",
        edit_type="correction",
        user_id="test_user"
    )

    # Verify edit was logged
    assert edit_id is not None
    assert isinstance(edit_id, str)
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_node_edit_multiple_fields():
    """Test logging multiple field changes"""
    from services.edit_logger import EditLogger

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    logger = EditLogger(mock_session)

    # Log multiple field changes
    changes = {
        "title": {"old": "Old Title", "new": "New Title"},
        "summary": {"old": "Old summary", "new": "New summary"},
        "keywords": {"old": ["old"], "new": ["new", "keywords"]}
    }

    edit_ids = await logger.log_node_edit(
        conversation_id="12345678-1234-1234-1234-123456789abc",
        node_id="87654321-4321-4321-4321-cba987654321",
        changes=changes,
        user_id="test_user",
        user_comment="Updated all fields"
    )

    # Should have logged 3 edits (one per field)
    assert len(edit_ids) == 3
    assert mock_session.add.call_count == 3
    assert mock_session.commit.call_count == 3


def test_edit_logger_initialization():
    """Test EditLogger can be initialized"""
    from services.edit_logger import EditLogger

    mock_session = MagicMock()
    logger = EditLogger(mock_session)

    assert logger is not None
    assert logger.db == mock_session


# Integration test placeholder
@pytest.mark.skip(reason="Requires database setup")
@pytest.mark.asyncio
async def test_edit_logger_database_integration():
    """
    Integration test with real database

    This would require:
    1. Test database setup
    2. Alembic migrations run
    3. Test data inserted
    """
    pass


# Training data export test placeholder
@pytest.mark.skip(reason="Requires database setup")
@pytest.mark.asyncio
async def test_training_data_export_jsonl():
    """
    Test JSONL export format

    Verify:
    - Correct OpenAI fine-tuning format
    - Messages structured correctly
    - Metadata included
    """
    pass
