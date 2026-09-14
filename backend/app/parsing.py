import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import os

class ShiftParser:
    """Handles parsing of Excel shift schedule files."""

    def __init__(self):
        self.shift_records = []

    def parse_excel_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse an Excel file with multiple sheets (one per location).

        Expected columns: Date, Day, Shift Type, Start Time, End Time, Location, Hours, Notes
        Notes column contains person's name in historical files, blank in "to be filled" files.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read all sheets from the Excel file
        excel_data = pd.read_excel(file_path, sheet_name=None)

        all_records = []

        for sheet_name, df in excel_data.items():
            # Skip empty sheets
            if df.empty:
                continue

            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()

            # Ensure required columns exist
            required_columns = ['Date', 'Day', 'Shift Type', 'Start Time', 'End Time', 'Location', 'Hours', 'Notes']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in sheet '{sheet_name}': {missing_columns}")

            # Process each row
            for _, row in df.iterrows():
                # Skip completely empty rows
                if pd.isna(row['Date']) and pd.isna(row['Notes']):
                    continue

                record = {
                    'location': str(row['Location']).strip() if not pd.isna(row['Location']) else '',
                    'date': self._parse_date(row['Date']),
                    'day': str(row['Day']).strip() if not pd.isna(row['Day']) else '',
                    'shift_type': str(row['Shift Type']).strip() if not pd.isna(row['Shift Type']) else '',
                    'start_time': self._parse_time(row['Start Time']),
                    'end_time': self._parse_time(row['End Time']),
                    'hours': float(row['Hours']) if not pd.isna(row['Hours']) else 0.0,
                    'notes': str(row['Notes']).strip() if not pd.isna(row['Notes']) else '',
                    'sheet_name': sheet_name  # Keep track of which location sheet this came from
                }

                # Only add records that have essential shift information
                if record['date'] and record['shift_type'] and record['location']:
                    all_records.append(record)

        return all_records

    def _parse_date(self, date_value) -> str:
        """Parse date value to ISO format string (YYYY-MM-DD)."""
        if pd.isna(date_value):
            return None

        if isinstance(date_value, str):
            # Try parsing common date formats
            # Try DD/MM/YYYY format first to avoid US-centric bias for ambiguous dates
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(date_value, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            # If none worked, return as-is (but this might cause issues later)
            return date_value
        elif isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        else:
            # Handle pandas Timestamp or other date types
            try:
                return pd.to_datetime(date_value).strftime('%Y-%m-%d')
            except:
                return str(date_value)

    def _parse_time(self, time_value) -> str:
        """Parse time value to ISO format string (HH:MM:SS)."""
        if pd.isna(time_value):
            return None

        if isinstance(time_value, str):
            # Try parsing common time formats
            for fmt in ['%H:%M:%S', '%H:%M', '%I:%M:%S %p', '%I:%M %p']:
                try:
                    return datetime.strptime(time_value, fmt).strftime('%H:%M:%S')
                except ValueError:
                    continue
            # If none worked, return as-is
            return time_value
        elif isinstance(time_value, datetime):
            return time_value.strftime('%H:%M:%S')
        else:
            # Handle pandas Timestamp or other time types
            try:
                return pd.to_datetime(time_value).strftime('%H:%M:%S')
            except:
                return str(time_value)

    def create_output_excel(self, predictions: List[Dict[str, Any]], output_path: str):
        """
        Create an Excel output file with predictions.
        - Notes column filled for confident predictions (highlighted green)
        - Notes left blank for flagged shifts (highlighted yellow)
        - Extra sheet 'Suggestions' with flagged shifts and candidate suggestions
        """
        # Group predictions by location/sheet
        sheets_data = {}

        for pred in predictions:
            location = pred['location']
            if location not in sheets_data:
                sheets_data[location] = []
            sheets_data[location].append(pred)

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write each location sheet
            for location, records in sheets_data.items():
                # Convert to DataFrame
                df_data = []
                for record in records:
                    df_data.append({
                        'Date': record['date'],
                        'Day': record['day'],
                        'Shift Type': record['shift_type'],
                        'Start Time': record['start_time'],
                        'End Time': record['end_time'],
                        'Location': record['location'],
                        'Hours': record['hours'],
                        'Notes': record.get('assigned_person', '')  # This will be filled by prediction engine
                    })

                df = pd.DataFrame(df_data)
                df.to_excel(writer, sheet_name=location, index=False)

            # Create Suggestions sheet for flagged shifts
            flagged_shifts = [p for p in predictions if p.get('needs_review', False)]
            if flagged_shifts:
                suggestions_data = []
                for pred in flagged_shifts:
                    suggestions_data.append({
                        'Location': pred['location'],
                        'Date': pred['date'],
                        'Day': pred['day'],
                        'Shift Type': pred['shift_type'],
                        'Start Time': pred['start_time'],
                        'End Time': pred['end_time'],
                        'Top Candidate': pred.get('top_candidate', ''),
                        'Top Candidate Confidence': f"{pred.get('top_candidate_confidence', 0)}%",
                        'Second Candidate': pred.get('second_candidate', ''),
                        'Second Candidate Confidence': f"{pred.get('second_candidate_confidence', 0)}%",
                        'Reasoning': pred.get('reasoning', '')
                    })

                if suggestions_data:
                    suggestions_df = pd.DataFrame(suggestions_data)
                    suggestions_df.to_excel(writer, sheet_name='Suggestions', index=False)

        # TODO: Add actual cell coloring using openpyxl styling
        # For now, we'll leave this as a TODO since the user wanted to validate core logic first
        print(f"Output Excel file created: {output_path}")
        print("Note: Cell coloring and advanced formatting to be implemented in later steps")


# Example usage and test function
def test_parser():
    """Test function to verify parser works correctly."""
    parser = ShiftParser()
    print("ShiftParser initialized successfully")
    return parser

if __name__ == "__main__":
    test_parser()