"""
Tests for Google Meet transcript parser.

Run with: pytest tests/test_google_meet_parser.py -v
"""

import pytest
from pathlib import Path

from parsers.google_meet import GoogleMeetParser, Utterance, ParsedTranscript, ValidationResult


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestBasicParsing:
    """Tests for basic transcript parsing."""

    def test_parse_simple_transcript(self):
        """Test parsing of simple transcript with timestamps."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_simple.txt"

        transcript = parser.parse_file(str(transcript_path))

        assert transcript is not None
        assert len(transcript.utterances) > 0
        assert len(transcript.participants) >= 3  # Alice, Bob, Charlie

        # Check participants
        assert "Alice" in transcript.participants
        assert "Bob" in transcript.participants
        assert "Charlie" in transcript.participants

        # Check first utterance
        first_utt = transcript.utterances[0]
        assert first_utt.speaker == "Alice"
        assert "Hello everyone" in first_utt.text
        assert first_utt.sequence_number == 0

    def test_parse_text_directly(self):
        """Test parsing text directly without file."""
        parser = GoogleMeetParser()

        text = """
00:00:00
Alice ~: Hello world
Bob ~: Hi Alice

00:00:30
Charlie ~: Good morning!
"""

        transcript = parser.parse_text(text)

        assert len(transcript.utterances) == 3
        assert transcript.participants == ["Alice", "Bob", "Charlie"] or set(transcript.participants) == {"Alice", "Bob", "Charlie"}

    def test_empty_transcript(self):
        """Test handling of empty transcript."""
        parser = GoogleMeetParser()
        transcript = parser.parse_text("")

        assert len(transcript.utterances) == 0
        assert len(transcript.participants) == 0


class TestMultilineUtterances:
    """Tests for multiline utterance handling."""

    def test_parse_multiline_utterance(self):
        """Test utterances spanning multiple lines."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_multiline.txt"

        transcript = parser.parse_file(str(transcript_path))

        assert len(transcript.utterances) > 0

        # Find Alice's first multiline utterance
        alice_utts = [u for u in transcript.utterances if u.speaker == "Alice"]
        assert len(alice_utts) > 0

        # Check that multiline text is concatenated
        first_alice = alice_utts[0]
        assert "multiple lines" in first_alice.text
        assert "continues here" in first_alice.text

    def test_multiline_preserves_content(self):
        """Test that multiline utterances preserve all content."""
        parser = GoogleMeetParser()

        text = """
Alice ~: This is line one
and line two
and line three

Bob ~: Short response
"""

        transcript = parser.parse_text(text)

        alice_utt = transcript.utterances[0]
        assert "line one" in alice_utt.text
        assert "line two" in alice_utt.text
        assert "line three" in alice_utt.text


class TestSpecialCharacters:
    """Tests for handling special characters in names."""

    def test_parse_special_characters_in_names(self):
        """Test names with unicode, punctuation, etc."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_special_chars.txt"

        transcript = parser.parse_file(str(transcript_path))

        # Check that special character names are parsed
        assert "José García" in transcript.participants
        assert "Mary O'Brien" in transcript.participants
        assert "François Müller" in transcript.participants
        assert "李明" in transcript.participants

    def test_names_with_apostrophes(self):
        """Test names with apostrophes (O'Brien, D'Angelo, etc.)."""
        parser = GoogleMeetParser()

        text = "Mary O'Brien ~: Hello\nJohn D'Angelo ~: Hi"

        transcript = parser.parse_text(text)

        assert "Mary O'Brien" in transcript.participants
        assert "John D'Angelo" in transcript.participants

    def test_names_with_hyphens(self):
        """Test names with hyphens."""
        parser = GoogleMeetParser()

        text = "Jean-Paul Sartre ~: Existence precedes essence"

        transcript = parser.parse_text(text)

        assert "Jean-Paul Sartre" in transcript.participants


class TestTimestampHandling:
    """Tests for timestamp extraction and calculation."""

    def test_parse_timestamps(self):
        """Test timestamp extraction from HH:MM:SS format."""
        parser = GoogleMeetParser()

        # Test timestamp parsing
        assert parser._parse_timestamp("00:00:00") == 0.0
        assert parser._parse_timestamp("00:01:30") == 90.0
        assert parser._parse_timestamp("01:00:00") == 3600.0
        assert parser._parse_timestamp("02:30:45") == 9045.0

    def test_timestamps_assigned_to_utterances(self):
        """Test that timestamps are correctly assigned."""
        parser = GoogleMeetParser()

        text = """
00:00:00
Alice ~: First utterance
Bob ~: Second utterance

00:01:00
Charlie ~: Third utterance
"""

        transcript = parser.parse_text(text)

        # First utterance should have timestamp from 00:00:00
        assert transcript.utterances[0].timestamp_marker == "00:00:00"

        # Third utterance should have timestamp from 00:01:00
        charlie_utt = [u for u in transcript.utterances if u.speaker == "Charlie"][0]
        assert charlie_utt.timestamp_marker == "00:01:00"

    def test_missing_timestamps_estimated(self):
        """Test handling of transcripts without timestamps."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_no_timestamps.txt"

        transcript = parser.parse_file(str(transcript_path))

        # All utterances should have estimated start/end times
        for utt in transcript.utterances:
            assert utt.start_time is not None
            assert utt.end_time is not None
            assert utt.end_time > utt.start_time

    def test_timestamp_calculation_distributes_time(self):
        """Test that time is distributed evenly between timestamp markers."""
        parser = GoogleMeetParser()

        text = """
00:00:00
Alice ~: Utterance 1
Bob ~: Utterance 2

00:01:00
Charlie ~: Utterance 3
"""

        transcript = parser.parse_text(text)

        # Alice should start at 0
        alice = transcript.utterances[0]
        assert alice.start_time == 0.0

        # Bob should be after Alice but before Charlie
        bob = transcript.utterances[1]
        assert bob.start_time is not None
        assert bob.start_time >= 0
        assert bob.start_time < 60

        # Charlie should start at 60
        charlie = transcript.utterances[2]
        assert charlie.start_time == 60.0


class TestSpeakerDiarization:
    """Tests for speaker identification."""

    def test_speaker_with_tilde(self):
        """Test speaker names with tilde suffix."""
        parser = GoogleMeetParser()
        text = "Alice ~: Hello"

        transcript = parser.parse_text(text)

        assert transcript.utterances[0].speaker == "Alice"

    def test_speaker_without_tilde(self):
        """Test speaker names without tilde suffix."""
        parser = GoogleMeetParser()
        text = "Alice: Hello"

        transcript = parser.parse_text(text)

        assert transcript.utterances[0].speaker == "Alice"

    def test_speaker_with_spaces(self):
        """Test speaker names with spaces."""
        parser = GoogleMeetParser()
        text = "Alice Smith ~: Hello"

        transcript = parser.parse_text(text)

        assert transcript.utterances[0].speaker == "Alice Smith"

    def test_multiple_speakers_tracked(self):
        """Test that all unique speakers are identified."""
        parser = GoogleMeetParser()

        text = """
Alice ~: Hello
Bob ~: Hi
Charlie ~: Hey
Alice ~: How are you?
"""

        transcript = parser.parse_text(text)

        assert len(transcript.participants) == 3
        assert set(transcript.participants) == {"Alice", "Bob", "Charlie"}


class TestValidation:
    """Tests for transcript validation."""

    def test_validate_valid_transcript(self):
        """Test validation of a valid transcript."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_simple.txt"

        transcript = parser.parse_file(str(transcript_path))
        validation = parser.validate_transcript(transcript)

        assert validation.is_valid
        assert len(validation.errors) == 0

    def test_validate_empty_transcript(self):
        """Test validation of empty transcript."""
        parser = GoogleMeetParser()
        transcript = parser.parse_text("")

        validation = parser.validate_transcript(transcript)

        assert not validation.is_valid
        assert "No utterances" in validation.errors[0]

    def test_validation_stats(self):
        """Test that validation returns statistics."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_simple.txt"

        transcript = parser.parse_file(str(transcript_path))
        validation = parser.validate_transcript(transcript)

        assert 'total_utterances' in validation.stats
        assert 'total_speakers' in validation.stats
        assert 'has_timestamps' in validation.stats

        assert validation.stats['total_utterances'] > 0
        assert validation.stats['total_speakers'] >= 3

    def test_validation_warns_single_speaker(self):
        """Test validation warns for monologues."""
        parser = GoogleMeetParser()

        text = """
Alice ~: First utterance
Alice ~: Second utterance
Alice ~: Third utterance
"""

        transcript = parser.parse_text(text)
        validation = parser.validate_transcript(transcript)

        # Should be valid but have warning
        assert validation.is_valid
        assert any("one speaker" in w.lower() for w in validation.warnings)


class TestSpeakerStatistics:
    """Tests for speaker statistics calculation."""

    def test_get_speaker_statistics(self):
        """Test speaker statistics calculation."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_simple.txt"

        transcript = parser.parse_file(str(transcript_path))
        stats = parser.get_speaker_statistics(transcript)

        # Should have stats for each speaker
        assert "Alice" in stats
        assert "Bob" in stats
        assert "Charlie" in stats

        # Check stat structure
        alice_stats = stats["Alice"]
        assert 'utterance_count' in alice_stats
        assert 'total_words' in alice_stats
        assert 'total_characters' in alice_stats
        assert 'speaking_time_seconds' in alice_stats

        # Alice should have multiple utterances
        assert alice_stats['utterance_count'] > 0

    def test_speaker_stats_word_count(self):
        """Test word counting in speaker stats."""
        parser = GoogleMeetParser()

        text = """
Alice ~: This is a test
Bob ~: Short
Alice ~: Another longer utterance here
"""

        transcript = parser.parse_text(text)
        stats = parser.get_speaker_statistics(transcript)

        # Alice has 2 utterances with 4 + 4 = 8 words
        assert stats['Alice']['total_words'] == 8

        # Bob has 1 utterance with 1 word
        assert stats['Bob']['total_words'] == 1


class TestEdgeCases:
    """Tests for various edge cases."""

    def test_empty_utterance_text(self):
        """Test handling of utterances with no text."""
        parser = GoogleMeetParser()

        text = """
Alice ~:
Bob ~: Actual text
"""

        transcript = parser.parse_text(text)

        # Alice's utterance should still exist but with empty/minimal text
        assert len(transcript.utterances) >= 1

        # Bob's utterance should be parsed
        bob_utts = [u for u in transcript.utterances if u.speaker == "Bob"]
        assert len(bob_utts) == 1
        assert "Actual text" in bob_utts[0].text

    def test_consecutive_same_speaker(self):
        """Test consecutive utterances from same speaker."""
        parser = GoogleMeetParser()

        text = """
Alice ~: First utterance
Alice ~: Second utterance
Alice ~: Third utterance
"""

        transcript = parser.parse_text(text)

        # Should have 3 separate utterances
        assert len(transcript.utterances) == 3
        assert all(u.speaker == "Alice" for u in transcript.utterances)

    def test_very_long_utterance(self):
        """Test handling of very long utterances."""
        parser = GoogleMeetParser()

        long_text = " ".join(["word"] * 1000)
        text = f"Alice ~: {long_text}"

        transcript = parser.parse_text(text)

        assert len(transcript.utterances) == 1
        assert len(transcript.utterances[0].text) > 1000

    def test_special_characters_in_text(self):
        """Test handling of special characters in utterance text."""
        parser = GoogleMeetParser()

        text = "Alice ~: This has symbols: @#$%^&*()_+-=[]{}|;':\",./<>?"

        transcript = parser.parse_text(text)

        assert len(transcript.utterances) == 1
        assert "@#$%^&*()" in transcript.utterances[0].text


class TestSequenceNumbers:
    """Tests for sequence number assignment."""

    def test_sequence_numbers_incremental(self):
        """Test that sequence numbers are assigned incrementally."""
        parser = GoogleMeetParser()

        text = """
Alice ~: First
Bob ~: Second
Charlie ~: Third
"""

        transcript = parser.parse_text(text)

        assert transcript.utterances[0].sequence_number == 0
        assert transcript.utterances[1].sequence_number == 1
        assert transcript.utterances[2].sequence_number == 2

    def test_sequence_numbers_unique(self):
        """Test that all sequence numbers are unique."""
        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_simple.txt"

        transcript = parser.parse_file(str(transcript_path))

        sequence_numbers = [u.sequence_number for u in transcript.utterances]
        assert len(sequence_numbers) == len(set(sequence_numbers))  # All unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
