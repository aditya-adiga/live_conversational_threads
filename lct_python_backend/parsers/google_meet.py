"""
Google Meet transcript parser.

Supports parsing of Google Meet transcripts in PDF and TXT formats.
Handles speaker diarization, timestamps, and various edge cases.
"""

import re
import pdfplumber
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class Utterance:
    """
    A single utterance by a speaker.

    Attributes:
        speaker: Speaker name/identifier
        text: The spoken text
        start_time: Start time in seconds (optional)
        end_time: End time in seconds (optional)
        timestamp_marker: Raw timestamp string if present (e.g., "00:10:47")
        sequence_number: Order in conversation
        line_numbers: Source line numbers in original file
    """
    speaker: str
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    timestamp_marker: Optional[str] = None
    sequence_number: int = 0
    line_numbers: List[int] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    """
    Result of transcript validation.

    Attributes:
        is_valid: Whether transcript is valid
        errors: List of error messages
        warnings: List of warning messages
        stats: Statistics about the transcript
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)


@dataclass
class ParsedTranscript:
    """
    A fully parsed transcript.

    Attributes:
        utterances: List of parsed utterances
        participants: Set of unique speaker names
        duration: Total duration in seconds (if timestamps available)
        source_file: Path to source file
        parse_metadata: Metadata about the parsing process
    """
    utterances: List[Utterance]
    participants: List[str]
    duration: Optional[float] = None
    source_file: Optional[str] = None
    parse_metadata: Dict = field(default_factory=dict)


class GoogleMeetParser:
    """
    Parser for Google Meet transcripts.

    Supports:
    - PDF files (via pdfplumber)
    - TXT files (plain text)
    - Speaker diarization
    - Timestamp extraction
    - Edge case handling

    Format:
        Speaker Name ~: utterance text
        or
        Speaker Name: utterance text

        00:10:47
        Speaker Name ~: utterance at this timestamp
    """

    # Patterns for parsing
    TIMESTAMP_PATTERN = r'^\s*(\d{1,2}):(\d{2}):(\d{2})\s*$'
    SPEAKER_PATTERN = r'^(.+?)\s*~?\s*:\s*(.+)$'
    SPEAKER_ONLY_PATTERN = r'^(.+?)\s*~?\s*:?\s*$'

    def __init__(self):
        """Initialize the parser."""
        self.current_timestamp = None
        self.total_duration = 0.0

    def parse_file(self, file_path: str) -> ParsedTranscript:
        """
        Parse a Google Meet transcript file (PDF or TXT).

        Args:
            file_path: Path to the transcript file

        Returns:
            ParsedTranscript object

        Raises:
            ValueError: If file format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type and extract text
        if path.suffix.lower() == '.pdf':
            text = self._extract_text_from_pdf(file_path)
        elif path.suffix.lower() in ['.txt', '.text']:
            text = self._extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        # Parse the text
        transcript = self.parse_text(text)
        transcript.source_file = file_path

        return transcript

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file using pdfplumber.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                full_text = '\n'.join(text_parts)
                logger.info(f"Extracted {len(full_text)} characters from PDF ({len(pdf.pages)} pages)")
                return full_text

        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}")

    def _extract_text_from_txt(self, file_path: str) -> str:
        """
        Extract text from TXT file.

        Args:
            file_path: Path to TXT file

        Returns:
            File contents
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logger.info(f"Read {len(text)} characters from TXT file")
            return text

        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    logger.info(f"Read text using {encoding} encoding")
                    return text
                except UnicodeDecodeError:
                    continue

            raise ValueError("Could not decode text file with any common encoding")

    def parse_text(self, text: str) -> ParsedTranscript:
        """
        Parse transcript text into structured data.

        Args:
            text: Raw transcript text

        Returns:
            ParsedTranscript object
        """
        lines = text.split('\n')
        utterances = []
        current_speaker = None
        current_text_parts = []
        current_timestamp = None
        sequence_number = 0
        current_line_numbers = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if not line:
                # Empty line - might signal end of utterance
                if current_speaker and current_text_parts:
                    # Save current utterance
                    utterances.append(Utterance(
                        speaker=current_speaker,
                        text=' '.join(current_text_parts),
                        timestamp_marker=current_timestamp,
                        sequence_number=sequence_number,
                        line_numbers=current_line_numbers.copy(),
                    ))
                    sequence_number += 1
                    current_text_parts = []
                    current_line_numbers = []
                continue

            # Check if this is a timestamp line
            timestamp_match = re.match(self.TIMESTAMP_PATTERN, line)
            if timestamp_match:
                # Save any pending utterance
                if current_speaker and current_text_parts:
                    utterances.append(Utterance(
                        speaker=current_speaker,
                        text=' '.join(current_text_parts),
                        timestamp_marker=current_timestamp,
                        sequence_number=sequence_number,
                        line_numbers=current_line_numbers.copy(),
                    ))
                    sequence_number += 1
                    current_text_parts = []
                    current_line_numbers = []

                current_timestamp = line
                continue

            # Check if this is a speaker line
            speaker_match = re.match(self.SPEAKER_PATTERN, line)

            if speaker_match:
                # This is a new speaker utterance
                # Save previous utterance if any
                if current_speaker and current_text_parts:
                    utterances.append(Utterance(
                        speaker=current_speaker,
                        text=' '.join(current_text_parts),
                        timestamp_marker=current_timestamp,
                        sequence_number=sequence_number,
                        line_numbers=current_line_numbers.copy(),
                    ))
                    sequence_number += 1

                # Start new utterance
                current_speaker = speaker_match.group(1).strip()
                text_part = speaker_match.group(2).strip()
                current_text_parts = [text_part] if text_part else []
                current_line_numbers = [line_num]

            elif current_speaker:
                # This is a continuation of the current utterance (multiline)
                current_text_parts.append(line)
                current_line_numbers.append(line_num)

        # Save final utterance if any
        if current_speaker and current_text_parts:
            utterances.append(Utterance(
                speaker=current_speaker,
                text=' '.join(current_text_parts),
                timestamp_marker=current_timestamp,
                sequence_number=sequence_number,
                line_numbers=current_line_numbers,
            ))

        # Calculate timestamps
        utterances = self._calculate_timestamps(utterances)

        # Extract unique participants
        participants = list(set(u.speaker for u in utterances))

        # Calculate duration
        duration = None
        if utterances and utterances[-1].end_time:
            duration = utterances[-1].end_time

        transcript = ParsedTranscript(
            utterances=utterances,
            participants=participants,
            duration=duration,
            parse_metadata={
                'total_lines': len(lines),
                'utterance_count': len(utterances),
                'participant_count': len(participants),
            }
        )

        return transcript

    def _calculate_timestamps(self, utterances: List[Utterance]) -> List[Utterance]:
        """
        Calculate start/end times for each utterance based on timestamp markers.

        Args:
            utterances: List of utterances (possibly with timestamp_marker set)

        Returns:
            Utterances with start_time and end_time calculated
        """
        if not utterances:
            return utterances

        # Track the current timestamp
        current_time = 0.0
        last_timestamp_time = 0.0

        # Count utterances between timestamps to estimate duration
        utterances_since_timestamp = 0
        last_timestamp_index = -1

        for i, utterance in enumerate(utterances):
            if utterance.timestamp_marker:
                # Parse the timestamp
                timestamp_seconds = self._parse_timestamp(utterance.timestamp_marker)

                if timestamp_seconds is not None:
                    # If we have utterances between last timestamp and this one,
                    # distribute time evenly among them
                    if last_timestamp_index >= 0 and utterances_since_timestamp > 0:
                        time_delta = timestamp_seconds - last_timestamp_time
                        time_per_utterance = time_delta / utterances_since_timestamp

                        for j in range(last_timestamp_index + 1, i):
                            start = last_timestamp_time + (j - last_timestamp_index - 1) * time_per_utterance
                            end = start + time_per_utterance
                            utterances[j].start_time = round(start, 2)
                            utterances[j].end_time = round(end, 2)

                    current_time = timestamp_seconds
                    last_timestamp_time = timestamp_seconds
                    last_timestamp_index = i
                    utterances_since_timestamp = 0

                    utterance.start_time = round(current_time, 2)
                    # End time will be set when we see next timestamp or estimate at end

            else:
                utterances_since_timestamp += 1

        # Handle remaining utterances after last timestamp
        if last_timestamp_index >= 0 and utterances_since_timestamp > 0:
            # Estimate 2 seconds per utterance for remaining ones
            estimated_time_per_utterance = 2.0

            for j in range(last_timestamp_index + 1, len(utterances)):
                start = last_timestamp_time + (j - last_timestamp_index) * estimated_time_per_utterance
                end = start + estimated_time_per_utterance
                utterances[j].start_time = round(start, 2)
                utterances[j].end_time = round(end, 2)

        # If no timestamps at all, estimate times
        if last_timestamp_index == -1:
            estimated_time_per_utterance = 3.0  # 3 seconds per utterance
            for i, utterance in enumerate(utterances):
                utterance.start_time = round(i * estimated_time_per_utterance, 2)
                utterance.end_time = round((i + 1) * estimated_time_per_utterance, 2)

        return utterances

    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """
        Parse a timestamp string (HH:MM:SS) into seconds.

        Args:
            timestamp_str: Timestamp string (e.g., "00:10:47")

        Returns:
            Time in seconds, or None if parsing fails
        """
        match = re.match(self.TIMESTAMP_PATTERN, timestamp_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return float(total_seconds)

        return None

    def validate_transcript(self, transcript: ParsedTranscript) -> ValidationResult:
        """
        Validate a parsed transcript for quality and completeness.

        Args:
            transcript: ParsedTranscript to validate

        Returns:
            ValidationResult with errors, warnings, and stats
        """
        errors = []
        warnings = []
        stats = {}

        # Check if we have any utterances
        if not transcript.utterances:
            errors.append("No utterances found in transcript")
            return ValidationResult(is_valid=False, errors=errors)

        # Check for speakers
        if not transcript.participants:
            errors.append("No speakers identified")
        elif len(transcript.participants) == 1:
            warnings.append("Only one speaker detected - may be a monologue")

        # Stats
        stats['total_utterances'] = len(transcript.utterances)
        stats['total_speakers'] = len(transcript.participants)
        stats['has_timestamps'] = any(u.timestamp_marker for u in transcript.utterances)

        # Check for very short utterances
        short_utterances = [u for u in transcript.utterances if len(u.text) < 3]
        if len(short_utterances) > len(transcript.utterances) * 0.2:
            warnings.append(f"{len(short_utterances)} utterances are very short (< 3 chars)")

        # Check for speaker name anomalies
        for speaker in transcript.participants:
            if len(speaker) > 100:
                warnings.append(f"Speaker name is very long: {speaker[:50]}...")
            if speaker.lower() in ['unknown', 'unnamed', 'speaker']:
                warnings.append(f"Generic speaker name detected: {speaker}")

        # Check timestamp coverage
        utterances_with_timestamps = [u for u in transcript.utterances if u.start_time is not None]
        timestamp_coverage = len(utterances_with_timestamps) / len(transcript.utterances)
        stats['timestamp_coverage'] = round(timestamp_coverage * 100, 1)

        if timestamp_coverage < 0.5:
            warnings.append(f"Only {stats['timestamp_coverage']}% of utterances have timestamps")

        # Check for gaps in conversation
        if transcript.duration and transcript.duration > 3600 * 3:  # > 3 hours
            warnings.append(f"Conversation is very long ({transcript.duration / 3600:.1f} hours)")

        # Overall validation
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            stats=stats,
        )

    def get_speaker_statistics(self, transcript: ParsedTranscript) -> Dict[str, Dict]:
        """
        Calculate statistics for each speaker.

        Args:
            transcript: ParsedTranscript

        Returns:
            Dict mapping speaker name to statistics
        """
        speaker_stats = {}

        for speaker in transcript.participants:
            utterances = [u for u in transcript.utterances if u.speaker == speaker]

            total_words = sum(len(u.text.split()) for u in utterances)
            total_chars = sum(len(u.text) for u in utterances)

            # Calculate speaking time if timestamps available
            speaking_time = 0.0
            if all(u.start_time is not None and u.end_time is not None for u in utterances):
                speaking_time = sum(u.end_time - u.start_time for u in utterances)

            speaker_stats[speaker] = {
                'utterance_count': len(utterances),
                'total_words': total_words,
                'total_characters': total_chars,
                'speaking_time_seconds': round(speaking_time, 2),
                'avg_utterance_length': round(total_chars / len(utterances), 1) if utterances else 0,
            }

        return speaker_stats
