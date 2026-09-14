"""
AI Reasoning Layer for Shift Sense
Handles optional Gemini API integration for explaining predictions and tie-breaking.
Designed to gracefully degrade when no API key is available.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Try to import Google Gemini AI, but make it optional
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None

@dataclass
class GeminiResponse:
    """Structured response from Gemini API"""
    recommended_name: Optional[str]
    confidence: int  # 0-100
    reasoning: str

class AIReasoningEngine:
    """
    Handles AI-powered reasoning for shift predictions.
    Uses Google Gemini API when available, falls back to rule-based reasoning.
    """

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Gemini client if API key is available."""
        if not GEMINI_AVAILABLE:
            print("Warning: Google Gemini AI not available. Install google-genai package.")
            return

        if not self.api_key:
            print("Info: GEMINI_API_KEY not set. AI reasoning layer will operate in fallback mode.")
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            print(f"Info: Gemini AI reasoning engine initialized with model {self.model_name}")
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini client: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if AI reasoning is available (API key set and client initialized)."""
        return self.client is not None

    def explain_prediction(self, shift_details: Dict[str, Any],
                          prediction_stats: Dict[str, Any]) -> GeminiResponse:
        """
        Generate a natural language explanation for a prediction.

        Args:
            shift_details: Information about the shift being predicted
            prediction_stats: Statistics from the pattern engine (candidate names, counts, etc.)

        Returns:
            GeminiResponse with reasoning and optional adjusted recommendation
        """
        if not self.is_available():
            return self._fallback_explain_prediction(shift_details, prediction_stats)

        try:
            # Prepare the prompt for Gemini
            prompt = self._build_explanation_prompt(shift_details, prediction_stats)

            # Call Gemini API with structured output
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiResponse,
                )
            )

            # Parse the structured response
            gemini_response = response.parsed
            if isinstance(gemini_response, GeminiResponse):
                return gemini_response
            else:
                # Fallback if response parsing failed
                return self._fallback_explain_prediction(shift_details, prediction_stats)

        except Exception as e:
            print(f"Warning: Gemini API call failed: {e}")
            return self._fallback_explain_prediction(shift_details, prediction_stats)

    def tie_break_prediction(self, shift_details: Dict[str, Any],
                           candidates: List[Dict[str, Any]],
                           constraints: Optional[List[Dict[str, Any]]] = None) -> GeminiResponse:
        """
        Use AI for tie-breaking when top candidates are close in confidence.

        Args:
            shift_details: Information about the shift being predicted
            candidates: List of top candidates with their stats (usually top 2-3)
            constraints: Optional constraints (e.g., no double-booking)

        Returns:
            GeminiResponse with recommended candidate and reasoning
        """
        if not self.is_available():
            return self._fallback_tie_break(shift_details, candidates, constraints)

        try:
            # Prepare the prompt for Gemini
            prompt = self._build_tie_break_prompt(shift_details, candidates, constraints)

            # Call Gemini API with structured output
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiResponse,
                )
            )

            # Parse the structured response
            gemini_response = response.parsed
            if isinstance(gemini_response, GeminiResponse):
                return gemini_response
            else:
                # Fallback if response parsing failed
                return self._fallback_tie_break(shift_details, candidates, constraints)

        except Exception as e:
            print(f"Warning: Gemini API tie-break call failed: {e}")
            return self._fallback_tie_break(shift_details, candidates, constraints)

    def _build_explanation_prompt(self, shift_details: Dict[str, Any],
                                prediction_stats: Dict[str, Any]) -> str:
        """Build prompt for explaining a prediction."""
        return f"""
You are an AI assistant that explains shift allocation predictions in clear, natural language.

Shift Details:
- Location: {shift_details.get('location', 'Unknown')}
- Date: {shift_details.get('date', 'Unknown')} ({shift_details.get('day', 'Unknown')})
- Shift Type: {shift_details.get('shift_type', 'Unknown')}
- Time: {shift_details.get('start_time', 'Unknown')} to {shift_details.get('end_time', 'Unknown')}

Prediction Statistics:
- Top Candidate: {prediction_stats.get('top_candidate', 'None')}
- Top Candidate Confidence: {prediction_stats.get('top_candidate_confidence', 0)}%
- Second Candidate: {prediction_stats.get('second_candidate', 'None')}
- Second Candidate Confidence: {prediction_stats.get('second_candidate_confidence', 0)}%
- Historical Matches: {prediction_stats.get('total_matches', 0)} total shifts analyzed
- Match Type: {prediction_stats.get('match_type', 'unknown')}
- Additional Context: {prediction_stats.get('reasoning', 'No additional reasoning provided')}

Provide a clear, concise one-sentence explanation of why this prediction was made, suitable for showing to a human supervisor.
Focus on the pattern that was detected (e.g., "Ghulam has worked this shift 6 out of 8 times recently").
If confidence is low, explain why the prediction is uncertain.

Respond ONLY with a valid JSON object matching this structure:
{{
  "recommended_name": "string or null if no clear recommendation",
  "confidence": integer between 0 and 100,
  "reasoning": "clear one-sentence explanation in natural language"
}}
"""

    def _build_tie_break_prompt(self, shift_details: Dict[str, Any],
                              candidates: List[Dict[str, Any]],
                              constraints: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build prompt for tie-breaking between close candidates."""
        constraints_text = ""
        if constraints:
            constraints_text = f"\nConstraints to consider:\n{chr(10).join(['- ' + str(c) for c in constraints])}"

        candidates_text = ""
        for i, candidate in enumerate(candidates):
            candidates_text += f"""
Candidate {i+1}:
- Name: {candidate.get('name', 'Unknown')}
- Confidence: {candidate.get('confidence', 0)}%
- Historical Matches: {candidate.get('matches', 0)}
- Recent Activity: {candidate.get('recent_activity', 'Unknown')}
- Rotation Pattern Fit: {candidate.get('rotation_fit', 'Unknown')}
"""

        return f"""
You are an AI assistant that helps break ties in shift allocation predictions when multiple candidates have similar confidence scores.

Shift Details:
- Location: {shift_details.get('location', 'Unknown')}
- Date: {shift_details.get('date', 'Unknown')} ({shift_details.get('day', 'Unknown')})
- Shift Type: {shift_details.get('shift_type', 'Unknown')}
- Time: {shift_details.get('start_time', 'Unknown')} to {shift_details.get('end_time', 'Unknown')}

Candidates for Consideration:{candidates_text}{constraints_text}

Analyze the candidates and shift context to recommend the best choice, or determine that the shift should remain unassigned for human review.
Consider factors like:
- Consistency of historical performance
- Recent activity patterns
- Fairness in distribution
- Any specified constraints
- Overall suitability for this specific shift

Respond ONLY with a valid JSON object matching this structure:
{{
  "recommended_name": "string or null if shift should remain unassigned",
  "confidence": integer between 0 and 100 (confidence in this recommendation),
  "reasoning": "clear explanation of why this candidate was chosen or why human review is needed"
}}
"""

    def _fallback_explain_prediction(self, shift_details: Dict[str, Any],
                                   prediction_stats: Dict[str, Any]) -> GeminiResponse:
        """Fallback explanation when AI is not available."""
        top_candidate = prediction_stats.get('top_candidate', 'None')
        top_confidence = prediction_stats.get('top_candidate_confidence', 0)
        reasoning = prediction_stats.get('reasoning', 'No historical data available')

        # Generate a simple template-based explanation
        if top_candidate != 'None' and top_confidence > 0:
            explanation = f"{top_candidate} has worked this shift {top_confidence:.0f}% of the time based on historical patterns. {reasoning}"
        else:
            explanation = f"Insufficient historical data to make a confident prediction for this shift. {reasoning}"

        return GeminiResponse(
            recommended_name=top_candidate if top_candidate != 'None' and top_confidence >= 30 else None,
            confidence=min(95, int(top_confidence)) if top_candidate != 'None' else 0,
            reasoning=explanation
        )

    def _fallback_tie_break(self, shift_details: Dict[str, Any],
                          candidates: List[Dict[str, Any]],
                          constraints: Optional[List[Dict[str, Any]]] = None) -> GeminiResponse:
        """Fallback tie-breaking when AI is not available."""
        if not candidates:
            return GeminiResponse(
                recommended_name=None,
                confidence=0,
                reasoning="No candidates provided for tie-breaking analysis."
            )

        # Simple fallback: choose the candidate with highest confidence
        best_candidate = max(candidates, key=lambda x: x.get('confidence', 0))
        second_best = sorted(candidates, key=lambda x: x.get('confidence', 0), reverse=True)[1] if len(candidates) > 1 else None

        confidence_diff = 0
        if second_best:
            confidence_diff = best_candidate.get('confidence', 0) - second_best.get('confidence', 0)

        if confidence_diff < 10:  # Very close - recommend human review
            explanation = f"Top candidates {best_candidate.get('name')} ({best_candidate.get('confidence', 0)}%) and "
            if second_best:
                explanation += f"{second_best.get('name')} ({second_best.get('confidence', 0)}%) are very close in confidence. "
            explanation += "Human review recommended to consider factors like fairness, recent availability, and workload distribution."
            return GeminiResponse(
                recommended_name=None,
                confidence=max(30, 100 - confidence_diff * 5),  # Lower confidence for close calls
                reasoning=explanation
            )
        else:
            # Clear winner
            explanation = f"{best_candidate.get('name')} is recommended with {best_candidate.get('confidence', 0)}% confidence. "
            explanation += f"This candidate shows stronger historical patterns and consistency for this shift type."
            return GeminiResponse(
                recommended_name=best_candidate.get('name'),
                confidence=min(95, best_candidate.get('confidence', 0) + 5),
                reasoning=explanation
            )

# Global instance for easy access
ai_reasoning_engine = AIReasoningEngine()

def get_ai_reasoning_engine() -> AIReasoningEngine:
    """Get the global AI reasoning engine instance."""
    return ai_reasoning_engine

# Example usage and test function
def test_ai_reasoning():
    """Test function to verify AI reasoning engine works correctly."""
    engine = AIReasoningEngine()
    print("AIReasoningEngine initialized successfully")
    print(f"AI Available: {engine.is_available()}")
    return engine

if __name__ == "__main__":
    test_ai_reasoning()