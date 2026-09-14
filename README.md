# Shift Sense

An open-source tool that looks at historical shift schedules (Excel files) and learns who usually works which shift, at which location, on which day/time. Given a new, blank week's schedule, it predicts and fills in who should work each shift based on learned patterns.

## Features

- Learns from multiple historical weekly schedule files
- Predicts shift assignments based on location, shift type, day/time patterns
- Detects rotation patterns between employees
- Prevents double-booking across locations
- Provides confidence scores for predictions
- Flags low-confidence assignments for manual review
- Optional AI reasoning layer using Google Gemini for explanations
- Color-coded Excel output (green for confident, yellow for review needed)
- Suggestions sheet with alternative candidates for flagged shifts

## Tech Stack

- Backend: Python (FastAPI, pandas, openpyxl, google-genai)
- Frontend: React (Vite) + Tailwind CSS