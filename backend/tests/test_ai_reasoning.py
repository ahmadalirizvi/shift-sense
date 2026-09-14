"""
Test script for the AI reasoning layer.
Tests both the fallback mode (no API key) and verifies the structure works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from ai_reasoning import AIReasoningEngine, GeminiResponse

def test_ai_reasoning_fallback():
    """Test the AI reasoning engine in fallback mode (no API key)."""
    print("=" * 60)
    print("Testing AI Reasoning Engine (Fallback Mode)")
    print("=" * 60)

    # Initialize engine (will be in fallback mode since no API key is set)
    engine = AIReasoningEngine()
    print(f"AI Available: {engine.is_available()}")

    # Test explanation generation
    shift_details = {
        'location': 'Brize Norton',
        'date': '2026-09-18',
        'day': 'Saturday',
        'shift_type': 'Day',
        'start_time': '08:00:00',
        'end_time': '16:00:00'
    }

    prediction_stats = {
        'top_candidate': 'Ghulam',
        'top_candidate_confidence': 80.0,
        'second_candidate': 'Hamza',
        'second_candidate_confidence': 20.0,
        'total_matches': 5,
        'match_type': 'exact',
        'reasoning': 'Ghulam: 4/5 past Saturday Day shifts at this location'
    }

    explanation = engine.explain_prediction(shift_details, prediction_stats)
    print(f"\nExplanation Test:")
    print(f"  Recommended Name: {explanation.recommended_name}")
    print(f"  Confidence: {explanation.confidence}")
    print(f"  Reasoning: {explanation.reasoning}")

    # Test tie-breaking
    candidates = [
        {
            'name': 'Ghulam',
            'confidence': 45.0,
            'matches': 4,
            'recent_activity': '2 weeks ago',
            'rotation_fit': 'Good'
        },
        {
            'name': 'Hamza',
            'confidence': 40.0,
            'matches': 3,
            'recent_activity': '1 week ago',
            'rotation_fit': 'Good'
        }
    ]

    tie_break_result = engine.tie_break_prediction(shift_details, candidates)
    print(f"\nTie-Break Test:")
    print(f"  Recommended Name: {tie_break_result.recommended_name}")
    print(f"  Confidence: {tie_break_result.confidence}")
    print(f"  Reasoning: {tie_break_result.reasoning}")

    # Test very close tie-break (should recommend human review)
    close_candidates = [
        {
            'name': 'Ghulam',
            'confidence': 51.0,
            'matches': 5,
            'recent_activity': '2 weeks ago',
            'rotation_fit': 'Good'
        },
        {
            'name': 'Hamza',
            'confidence': 49.0,
            'matches': 5,
            'recent_activity': '1 week ago',
            'rotation_fit': 'Good'
        }
    ]

    close_tie_break = engine.tie_break_prediction(shift_details, close_candidates)
    print(f"\nClose Tie-Break Test (should recommend human review):")
    print(f"  Recommended Name: {close_tie_break.recommended_name}")
    print(f"  Confidence: {close_tie_break.confidence}")
    print(f"  Reasoning: {close_tie_break.reasoning}")

    print("\n" + "=" * 60)
    print("AI Reasoning Engine Testing Complete!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    test_ai_reasoning_fallback()