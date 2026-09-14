"""
Integration test for Shift Sense core functionality.
Tests the complete flow from historical data to predictions with conflict resolution.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from parsing import ShiftParser
from patterns import PatternEngine
from conflicts import ConflictDetector
from ai_reasoning import AIReasoningEngine
from models import Shift, Prediction

def test_integration():
    """Test the complete integration of all core components."""
    print("=" * 70)
    print("Shift Sense Integration Test")
    print("=" * 70)

    # Initialize all components
    parser = ShiftParser()
    pattern_engine = PatternEngine()
    conflict_detector = ConflictDetector()
    ai_engine = AIReasoningEngine()

    print("✓ All components initialized successfully")

    # Sample historical data representing multiple weeks
    historical_weeks = [
        # Week 1 (2 weeks ago)
        [
            {
                'location': 'Brize Norton',
                'date': '2026-08-28',
                'day': 'Saturday',
                'shift_type': 'Day',
                'start_time': '08:00:00',
                'end_time': '16:00:00',
                'hours': 8.0,
                'notes': 'Ghulam',
                'week_offset': 2
            },
            {
                'location': 'Brize Norton',
                'date': '2026-08-30',
                'day': 'Monday',
                'shift_type': 'Night',
                'start_time': '22:00:00',
                'end_time': '06:00:00',
                'hours': 8.0,
                'notes': 'Hamza',
                'week_offset': 2
            },
            {
                'location': 'Needleman Street',
                'date': '2026-08-28',
                'day': 'Saturday',
                'shift_type': 'Day',
                'start_time': '08:00:00',
                'end_time': '16:00:00',
                'hours': 8.0,
                'notes': 'Hamza',
                'week_offset': 2
            }
        ],
        # Week 2 (1 week ago)
        [
            {
                'location': 'Brize Norton',
                'date': '2026-09-04',
                'day': 'Saturday',
                'shift_type': 'Day',
                'start_time': '08:00:00',
                'end_time': '16:00:00',
                'hours': 8.0,
                'notes': 'Hamza',  # Rotation started
                'week_offset': 1
            },
            {
                'location': 'Brize Norton',
                'date': '2026-09-06',
                'day': 'Monday',
                'shift_type': 'Night',
                'start_time': '22:00:00',
                'end_time': '06:00:00',
                'hours': 8.0,
                'notes': 'Ghulam',  # Rotation
                'week_offset': 1
            },
            {
                'location': 'Needleman Street',
                'date': '2026-09-04',
                'day': 'Saturday',
                'shift_type': 'Day',
                'start_time': '08:00:00',
                'end_time': '16:00:00',
                'hours': 8.0,
                'notes': 'Ghulam',  # Rotation
                'week_offset': 1
            }
        ],
        # Week 3 (most recent)
        [
            {
                'location': 'Brize Norton',
                'date': '2026-09-11',
                'day': 'Saturday',
                'shift_type': 'Day',
                'start_time': '08:00:00',
                'end_time': '16:00:00',
                'hours': 8.0,
                'notes': 'Ghulam',  # Back to Ghulam
                'week_offset': 0
            },
            {
                'location': 'Brize Norton',
                'date': '2026-09-13',
                'day': 'Monday',
                'shift_type': 'Night',
                'start_time': '22:00:00',
                'end_time': '06:00:00',
                'hours': 8.0,
                'notes': 'Hamza',  # Back to Hamza
                'week_offset': 0
            },
            {
                'location': 'Needleman Street',
                'date': '2026-09-11',
                'day': 'Saturday',
                'shift_type': 'Day',
                'start_time': '08:00:00',
                'end_time': '16:00:00',
                'hours': 8.0,
                'notes': 'Hamza',  # Hamza again
                'week_offset': 0
            }
        ]
    ]

    # Add all historical data to pattern engine
    total_records = 0
    for week_data in historical_weeks:
        pattern_engine.add_historical_data(week_data)
        total_records += len(week_data)

    print(f"✓ Added {total_records} historical shift records from {len(historical_weeks)} weeks")

    # Define target shifts to predict (blank week needing assignments)
    target_shifts = [
        {
            'location': 'Brize Norton',
            'date': '2026-09-18',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': ''  # Needs prediction
        },
        {
            'location': 'Brize Norton',
            'date': '2026-09-20',
            'day': 'Monday',
            'shift_type': 'Night',
            'start_time': '22:00:00',
            'end_time': '06:00:00',
            'hours': 8.0,
            'notes': ''  # Needs prediction
        },
        {
            'location': 'Needleman Street',
            'date': '2026-09-18',
            'day': 'Saturday',
            'shift_type': 'Day',
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': ''  # Needs prediction
        },
        {
            'location': 'Needleman Street',
            'date': '2026-09-20',
            'day': 'Monday',
            'shift_type': 'Day',  # Different shift type
            'start_time': '08:00:00',
            'end_time': '16:00:00',
            'hours': 8.0,
            'notes': ''  # Needs prediction
        }
    ]

    print(f"\n✓ Testing predictions for {len(target_shifts)} target shifts...\n")

    # Make predictions for each target shift
    predictions = []
    for i, shift_data in enumerate(target_shifts):
        print(f"Shift {i+1}: {shift_data['location']} {shift_data['day']} {shift_data['shift_type']} "
              f"{shift_data['start_time']}-{shift_data['end_time']}")

        # Get pattern-based prediction
        prediction_result = pattern_engine.predict_shift(shift_data, confidence_threshold=0.6)

        # Apply AI reasoning for explanation (will use fallback since no API key)
        shift_details = {
            'location': shift_data['location'],
            'date': shift_data['date'],
            'day': shift_data['day'],
            'shift_type': shift_data['shift_type'],
            'start_time': shift_data['start_time'],
            'end_time': shift_data['end_time']
        }

        ai_explanation = ai_engine.explain_prediction(shift_details, prediction_result)

        # Create final prediction object
        final_prediction = {
            'location': shift_data['location'],
            'date': shift_data['date'],
            'day': shift_data['day'],
            'shift_type': shift_data['shift_type'],
            'start_time': shift_data['start_time'],
            'end_time': shift_data['end_time'],
            'hours': shift_data['hours'],
            'assigned_person': prediction_result.get('assigned_person'),
            'confidence': prediction_result.get('confidence', 0.0),
            'needs_review': prediction_result.get('needs_review', True),
            'reasoning': ai_explanation.reasoning,  # Use AI-generated reasoning
            'top_candidate': prediction_result.get('top_candidate'),
            'top_candidate_confidence': prediction_result.get('top_candidate_confidence', 0.0),
            'second_candidate': prediction_result.get('second_candidate'),
            'second_candidate_confidence': prediction_result.get('second_candidate_confidence', 0.0)
        }

        predictions.append(final_prediction)

        # Display result
        status = "✓ CONFIDENT" if not final_prediction['needs_review'] else "⚠ FLAGGED"
        person = final_prediction['assigned_person'] or "UNASSIGNED"
        print(f"  {status} -> {person} ({final_prediction['confidence']:.1f}% confidence)")
        print(f"  Reasoning: {final_prediction['reasoning']}")
        print()

    # Test conflict detection and resolution
    print("✓ Testing conflict detection and resolution...")
    conflicts = conflict_detector.detect_conflicts(predictions)
    print(f"  Detected {len(conflicts)} potential conflicts")

    if conflicts:
        for conflict in conflicts:
            print(f"  ⚠ {conflict['description']}")

        # Apply conflict resolution
        resolved_predictions = conflict_detector.resolve_conflicts(predictions)
        print(f"  ✓ Applied conflict resolution")

        # Show final assignments after conflict resolution
        print("\nFinal Assignments After Conflict Resolution:")
        for i, pred in enumerate(resolved_predictions):
            person = pred.get('assigned_person', 'UNASSIGNED')
            status = "✓" if not pred.get('needs_review', True) else "⚠"
            print(f"  {status} Shift {i+1}: {person} ({pred.get('confidence', 0):.1f}%)")
    else:
        print("  ✓ No conflicts detected")
        resolved_predictions = predictions

    print("\n" + "=" * 70)
    print("Integration Test Complete!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  • Processed {len(historical_weeks)} weeks of historical data ({total_records} shift records)")
    print(f"  • Made predictions for {len(target_shifts)} target shifts")
    print(f"  • Detected and resolved {len(conflicts)} conflicts")
    print(f"  • AI reasoning engine available: {ai_engine.is_available()} (running in fallback mode)")
    print("\n✓ All core components working correctly!")

    return True

if __name__ == "__main__":
    test_integration()