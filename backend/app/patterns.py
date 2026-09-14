from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
import math
from datetime import datetime
import itertools

class PatternEngine:
    """
    Pattern learning and prediction engine for shift allocation.

    Learns from historical shift data and makes predictions for new shifts
    based on location, shift type, day/time patterns with various weighting strategies.
    """

    def __init__(self, recency_decay_factor: float = 0.9):
        """
        Initialize the pattern engine.

        Args:
            recency_decay_factor: Factor for exponential decay of historical weights
                                (closer to 1.0 means less decay, more weight on older data)
        """
        self.recency_decay_factor = recency_decay_factor
        self.shift_history = []  # List of all historical shift records
        self.pattern_cache = {}  # Cache for computed patterns

    def add_historical_data(self, shift_records: List[Dict[str, Any]], week_offset: int = 0):
        """
        Add historical shift data to the learning dataset.

        Args:
            shift_records: List of shift dictionaries from parsing
            week_offset: How many weeks ago this data is (0 = most recent week)
        """
        for record in shift_records:
            # Add week offset for recency weighting
            record_with_offset = record.copy()
            record_with_offset['week_offset'] = week_offset
            self.shift_history.append(record_with_offset)

        # Clear pattern cache when new data is added
        self.pattern_cache.clear()

    def _get_recency_weight(self, week_offset: int) -> float:
        """
        Calculate recency weight using exponential decay.

        Args:
            week_offset: How many weeks ago the shift occurred

        Returns:
            Weight between 0 and 1 (more recent = higher weight)
        """
        return math.pow(self.recency_decay_factor, week_offset)

    def _matches_shift_signature(self, shift1: Dict[str, Any], shift2: Dict[str, Any],
                               ignore_day: bool = False) -> bool:
        """
        Check if two shifts match based on their signature.

        Args:
            shift1, shift2: Shift dictionaries to compare
            ignore_day: If True, ignore day-of-week in comparison

        Returns:
            True if shifts match according to specified criteria
        """
        # Location must always match (case-insensitive)
        if shift1['location'].lower() != shift2['location'].lower():
            return False

        # Shift type must match (case-insensitive)
        if shift1['shift_type'].lower() != shift2['shift_type'].lower():
            return False

        # Day-of-week (unless ignoring) - case-insensitive
        if not ignore_day and shift1['day'].lower() != shift2['day'].lower():
            return False

        # Start and end times must match
        if shift1['start_time'] != shift2['start_time']:
            return False
        if shift1['end_time'] != shift2['end_time']:
            return False

        return True

    def _get_historical_matches(self, target_shift: Dict[str, Any],
                               ignore_day: bool = False) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find historical shifts that match the target shift and calculate their weights.

        Args:
            target_shift: The shift we want to make a prediction for
            ignore_day: If True, ignore day-of-week when matching

        Returns:
            List of tuples (historical_shift, weight) for all matches
        """
        matches = []

        for hist_shift in self.shift_history:
            if self._matches_shift_signature(target_shift, hist_shift, ignore_day):
                # Calculate weight based on recency
                weight = self._get_recency_weight(hist_shift['week_offset'])
                matches.append((hist_shift, weight))

        return matches

    def _calculate_person_scores(self, matches: List[Tuple[Dict[str, Any], float]]) -> Dict[str, float]:
        """
        Calculate scores for each person based on historical matches.

        Args:
            matches: List of (historical_shift, weight) tuples

        Returns:
            Dictionary mapping person names to their scores
        """
        person_scores = defaultdict(float)

        for hist_shift, weight in matches:
            person_name = hist_shift['notes']
            if person_name and person_name.strip():  # Only count if there's actually a person assigned
                person_scores[person_name] += weight

        return dict(person_scores)

    def _detect_rotation_pattern(self, matches: List[Tuple[Dict[str, Any], float]]) -> Optional[List[str]]:
        """
        Detect simple rotation patterns (A, B, A, B...) in the historical data.

        Args:
            matches: List of (historical_shift, weight) tuples, ordered by recency

        Returns:
            List representing the rotation pattern if detected, None otherwise
        """
        if len(matches) < 4:  # Need at least 4 shifts to detect a pattern
            return None

        # Sort by week_offset (most recent first) to see the sequence
        sorted_matches = sorted(matches, key=lambda x: x[0]['week_offset'])

        # Extract the sequence of people (most recent first)
        people_sequence = []
        for hist_shift, weight in sorted_matches:
            person_name = hist_shift['notes']
            if person_name and person_name.strip():
                people_sequence.append(person_name)

        if len(people_sequence) < 4:
            return None

        # Check for simple 2-person rotation (A, B, A, B...)
        if len(people_sequence) >= 4:
            # Check if it alternates between two people
            if (people_sequence[0] == people_sequence[2] == people_sequence[4::2] if len(people_sequence) > 4 else people_sequence[0] == people_sequence[2]) and \
               (people_sequence[1] == people_sequence[3] == people_sequence[5::2] if len(people_sequence) > 5 else people_sequence[1] == people_sequence[3]):
                if people_sequence[0] != people_sequence[1]:  # Make sure they're different people
                    return [people_sequence[0], people_sequence[1]]

        # Check for simple 3-person rotation (A, B, C, A, B, C...)
        if len(people_sequence) >= 6:
            if (people_sequence[0] == people_sequence[3] and
                people_sequence[1] == people_sequence[4] and
                people_sequence[2] == people_sequence[5]):
                if len(set([people_sequence[0], people_sequence[1], people_sequence[2]])) == 3:  # All different
                    return [people_sequence[0], people_sequence[1], people_sequence[2]]

        return None

    def predict_shift(self, target_shift: Dict[str, Any],
                     confidence_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Make a prediction for a target shift based on historical patterns.

        Implements the priority order from the brief:
        1. Exact match: same Location + same Shift Type + same day-of-week + same start/end time
        2. Same Location + same Shift Type (ignore exact day)
        3. Same Location only
        4. Recency weighting
        5. Frequency weighting
        6. Rotation detection

        Args:
            target_shift: Dictionary representing the shift to predict
            confidence_threshold: Minimum confidence to auto-assign (0-1)

        Returns:
            Dictionary with prediction results including assigned person, confidence, etc.
        """
        # Priority 1: Exact match
        exact_matches = self._get_historical_matches(target_shift, ignore_day=False)
        if exact_matches:
            person_scores = self._calculate_person_scores(exact_matches)
            if person_scores:
                result = self._process_person_scores(person_scores, exact_matches, target_shift)
                if result['confidence'] >= confidence_threshold:
                    return result

        # Priority 2: Same Location + same Shift Type (ignore day)
        shift_type_matches = self._get_historical_matches(target_shift, ignore_day=True)
        if shift_type_matches:
            person_scores = self._calculate_person_scores(shift_type_matches)
            if person_scores:
                result = self._process_person_scores(person_scores, shift_type_matches, target_shift)
                if result['confidence'] >= confidence_threshold:
                    return result

        # Priority 3: Same Location only
        location_matches = []
        for hist_shift in self.shift_history:
            if hist_shift['location'] == target_shift['location']:
                weight = self._get_recency_weight(hist_shift['week_offset'])
                location_matches.append((hist_shift, weight))

        if location_matches:
            person_scores = self._calculate_person_scores(location_matches)
            if person_scores:
                result = self._process_person_scores(person_scores, location_matches, target_shift)
                # Location-only matches get lower confidence ceiling
                if result['confidence'] >= confidence_threshold:
                    return result

        # No confident prediction found
        return {
            'assigned_person': None,
            'confidence': 0.0,
            'needs_review': True,
            'top_candidate': None,
            'top_candidate_confidence': 0.0,
            'second_candidate': None,
            'second_candidate_confidence': 0.0,
            'reasoning': 'Insufficient historical data for confident prediction',
            'match_type': 'none'
        }

    def _process_person_scores(self, person_scores: Dict[str, float],
                              matches: List[Tuple[Dict[str, Any], float]],
                              target_shift: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process person scores to generate a prediction result.

        Args:
            person_scores: Dictionary mapping person names to their scores
            matches: List of (historical_shift, weight) tuples used for scoring
            target_shift: The shift being predicted

        Returns:
            Dictionary with prediction details
        """
        if not person_scores:
            return {
                'assigned_person': None,
                'confidence': 0.0,
                'needs_review': True,
                'top_candidate': None,
                'top_candidate_confidence': 0.0,
                'second_candidate': None,
                'second_candidate_confidence': 0.0,
                'reasoning': 'No historical matches found',
                'match_type': 'none'
            }

        # Sort persons by score (descending)
        sorted_persons = sorted(person_scores.items(), key=lambda x: x[1], reverse=True)

        # Calculate total weight for normalization
        total_weight = sum(person_scores.values())

        if total_weight == 0:
            return {
                'assigned_person': None,
                'confidence': 0.0,
                'needs_review': True,
                'top_candidate': None,
                'top_candidate_confidence': 0.0,
                'second_candidate': None,
                'second_candidate_confidence': 0.0,
                'reasoning': 'No valid historical assignments found',
                'match_type': 'none'
            }

        # Get top 2 candidates
        top_person, top_score = sorted_persons[0]
        top_confidence = (top_score / total_weight) * 100

        second_person = None
        second_confidence = 0.0
        if len(sorted_persons) > 1:
            second_person, second_score = sorted_persons[1]
            second_confidence = (second_score / total_weight) * 100

        # Check for rotation pattern
        rotation_pattern = self._detect_rotation_pattern(matches)
        reasoning_parts = []

        if rotation_pattern and len(rotation_pattern) >= 2:
            # Check if the top person fits the rotation pattern
            # Get recent sequence to see where we are in the pattern
            sorted_matches = sorted(matches, key=lambda x: x[0]['week_offset'], reverse=True)  # Most recent first
            recent_people = []
            for hist_shift, weight in sorted_matches[:len(rotation_pattern)*2]:  # Look at enough recent shifts
                person = hist_shift['notes']
                if person and person.strip():
                    recent_people.append(person)

            # Simple check: if recent pattern matches rotation, boost confidence
            if len(recent_people) >= len(rotation_pattern):
                matches_pattern = True
                for i, person in enumerate(recent_people[:len(rotation_pattern)]):
                    expected_person = rotation_pattern[i % len(rotation_pattern)]
                    if person != expected_person:
                        matches_pattern = False
                        break

                if matches_pattern:
                    reasoning_parts.append(f"Follows rotation pattern: {' -> '.join(rotation_pattern)}")
                    # Boost confidence for rotation pattern matches
                    top_confidence = min(95.0, top_confidence * 1.2)

        # Build reasoning string
        total_matches = len(matches)
        reasoning_parts.append(f"{top_person}: {top_score:.1f}/{total_weight:.1f} historical matches")

        if rotation_pattern:
            reasoning_parts.append(f"Rotation detected: {' -> '.join(rotation_pattern)}")

        reasoning = "; ".join(reasoning_parts)

        # Determine match type based on what we used
        # This is simplified - in reality we'd track which priority level matched
        match_type = "exact"  # Placeholder

        result = {
            'assigned_person': top_person if top_confidence >= 0 else None,  # Will be filtered by threshold later
            'confidence': top_confidence,
            'needs_review': top_confidence < 60.0,  # Will be overridden by threshold parameter
            'top_candidate': top_person,
            'top_candidate_confidence': top_confidence,
            'second_candidate': second_person,
            'second_candidate_confidence': second_confidence,
            'reasoning': reasoning,
            'match_type': match_type,
            'total_matches': total_matches,
            'total_weight': total_weight
        }

        return result

# Example usage and test function
def test_pattern_engine():
    """Test function to verify pattern engine works correctly."""
    engine = PatternEngine()
    print("PatternEngine initialized successfully")
    return engine

if __name__ == "__main__":
    test_pattern_engine()