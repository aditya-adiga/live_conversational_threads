"""
API endpoints for importing transcripts.

Provides endpoints for:
- Importing Google Meet transcripts (PDF/TXT)
- Parsing and validating transcripts
- Saving to database
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pathlib import Path
import tempfile
import uuid
from datetime import datetime

from pydantic import BaseModel

from parsers import GoogleMeetParser, ParsedTranscript, ValidationResult
from models import Conversation, Utterance as DBUtterance


# Pydantic models for API responses

class UtteranceResponse(BaseModel):
    """Response model for utterance."""
    speaker: str
    text: str
    start_time: Optional[float]
    end_time: Optional[float]
    sequence_number: int

    class Config:
        from_attributes = True


class ValidationResponse(BaseModel):
    """Response model for validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    stats: dict


class ParsedTranscriptResponse(BaseModel):
    """Response model for parsed transcript."""
    conversation_id: str
    utterance_count: int
    participant_count: int
    participants: List[str]
    duration: Optional[float]
    validation: ValidationResponse
    sample_utterances: List[UtteranceResponse]


class ImportStatusResponse(BaseModel):
    """Response model for import status."""
    success: bool
    conversation_id: Optional[str]
    message: str
    utterance_count: int
    participant_count: int


# Create router
router = APIRouter(prefix="/api/import", tags=["import"])


# Dependency to get database session
async def get_db() -> AsyncSession:
    """Get database session."""
    # TODO: Replace with actual database session
    # For now, return None - the endpoint will handle gracefully
    return None


@router.post("/google-meet", response_model=ImportStatusResponse)
async def import_google_meet_transcript(
    file: UploadFile = File(..., description="Google Meet transcript (PDF or TXT)"),
    conversation_name: Optional[str] = Form(None, description="Name for this conversation"),
    owner_id: Optional[str] = Form(None, description="Owner/user ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Import a Google Meet transcript from PDF or TXT file.

    This endpoint:
    1. Accepts uploaded PDF or TXT file
    2. Parses speaker-diarized transcript
    3. Extracts timestamps
    4. Validates the transcript
    5. Saves to database (conversation + utterances)

    Args:
        file: Uploaded transcript file (PDF or TXT)
        conversation_name: Optional name for the conversation
        owner_id: Optional owner/user ID
        db: Database session

    Returns:
        ImportStatusResponse with success status and metadata
    """

    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.txt', '.text']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Only PDF and TXT are supported."
        )

    # Save uploaded file to temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Parse the transcript
    try:
        parser = GoogleMeetParser()
        transcript = parser.parse_file(temp_path)

    except ValueError as e:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse transcript: {str(e)}")

    except Exception as e:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error during parsing: {str(e)}")

    finally:
        # Always clean up temp file
        try:
            Path(temp_path).unlink(missing_ok=True)
        except:
            pass

    # Validate the transcript
    validation = parser.validate_transcript(transcript)

    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Transcript validation failed: {', '.join(validation.errors)}"
        )

    # Save to database if connection available
    conversation_id = str(uuid.uuid4())

    if db is not None:
        try:
            # Create conversation record
            conversation = Conversation(
                id=uuid.UUID(conversation_id),
                conversation_name=conversation_name or file.filename,
                conversation_type='transcript',
                source_type='google_meet',
                owner_id=owner_id,
                participant_count=len(transcript.participants),
                participants=[
                    {"name": p, "utterance_count": sum(1 for u in transcript.utterances if u.speaker == p)}
                    for p in transcript.participants
                ],
                duration_seconds=transcript.duration,
                created_at=datetime.now(),
                metadata={
                    'source_file': file.filename,
                    'parse_metadata': transcript.parse_metadata,
                    'validation': {
                        'warnings': validation.warnings,
                        'stats': validation.stats,
                    }
                }
            )

            db.add(conversation)

            # Create utterance records
            for utt in transcript.utterances:
                db_utterance = DBUtterance(
                    id=uuid.uuid4(),
                    conversation_id=uuid.UUID(conversation_id),
                    text=utt.text,
                    speaker_id=utt.speaker,
                    sequence_number=utt.sequence_number,
                    timestamp_start=utt.start_time,
                    timestamp_end=utt.end_time,
                    timestamp_marker=utt.timestamp_marker,
                    metadata=utt.metadata or {},
                )
                db.add(db_utterance)

            # Commit to database
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save to database: {str(e)}"
            )

    # Return success response
    return ImportStatusResponse(
        success=True,
        conversation_id=conversation_id,
        message=f"Successfully imported transcript with {len(transcript.utterances)} utterances",
        utterance_count=len(transcript.utterances),
        participant_count=len(transcript.participants),
    )


@router.post("/google-meet/preview", response_model=ParsedTranscriptResponse)
async def preview_google_meet_transcript(
    file: UploadFile = File(..., description="Google Meet transcript (PDF or TXT)"),
):
    """
    Preview/validate a Google Meet transcript without saving to database.

    This endpoint:
    1. Parses the uploaded file
    2. Validates the transcript
    3. Returns parsed data for review
    4. Does NOT save to database

    Args:
        file: Uploaded transcript file (PDF or TXT)

    Returns:
        ParsedTranscriptResponse with validation results and sample data
    """

    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.txt', '.text']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Only PDF and TXT are supported."
        )

    # Save to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Parse the transcript
    try:
        parser = GoogleMeetParser()
        transcript = parser.parse_file(temp_path)

    except ValueError as e:
        Path(temp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse transcript: {str(e)}")

    except Exception as e:
        Path(temp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error during parsing: {str(e)}")

    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except:
            pass

    # Validate
    validation = parser.validate_transcript(transcript)

    # Get sample utterances (first 10)
    sample_utterances = [
        UtteranceResponse(
            speaker=u.speaker,
            text=u.text,
            start_time=u.start_time,
            end_time=u.end_time,
            sequence_number=u.sequence_number,
        )
        for u in transcript.utterances[:10]
    ]

    # Return preview
    return ParsedTranscriptResponse(
        conversation_id=str(uuid.uuid4()),  # Generate temporary ID
        utterance_count=len(transcript.utterances),
        participant_count=len(transcript.participants),
        participants=transcript.participants,
        duration=transcript.duration,
        validation=ValidationResponse(
            is_valid=validation.is_valid,
            errors=validation.errors,
            warnings=validation.warnings,
            stats=validation.stats,
        ),
        sample_utterances=sample_utterances,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for import API."""
    return {
        "status": "healthy",
        "service": "import_api",
        "supported_formats": ["pdf", "txt"],
        "timestamp": datetime.now().isoformat(),
    }
