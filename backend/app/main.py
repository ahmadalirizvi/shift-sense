from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import uuid
from pathlib import Path

from .parsing import ShiftParser
from .patterns import PatternEngine
from .conflicts import ConflictDetector
from .ai_reasoning import AIReasoningEngine
from .models import Shift, Prediction

app = FastAPI(title="Shift Sense API", description="AI-Powered Shift Allocation System", openapi_version="3.0.3")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
        "http://127.0.0.1:3000"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (in production, you'd want to use dependency injection or a proper state manager)
parser = ShiftParser()
pattern_engine = PatternEngine()
conflict_detector = ConflictDetector()
ai_engine = AIReasoningEngine()

# Directory for storing uploaded files and generated outputs
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Welcome to Shift Sense API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload-historical")
async def upload_historical_files(files: List[UploadFile] = File(...)):
    """
    Upload one or more historical week Excel files to add to the learning dataset.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    total_records = 0
    processed_files = []

    for file in files:
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not an Excel file")

        # Generate unique filename to avoid conflicts
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

        try:
            # Save uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Parse the Excel file
            shift_records = parser.parse_excel_file(str(file_path))

            # Add to pattern engine's learning dataset
            # We'll use week_offset based on order of upload (most recent = 0)
            # In a real system, you might extract dates from filenames or file content
            week_offset = len(processed_files)  # Simple approach: each file is one week older
            pattern_engine.add_historical_data(shift_records, week_offset)

            total_records += len(shift_records)
            processed_files.append({
                "filename": file.filename,
                "records_count": len(shift_records),
                "week_offset": week_offset
            })

        except Exception as e:
            # Clean up on error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
        finally:
            file.file.close()

    return {
        "message": f"Successfully processed {len(processed_files)} historical files",
        "total_records_added": total_records,
        "files": processed_files
    }

@app.post("/predict")
async def predict_shifts(file: UploadFile = File(...)):
    """
    Upload a blank week Excel file and get back predictions.
    Returns the predictions as JSON for immediate display,
    and also generates a downloadable Excel file.
    """
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="File must be an Excel file")

    # Generate unique filename
    file_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    output_filename = f"predictions_{file_id}_{file.filename}"
    output_path = OUTPUT_DIR / output_filename

    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse the blank week file
        blank_shift_records = parser.parse_excel_file(str(input_path))

        if not blank_shift_records:
            raise HTTPException(status_code=400, detail="No valid shift records found in the file")

        # Make predictions for each blank shift
        predictions = []
        debug_info = {
            "total_historical_records": len(pattern_engine.shift_history),
            "predictions_debug": []
        }

        for shift_data in blank_shift_records:
            # Get pattern-based prediction with debug info
            prediction_result = pattern_engine.predict_shift(shift_data, confidence_threshold=0.6)

            # Add debug information about historical matches considered
            shift_details = {
                'location': shift_data['location'],
                'date': shift_data['date'],
                'day': shift_data['day'],
                'shift_type': shift_data['shift_type'],
                'start_time': shift_data['start_time'],
                'end_time': shift_data['end_time']
            }

            # Get match counts for each priority level
            exact_matches = pattern_engine._get_historical_matches(shift_data, ignore_day=False)
            shift_type_matches = pattern_engine._get_historical_matches(shift_data, ignore_day=True)
            location_matches = []
            for hist_shift in pattern_engine.shift_history:
                if hist_shift['location'] == shift_data['location']:
                    weight = pattern_engine._get_recency_weight(hist_shift['week_offset'])
                    location_matches.append((hist_shift, weight))

            debug_info["predictions_debug"].append({
                "shift": f"{shift_data['location']} {shift_data['shift_type']} {shift_data['day']} {shift_data['start_time']}-{shift_data['end_time']}",
                "exact_matches_count": len(exact_matches),
                "shift_type_matches_count": len(shift_type_matches),
                "location_matches_count": len(location_matches),
                "selected_match_type": prediction_result.get('match_type', 'unknown')
            })

            # Apply AI reasoning for explanation
            ai_explanation = ai_engine.explain_prediction(shift_details, prediction_result)

            # Create final prediction
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
                'reasoning': ai_explanation.reasoning,
                'top_candidate': prediction_result.get('top_candidate'),
                'top_candidate_confidence': prediction_result.get('top_candidate_confidence', 0.0),
                'second_candidate': prediction_result.get('second_candidate'),
                'second_candidate_confidence': prediction_result.get('second_candidate_confidence', 0.0)
            }

            predictions.append(final_prediction)

        # Detect and resolve conflicts
        conflicts = conflict_detector.detect_conflicts(predictions)
        if conflicts:
            predictions = conflict_detector.resolve_conflicts(predictions)

        # Generate output Excel file
        parser.create_output_excel(predictions, str(output_path))

        # Prepare response
        confident_count = sum(1 for p in predictions if not p['needs_review'])
        flagged_count = sum(1 for p in predictions if p['needs_review'])

        return {
            "message": "Predictions generated successfully",
            "input_filename": file.filename,
            "predictions": predictions,
            "debug_info": debug_info,
            "summary": {
                "total_shifts": len(predictions),
                "confident_predictions": confident_count,
                "flagged_for_review": flagged_count,
                "conflicts_resolved": len(conflicts)
            },
            "download_url": f"/download/{output_filename}"
        }

    except Exception as e:
        # Clean up on error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")
    finally:
        file.file.close()

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a generated Excel file with predictions.
    """
    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Invalid file type")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.get("/history")
async def get_history():
    """
    Get information about the historical data currently in the learning dataset.
    """
    total_shifts = len(pattern_engine.shift_history)
    # Group by week offset to show how many weeks of data we have
    week_counts = {}
    for shift in pattern_engine.shift_history:
        week_offset = shift.get('week_offset', 0)
        week_counts[week_offset] = week_counts.get(week_offset, 0) + 1

    return {
        "total_historical_shifts": total_shifts,
        "weeks_of_data": len(week_counts),
        "week_breakdown": [{"week_offset": k, "shift_count": v} for k, v in sorted(week_counts.items())],
        "ai_reasoning_available": ai_engine.is_available()
    }