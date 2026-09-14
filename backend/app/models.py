"""
Data models for Shift Sense
Defines the data classes used throughout the application.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class Shift:
    """Represents a single shift record."""
    location: str
    date: str  # YYYY-MM-DD format
    day: str   # Monday, Tuesday, etc.
    shift_type: str  # Day, Night, etc.
    start_time: str  # HH:MM:SS format
    end_time: str    # HH:MM:SS format
    hours: float
    notes: str = ""  # Person's name or empty for unassigned
    week_offset: int = 0  # For historical weighting (0 = most recent)

    def __post_init__(self):
        """Validate shift data after initialization."""
        if not self.location:
            raise ValueError("Location cannot be empty")
        if not self.date:
            raise ValueError("Date cannot be empty")
        if not self.shift_type:
            raise ValueError("Shift type cannot be empty")

@dataclass
class Prediction:
    """Represents a prediction for a shift."""
    shift: Shift
    assigned_person: Optional[str] = None
    confidence: float = 0.0  # 0-100 percentage
    needs_review: bool = False

    # For debugging and transparency
    top_candidate: Optional[str] = None
    top_candidate_confidence: float = 0.0
    second_candidate: Optional[str] = None
    second_candidate_confidence: float = 0.0
    reasoning: str = ""
    match_type: str = "none"  # exact, shift_type, location_only, none
    total_matches: int = 0
    total_weight: float = 0.0

@dataclass
class Conflict:
    """Represents a scheduling conflict."""
    person: str
    shift1: Shift
    shift2: Shift
    conflict_type: str = "double_booking"
    description: str = ""

@dataclass
class Suggestion:
    """Represents a suggested alternative for a flagged shift."""
    location: str
    date: str
    day: str
    shift_type: str
    start_time: str
    end_time: str
    top_candidate: str
    top_candidate_confidence: float
    second_candidate: Optional[str] = None
    second_candidate_confidence: float = 0.0
    reasoning: str = ""

# Example usage and test function
def test_models():
    """Test function to verify data models work correctly."""
    print("Testing Shift Sense Data Models...")

    # Test Shift model
    shift = Shift(
        location="Brize Norton",
        date="2026-09-18",
        day="Saturday",
        shift_type="Day",
        start_time="08:00:00",
        end_time="16:00:00",
        hours=8.0,
        notes="Ghulam"
    )
    print(f"✓ Shift model: {shift.location} {shift.date} {shift.shift_type}")

    # Test Prediction model
    prediction = Prediction(
        shift=shift,
        assigned_person="Ghulam",
        confidence=85.0,
        needs_review=False,
        top_candidate="Ghulam",
        top_candidate_confidence=85.0,
        second_candidate="Hamza",
        second_candidate_confidence=15.0,
        reasoning="Ghulam: 6/8 past Saturday Day shifts",
        match_type="exact",
        total_matches=8,
        total_weight=7.2
    )
    print(f"✓ Prediction model: {prediction.assigned_person} ({prediction.confidence}%)")

    # Test Conflict model
    shift2 = Shift(
        location="Needleman Street",
        date="2026-09-18",
        day="Saturday",
        shift_type="Day",
        start_time="10:00:00",
        end_time="18:00:00",
        hours=8.0,
        notes="Ghulam"
    )
    conflict = Conflict(
        person="Ghulam",
        shift1=shift,
        shift2=shift2,
        description="Ghulam is scheduled for overlapping shifts"
    )
    print(f"✓ Conflict model: {conflict.person} conflict between {conflict.shift1.location} and {conflict.shift2.location}")

    # Test Suggestion model
    suggestion = Suggestion(
        location="Brize Norton",
        date="2026-09-18",
        day="Saturday",
        shift_type="Day",
        start_time="08:00:00",
        end_time="16:00:00",
        top_candidate="Ghulam",
        top_candidate_confidence=75.0,
        second_candidate="Hamza",
        second_candidate_confidence=25.0,
        reasoning="Ghulam: 6/8 past shifts, Hamza: 2/8 past shifts"
    )
    print(f"✓ Suggestion model: {suggestion.top_candidate} ({suggestion.top_candidate_confidence}%)")

    print("All data models tested successfully!")

if __name__ == "__main__":
    test_models()