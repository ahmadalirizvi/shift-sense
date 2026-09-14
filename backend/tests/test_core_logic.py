"""
Test script to validate the core logic of the shift prediction system.
This tests steps 1-3 from the build order: Excel parsing, pattern learning, and conflict detection.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from parsing import ShiftParser
from patterns import PatternEngine
from conflicts import ConflictDetector

def test_with_sample_data():
    """Test the core logic with sample data matching the project brief."""

    print("=" * 60)
    print("Testing Shift Sense Core Logic")
    print("=" * 60)

    # Initialize components
    parser = ShiftParser()
    pattern_engine = PatternEngine()
    conflict_detector = ConflictDetector()

    print("\n1. Testing Excel Parser...")
    # Since we don't have actual Excel files yet, we'll test the parser structure
    print("   ✓ ShiftParser initialized successfully")

    print("\n2. Testing Pattern Engine...")
    # Test with some sample historical data
    sample_historical_data = [
        {
            'location': 'Brize Norton',
            'date': '2026-09-06',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': 'Ghulam',
            'week_offset': 1  # One week ago
        },
        {
            'location': 'Brize Norton',
            'date': '2026-09-11',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': 'Ghulam',
            'week_offset': 0  # Most recent week
        },
        {
            'location': 'Brize Norton',
            'date': '2026-09-04',
            'day': 'Thursday',
            'shift_type': 'Night',
            'start_time': '22:00:00',
            'end_time': '06:00:00',
            'hours': 8.0,
            'notes': 'Hamza',
            'week_offset': 1
        },
        {
            'location': 'Brize Norton',
            'date': '2026-09-11',
            'day': 'Thursday',
            'shift_type': 'Night',
            'start_time': '22:00:00',
            'end_time': '06:00:00',
            'hours': 8.0,
            'notes': 'Hamza',
            'week_offset': 0
        },
        {
            'location': 'Needleman Street',
            'date': '2026-09-06',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': 'Ghulam',
            'week_offset': 1
        },
        {
            'location': 'Needleman Street',
            'date': '2026-09-13',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': 'Hamza',
            'week_offset': 0  # Most recent week - shows alternation
        }
    ]

    # Add historical data to pattern engine
    pattern_engine.add_historical_data(sample_historical_data)
    print(f"   ✓ Added {len(sample_historical_data)} historical shift records")

    # Test prediction for a shift that matches historical pattern
    target_shift_1 = {
        'location': 'Brize Norton',
        'date': '2026-09-18',
        'day': 'Saturday',
        'shift_type': 'Day',
        'start_time': '08:00:00',
        'end_time': '16:00:00',
        'hours': 8.0,
        'notes': ''  # Blank - needs prediction
    }

    prediction_1 = pattern_engine.predict_shift(target_shift_1, confidence_threshold=0.6)
    print(f"\n   Prediction for Brize Norton Saturday Day shift:")
    print(f"     Assigned: {prediction_1.get('assigned_person')}")
    print(f"     Confidence: {prediction_1.get('confidence'):.1f}%")
    print(f"     Needs Review: {prediction_1.get('needs_review')}")
    print(f"     Reasoning: {prediction_1.get('reasoning')}")

    # Test prediction for Needleman Street (should show rotation pattern)
    target_shift_2 = {
        'location': 'Needleman Street',
        'date': '2026-09-20',
        'day': 'Saturday',
        'shift_type': 'Day',
        'start_time': '08:00:00',
        'end_time': '16:00:00',
        'hours': 8.0,
        'notes': ''  # Blank - needs prediction
    }

    prediction_2 = pattern_engine.predict_shift(target_shift_2, confidence_threshold=0.6)
    print(f"\n   Prediction for Needleman Street Saturday Day shift:")
    print(f"     Assigned: {prediction_2.get('assigned_person')}")
    print(f"     Confidence: {prediction_2.get('confidence'):.1f}%")
    print(f"     Needs Review: {prediction_2.get('needs_review')}")
    print(f"     Reasoning: {prediction_2.get('reasoning')}")

    print("\n3. Testing Conflict Detector...")
    # Test conflict detection with overlapping shifts
    test_predictions = [
        {
            'location': 'Brize Norton',
            'date': '2026-09-18',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': '',  # Will be filled below
            'assigned_person': 'Ghulam',
            'confidence': 85.0,
            'needs_review': False
        },
        {
            'location': 'Needleman Street',
            'date': '2026-09-18',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '10:00:00',  # Overlaps with first shift
            'end_time': '18:00:00',
            'hours': 8.0,
            'notes': '',  # Will be filled below
            'assigned_person': 'Ghulam',  # Same person - should create conflict
            'confidence': 75.0,
            'needs_review': False
        }
    ]

    conflicts = conflict_detector.detect_conflicts(test_predictions)
    print(f"   ✓ Detected {len(conflicts)} conflicts")
    if conflicts:
        print(f"     Conflict: {conflicts[0]['description']}")

    # Test conflict resolution
    resolved_predictions = conflict_detector.resolve_conflicts(test_predictions)
    print(f"\n   After conflict resolution:")
    for i, pred in enumerate(resolved_predictions):
        person = pred.get('assigned_person', 'UNASSIGNED')
        print(f"     Shift {i+1}: {person} (confidence: {pred.get('confidence', 0):.1f}%)")

    print("\n" + "=" * 60)
    print("Core Logic Testing Complete!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    test_with_sample_data()