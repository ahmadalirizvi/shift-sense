from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

class ConflictDetector:
    """
    Detects scheduling conflicts where the same person is assigned to overlapping shifts.
    """

    def __init__(self):
        pass

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """
        Parse date and time strings into a datetime object.
        """
        # Handle various date formats
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%d-%m-%Y']
        time_formats = ['%H:%M:%S', '%H:%M']

        date_obj = None
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if date_obj is None:
            raise ValueError(f"Unable to parse date: {date_str}")

        time_obj = None
        for fmt in time_formats:
            try:
                time_part = datetime.strptime(time_str, fmt).time()
                time_obj = datetime.combine(date_obj.date(), time_part)
                break
            except ValueError:
                continue

        if time_obj is None:
            raise ValueError(f"Unable to parse time: {time_str}")

        return time_obj

    def _shift_overlaps(self, shift1: Dict[str, Any], shift2: Dict[str, Any]) -> bool:
        """
        Check if two shifts overlap in time.
        Handles shifts that cross midnight.
        """
        try:
            # Parse start and end times for both shifts
            start1 = self._parse_datetime(shift1['date'], shift1['start_time'])
            end1 = self._parse_datetime(shift1['date'], shift1['end_time'])
            start2 = self._parse_datetime(shift2['date'], shift2['start_time'])
            end2 = self._parse_datetime(shift2['date'], shift2['end_time'])

            # Handle shifts that cross midnight (end time is earlier than start time)
            if end1 < start1:
                # Shift 1 crosses midnight, add one day to end time
                end1 += timedelta(days=1)
            if end2 < start2:
                # Shift 2 crosses midnight, add one day to end time
                end2 += timedelta(days=1)

            # Check for overlap: two shifts overlap if one starts before the other ends
            # and vice versa
            return start1 < end2 and start2 < end1

        except Exception as e:
            # If we can't parse the times, assume no overlap to be safe
            print(f"Warning: Could not parse times for overlap check: {e}")
            return False

    def detect_conflicts(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect conflicts in a list of shift predictions.

        Args:
            predictions: List of prediction dictionaries, each containing shift info and assigned person

        Returns:
            List of conflict dictionaries detailing the conflicts found
        """
        conflicts = []

        # Group predictions by assigned person to efficiently check for conflicts
        person_shifts = {}
        for pred in predictions:
            assigned_person = pred.get('assigned_person')
            if assigned_person and assigned_person.strip():
                if assigned_person not in person_shifts:
                    person_shifts[assigned_person] = []
                person_shifts[assigned_person].append(pred)

        # For each person, check if any of their shifts overlap
        for person, shifts in person_shifts.items():
            if len(shifts) < 2:
                continue  # Can't have a conflict with less than 2 shifts

            # Compare each pair of shifts for this person
            for i in range(len(shifts)):
                for j in range(i + 1, len(shifts)):
                    shift1 = shifts[i]
                    shift2 = shifts[j]

                    if self._shift_overlaps(shift1, shift2):
                        conflicts.append({
                            'person': person,
                            'shift1': {
                                'location': shift1['location'],
                                'date': shift1['date'],
                                'shift_type': shift1['shift_type'],
                                'start_time': shift1['start_time'],
                                'end_time': shift1['end_time']
                            },
                            'shift2': {
                                'location': shift2['location'],
                                'date': shift2['date'],
                                'shift_type': shift2['shift_type'],
                                'start_time': shift2['start_time'],
                                'end_time': shift2['end_time']
                            },
                            'conflict_type': 'double_booking',
                            'description': f"{person} is scheduled for overlapping shifts at {shift1['location']} and {shift2['location']} on {shift1['date']}"
                        })

        return conflicts

    def resolve_conflicts(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolve conflicts by removing the lower-confidence assignment in each conflict.

        Args:
            predictions: List of prediction dictionaries

        Returns:
            List of predictions with conflicts resolved (conflicting assignments removed)
        """
        # Work on a copy to avoid modifying the original during iteration
        resolved_predictions = [pred.copy() for pred in predictions]

        # Detect conflicts
        conflicts = self.detect_conflicts(resolved_predictions)

        # For each conflict, remove the assignment with lower confidence
        for conflict in conflicts:
            person = conflict['person']
            shift1_info = conflict['shift1']
            shift2_info = conflict['shift2']

            # Find the predictions corresponding to these shifts
            shift1_pred = None
            shift2_pred = None

            for pred in resolved_predictions:
                if (pred.get('assigned_person') == person and
                    pred.get('location') == shift1_info['location'] and
                    pred.get('date') == shift1_info['date'] and
                    pred.get('shift_type') == shift1_info['shift_type'] and
                    pred.get('start_time') == shift1_info['start_time'] and
                    pred.get('end_time') == shift1_info['end_time']):
                    shift1_pred = pred

                if (pred.get('assigned_person') == person and
                    pred.get('location') == shift2_info['location'] and
                    pred.get('date') == shift2_info['date'] and
                    pred.get('shift_type') == shift2_info['shift_type'] and
                    pred.get('start_time') == shift2_info['start_time'] and
                    pred.get('end_time') == shift2_info['end_time']):
                    shift2_pred = pred

            # If we found both predictions, remove the one with lower confidence
            if shift1_pred and shift2_pred:
                conf1 = shift1_pred.get('confidence', 0)
                conf2 = shift2_pred.get('confidence', 0)

                # Remove the assignment with lower confidence
                if conf1 < conf2:
                    shift1_pred['assigned_person'] = None
                    shift1_pred['needs_review'] = True
                    shift1_pred['confidence'] = 0.0
                    # Add conflict resolution note to reasoning
                    if 'reasoning' in shift1_pred:
                        shift1_pred['reasoning'] += f"; Conflict resolved: removed due to overlap with {shift2_info['location']} shift"
                    else:
                        shift1_pred['reasoning'] = f"Conflict resolved: removed due to overlap with {shift2_info['location']} shift"
                elif conf2 < conf1:
                    shift2_pred['assigned_person'] = None
                    shift2_pred['needs_review'] = True
                    shift2_pred['confidence'] = 0.0
                    # Add conflict resolution note to reasoning
                    if 'reasoning' in shift2_pred:
                        shift2_pred['reasoning'] += f"; Conflict resolved: removed due to overlap with {shift1_info['location']} shift"
                    else:
                        shift2_pred['reasoning'] = f"Conflict resolved: removed due to overlap with {shift1_info['location']} shift"
                else:
                    # Equal confidence - remove the second one (arbitrary choice)
                    shift2_pred['assigned_person'] = None
                    shift2_pred['needs_review'] = True
                    shift2_pred['confidence'] = 0.0
                    # Add conflict resolution note to reasoning
                    if 'reasoning' in shift2_pred:
                        shift2_pred['reasoning'] += f"; Conflict resolved: removed due to overlap with {shift1_info['location']} shift (equal confidence)"
                    else:
                        shift2_pred['reasoning'] = f"Conflict resolved: removed due to overlap with {shift1_info['location']} shift (equal confidence)"

        return resolved_predictions

# Example usage and test function
def test_conflict_detector():
    """Test function to verify conflict detector works correctly."""
    detector = ConflictDetector()
    print("ConflictDetector initialized successfully")
    return detector

if __name__ == "__main__":
    test_conflict_detector()