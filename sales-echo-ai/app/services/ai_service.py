"""
AI Service for SalesEcho AI
Handles Tachles-style summary generation (Gemini 1.5 Flash) and language mix detection.
"""

import os
import json
import logging
import re
from typing import Optional, Dict, Any

from google import genai

from app.core.config import settings
from app.core.prompts import SALES_INSIGHTS_PROMPT_HE
from app.models.meeting_models import TachlesSummary

logger = logging.getLogger(__name__)


# ============================================
# Gemini Client (Lazy Initialization)
# ============================================

_gemini_client: Optional[genai.Client] = None


def get_gemini_client() -> genai.Client:
    """
    Get or create Gemini client instance for summary generation.

    Returns:
        genai.Client: Initialized Gemini client instance.

    Raises:
        ValueError: If GEMINI_API_KEY is not configured.
    """
    global _gemini_client

    if _gemini_client is None:
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("Gemini API key not configured. Set GEMINI_API_KEY in your .env file.")
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY in your .env file.")
        try:
            _gemini_client = genai.Client(api_key=api_key)
            logger.info("Gemini client (summary) initialized successfully")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to initialize Gemini client: %s", str(exc))
            raise ValueError(f"Gemini client initialization failed: {exc}") from exc

    return _gemini_client


# ============================================
# System Prompt for Tachles Summary v2.0
# ============================================

TACHLES_SYSTEM_PROMPT_V2 = """You are an Israeli Sales Operations expert analyzing a sales meeting transcript.

CRITICAL: Extract ONLY facts that are explicitly stated in the transcript. Do NOT infer, assume, or add information that is not directly mentioned.

Your task is to extract structured data in "Tachles" style (concise, direct, action-oriented Hebrew).

FACT-BASED EXTRACTION RULES:
- Extract ONLY what is explicitly stated in the transcript
- If a fact is unclear or ambiguous, set confidence < 0.7 and mark requires_review: true
- Every extracted item MUST have:
  * confidence: 0.0-1.0 (1.0 = completely certain, 0.0 = uncertain)
  * source: Exact quote from transcript (verbatim, in original language)
  * language: "he", "en", or "he-en" (for mixed)

HEBLISH OPTIMIZATION:
- Currency: Recognize ILS (₪), שקל, shekel, shekels. Convert to ILS.
- Dates: Handle Israeli date formats:
  * "יום ראשון הבא" = "next Sunday" (calculate actual date)
  * "סוף החודש" = "end of month" (calculate actual date)
  * DD/MM/YYYY format
  * Hebrew day names: ראשון, שני, שלישי, etc.
- Mixed language: Handle technical English terms in Hebrew sentences
  Example: "אני צריך את ה-API key" → Extract as "he-en"

REVIEW FLAG:
- If ANY confidence score < 0.7, set requires_review: true
- If overall confidence_score < 0.7, set requires_review: true
- This ensures human review for uncertain extractions

Output ONLY valid JSON matching this exact schema:
{
  "summary_id": "uuid",
  "metadata": {
    "org_id": "string",
    "rep_id": "string",
    "client_id": "string or null",
    "language_mix": "he-IL/en-US",
    "duration": number
  },
  "content": {
    "summary_text": "Bulleted Hebrew text (facts only, no inference)",
    "action_items": [
      {
        "task": "string",
        "due": "ISO date string or null",
        "assignee": "string or null",
        "confidence": 0.0-1.0,
        "source": "exact transcript quote",
        "language": "he|en|he-en"
      }
    ],
    "crm_entities": {
      "deal_value": {
        "value": number or null,
        "currency": "ILS or USD or null",
        "confidence": 0.0-1.0 or null,
        "source": "exact transcript quote or null",
        "language": "he|en|he-en or null"
      } or null,
      "next_meeting_date": {
        "value": "ISO date string or null",
        "confidence": 0.0-1.0 or null,
        "source": "exact transcript quote or null",
        "language": "he|en|he-en or null"
      } or null,
      "contact_email": {
        "value": "email@example.com or null",
        "confidence": 0.0-1.0 or null,
        "source": "exact transcript quote or null",
        "language": "he|en|he-en or null"
      } or null
    }
  },
  "governance": {
    "feedback_loop_applied": false,
    "confidence_score": 0.0-1.0,
    "hallucination_check": "passed|failed|pending",
    "requires_review": true or false
  }
}

IMPORTANT:
- All confidence scores must be between 0.0 and 1.0
- All sources must be exact quotes from the transcript
- If confidence < 0.7 for any item, set requires_review: true
- Calculate actual dates for relative dates (e.g., "יום ראשון הבא")
- CRM ENTITIES NULL HANDLING: If a CRM entity (deal_value, next_meeting_date, contact_email) is NOT mentioned in the transcript, you MUST return null for that entire entity object. Do NOT omit the field from the JSON - always include it with null value.
- For entity fields (value, currency, source, confidence), if not found, return null for that specific field. Do NOT omit fields from entity objects.
- Return ONLY valid JSON, no additional text or explanation."""


# ============================================
# Transcription Service
# ============================================

async def transcribe_audio(file_path: str, language: str = "he") -> Dict[str, Any]:
    """
    Transcribe an audio file using OpenAI Whisper API.

    Processes audio asynchronously and returns full transcript with metadata.
    Supports Hebrew, English, and bilingual code-switching. All text is UTF-8 encoded.

    Args:
        file_path: Path to audio file on local filesystem.
        language: Language code for transcription (default: "he" for Hebrew).

    Returns:
        Dict containing:
            - transcript (str): Full transcribed text (UTF-8).
            - transcript_raw (dict): Raw Whisper response with timestamps, segments.
            - language (str): Detected language code.
            - duration (float | None): Audio duration in seconds.
    """
    client = get_openai_client()

    try:
        logger.info(f"Starting transcription for file: {file_path}")

        with open(file_path, "rb") as audio_file:
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",
            )

        transcript_text = transcript_response.text
        transcript_raw = {
            "text": transcript_text,
            "language": transcript_response.language,
            "duration": getattr(transcript_response, "duration", None),
            "segments": getattr(transcript_response, "segments", []),
        }

        logger.info(
            "Transcription completed. Length: %s characters", len(transcript_text)
        )

        return {
            "transcript": transcript_text,
            "transcript_raw": transcript_raw,
            "language": transcript_response.language,
            "duration": getattr(transcript_response, "duration", None),
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Transcription error: %s", str(exc), exc_info=True)
        raise Exception(f"Transcription failed: {str(exc)}") from exc


# ============================================
# JSON Extraction Helper
# ============================================

def _extract_json_from_response(text: str) -> str:
    """
    Extract JSON object from Gemini response using robust regex-based extraction.
    
    Handles:
    - Markdown code blocks (```json ... ```)
    - Plain text with JSON embedded
    - Multiple JSON objects (extracts the largest one)
    - UTF-8 encoding issues
    
    Args:
        text: Raw response text from Gemini
        
    Returns:
        Cleaned JSON string ready for json.loads()
    """
    if not text:
        raise ValueError("Empty response text")
    
    # Step 1: Remove markdown code blocks if present
    cleaned = text.strip()
    
    # Remove ```json ... ``` or ``` ... ```
    markdown_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    markdown_matches = re.findall(markdown_pattern, cleaned, re.DOTALL)
    if markdown_matches:
        # Use the last match (usually the complete JSON)
        cleaned = markdown_matches[-1].strip()
    
    # Step 2: Extract JSON object using regex (find content between first { and last })
    # This handles cases where there's text before/after the JSON
    json_pattern = r'\{.*\}'
    json_matches = re.findall(json_pattern, cleaned, re.DOTALL)
    
    if json_matches:
        # Use the longest match (most likely the complete JSON)
        json_candidate = max(json_matches, key=len)
        
        # Validate it's balanced braces
        open_braces = json_candidate.count('{')
        close_braces = json_candidate.count('}')
        
        if open_braces == close_braces:
            return json_candidate.strip()
        else:
            # If unbalanced, try to find the complete object manually
            first_brace = cleaned.find('{')
            if first_brace != -1:
                # Find matching closing brace
                brace_count = 0
                for i in range(first_brace, len(cleaned)):
                    if cleaned[i] == '{':
                        brace_count += 1
                    elif cleaned[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return cleaned[first_brace:i+1].strip()
    
    # Step 3: If no JSON found, try the cleaned string as-is
    # (might be pure JSON without any wrapper)
    if cleaned.startswith('{') and cleaned.endswith('}'):
        return cleaned
    
    # Step 4: Last resort - raise error with diagnostic info
    raise ValueError(
        f"Could not extract valid JSON from response. "
        f"First 500 chars: {text[:500]}"
    )


# ============================================
# Summary Generation Service
# ============================================


def _build_fallback_summary(
    *,
    transcript: str,
    meeting_id: str,
    org_id: str,
    rep_id: str,
    client_id: Optional[str],
    duration: Optional[int],
    language_mix: str,
    reason: str,
) -> TachlesSummary:
    """
    Build a minimal, but contract-valid TachlesSummary when Gemini fails
    or when the conversation is too short for meaningful AI analysis.
    """
    # Use a trimmed version of the transcript for context in the fallback
    trimmed_transcript = (transcript or "").strip()
    if len(trimmed_transcript) > 500:
        trimmed_transcript = trimmed_transcript[:500] + "..."

    summary_text = "שיחת מכירה קצרה מאוד.\n"
    if trimmed_transcript:
        summary_text += f"תמליל זמין (מלא/חלקי):\n{trimmed_transcript}\n"
    summary_text += f"(נוצר סיכום fallback בגלל: {reason})"

    # Minimal contract-compliant structure
    summary_dict: Dict[str, Any] = {
        "summary_id": meeting_id,
        "metadata": {
            "org_id": org_id,
            "rep_id": rep_id,
            "client_id": client_id,
            "language_mix": language_mix,
            "duration": duration,
        },
        "content": {
            "summary_text": summary_text,
            "action_items": [],
            "crm_entities": {
                "deal_value": None,
                "next_meeting_date": None,
                "contact_email": None,
                "additional_entities": None,
            },
        },
        "governance": {
            "feedback_loop_applied": False,
            # Conservative confidence, force human review
            "confidence_score": 0.4,
            "hallucination_check": "pending",
            "requires_review": True,
        },
    }

    return TachlesSummary(**summary_dict)


async def get_organization_settings(org_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch organization settings including custom prompt instructions.
    
    Args:
        org_id: Organization UUID.
        
    Returns:
        Dict with settings or None if not found.
    """
    try:
        from app.core.database import get_prisma
        prisma = get_prisma()
        
        settings_record = await prisma.organizationsettings.find_unique(
            where={"org_id": org_id}
        )
        
        if settings_record:
            return {
                "custom_prompt_instructions": settings_record.custom_prompt_instructions,
                "enabled_modules": settings_record.enabled_modules,
                "industry_type": settings_record.industry_type,
                "default_language": settings_record.default_language,
                "auto_dispatch_actions": settings_record.auto_dispatch_actions,
            }
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch org settings for {org_id}: {e}")
        return None


async def generate_summary(
    transcript: str,
    meeting_id: str,
    org_id: str,
    rep_id: str,
    client_id: Optional[str] = None,
    duration: Optional[int] = None,
    language_mix: str = "he-IL/en-US",
    custom_instructions: Optional[str] = None,
    historical_context: Optional[str] = None,
) -> TachlesSummary:
    """
    Generate Tachles-style summary from transcript using Gemini 1.5 Flash.

    Args:
        transcript: Full transcribed text (UTF-8, Hebrew/English).
        meeting_id: UUID of the meeting (used as summary_id if missing).
        org_id: Organization UUID.
        rep_id: Sales rep UUID.
        client_id: Optional client/contact UUID.
        duration: Optional meeting duration in seconds.
        language_mix: Language mix string (e.g., "he-IL/en-US").
        custom_instructions: Optional custom prompt instructions from org settings.
        historical_context: Optional block of client history from previous meetings.

    Returns:
        TachlesSummary Pydantic model with structured summary data.
    """
    client = get_gemini_client()

    try:
        logger.info("Generating summary (Gemini) for meeting: %s", meeting_id)

        # Fetch organization-specific settings if custom_instructions not provided
        org_custom_prompt = custom_instructions
        if not org_custom_prompt:
            org_settings = await get_organization_settings(org_id)
            if org_settings and org_settings.get("custom_prompt_instructions"):
                org_custom_prompt = org_settings["custom_prompt_instructions"]
                logger.info(
                    "Using custom prompt instructions for org %s: %s...",
                    org_id,
                    org_custom_prompt[:100] if len(org_custom_prompt) > 100 else org_custom_prompt
                )

        # If the conversation is extremely short, skip expensive AI call and
        # return a deterministic minimal summary instead of failing.
        if not transcript or len(transcript.strip()) < 20:
            logger.info(
                "Transcript too short for full AI summary (len=%s). "
                "Using fallback summary for meeting: %s",
                len(transcript.strip()) if transcript else 0,
                meeting_id,
            )
            return _build_fallback_summary(
                transcript=transcript or "",
                meeting_id=meeting_id,
                org_id=org_id,
                rep_id=rep_id,
                client_id=client_id,
                duration=duration,
                language_mix=language_mix,
                reason="תמליל קצר מאוד (Hello/Bye או דומה)",
            )

        # Build custom instructions block if organization has specific requirements
        custom_instructions_block = ""
        if org_custom_prompt:
            custom_instructions_block = f"""
=== ORGANIZATION-SPECIFIC INSTRUCTIONS ===
The following are custom analysis requirements from this organization. 
Apply these instructions IN ADDITION to the standard analysis:

{org_custom_prompt}

=== END ORGANIZATION-SPECIFIC INSTRUCTIONS ===

"""

        # Build historical context block for relationship continuity
        historical_context_block = ""
        if historical_context:
            historical_context_block = f"""
{historical_context}

HISTORICAL CONTEXT USAGE INSTRUCTIONS:
- Use client history to identify follow-up items from previous meetings
- Note any changes in sentiment compared to previous conversations
- Identify if previously discussed objections have been addressed
- Reference relationship stage when assessing deal heat
- Do NOT hallucinate information - only reference what's in the history block

"""
            logger.info(
                "Injecting historical context for client (%d chars)",
                len(historical_context)
            )

        # Combine business-focused sales prompt (Hebrew) + Tachles data contract prompt
        # into a single Gemini instruction block. Gemini does not have system/user roles,
        # so we embed both prompts followed by the concrete task and transcript.
        user_prompt = (
            f"{SALES_INSIGHTS_PROMPT_HE}\n\n"
            f"{TACHLES_SYSTEM_PROMPT_V2}\n\n"
            f"{custom_instructions_block}"
            f"{historical_context_block}"
            "עכשיו נתח את תמליל שיחת המכירה הבאה והפק סיכום בהתאם להנחיות והמבנה לעיל.\n\n"
            "חשוב מאוד - הנחיות פורמט JSON:\n"
            "- החזר רק אובייקט JSON תקין (valid JSON object) ללא כל טקסט נוסף.\n"
            "- אל תשתמש ב-Markdown code blocks (אל תעטוף ב-```json או ```).\n"
            "- התחל ישירות עם { והמשך עם כל המבנה המלא של ה-JSON.\n"
            "- ודא שכל המחרוזות (strings) מוגדרות כראוי ל-JSON:\n"
            "  * השתמש ב-\\\" עבור ציטוטים בתוך מחרוזות.\n"
            "  * השתמש ב-\\n עבור שורות חדשות.\n"
            "  * ודא שכל התווים המיוחדים מוגדרים (escaped) כראוי.\n"
            "- טיפול ב-CRM entities חסרים:\n"
            "  * אם CRM entity (deal_value, next_meeting_date, contact_email) לא הוזכר בתמליל, החזר null עבור כל האובייקט.\n"
            "  * אל תמחק את השדה מה-JSON - תמיד כלול אותו עם ערך null.\n"
            "  * אם שדה ספציפי בתוך entity לא נמצא, החזר null עבור השדה הזה.\n"
            "- הפלט חייב להיות JSON תקין בלבד, התואם במדויק לסכמת הנתונים שתוארה לעיל.\n"
            "- אין להוסיף הסברים, הערות, או טקסט מחוץ ל-JSON.\n\n"
            f"תמליל השיחה:\n{transcript}\n"
        )

        # Discover an appropriate text-capable Gemini model (flash preferred)
        try:
            available_models = list(client.models.list())
            model_name = None
            for m in available_models:
                name = getattr(m, "name", "") or ""
                methods = getattr(m, "supported_generation_methods", []) or getattr(m, "generation_methods", []) or []
                if "flash" in name.lower() and ("generateContent" in methods or not methods):
                    model_name = name
                    break
            if not model_name:
                model_name = "gemini-1.5-flash"
            logger.info("Using Gemini model for summary: %s", model_name)
        except Exception as discovery_error:
            logger.warning("Failed to list Gemini models for summary, using default id: %s", discovery_error)
            model_name = "gemini-1.5-flash"

        response = client.models.generate_content(
            model=model_name,
            contents=[user_prompt],
        )

        # Extract raw text content from Gemini response
        if hasattr(response, "text"):
            summary_json_str = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            content = getattr(candidate, "content", None)
            if content is not None and getattr(content, "parts", None):
                summary_json_str = content.parts[0].text
            else:
                summary_json_str = str(candidate)
        else:
            summary_json_str = str(response)

        # Log raw Gemini output (truncated for safety)
        logger.info(
            "Raw Gemini summary response for meeting %s (first 2000 chars): %s",
            meeting_id,
            (summary_json_str[:2000] + "…") if len(summary_json_str) > 2000 else summary_json_str,
        )

        # Robust JSON extraction: Use regex-based extraction to find JSON between { and }
        try:
            extracted_json_str = _extract_json_from_response(summary_json_str)
            logger.debug(
                "Extracted JSON for meeting %s (first 500 chars): %s",
                meeting_id,
                extracted_json_str[:500] if len(extracted_json_str) > 500 else extracted_json_str,
            )
        except ValueError as extract_err:
            logger.error(
                "Failed to extract JSON from Gemini response for meeting %s: %s. "
                "Raw response (first 1000 chars): %s",
                meeting_id,
                str(extract_err),
                summary_json_str[:1000],
            )
            raise Exception(f"Could not extract JSON from Gemini response: {str(extract_err)}") from extract_err
        
        # Parse the extracted JSON (ensure UTF-8 encoding)
        try:
            # Ensure the string is properly encoded as UTF-8
            if isinstance(extracted_json_str, bytes):
                extracted_json_str = extracted_json_str.decode('utf-8')
            
            summary_dict = json.loads(extracted_json_str, strict=False)
        except json.JSONDecodeError as json_err:
            logger.error(
                "Failed to parse extracted JSON for meeting %s. "
                "Error: %s (line %s, column %s). "
                "Extracted JSON (first 1000 chars): %s",
                meeting_id,
                str(json_err.msg),
                json_err.lineno,
                json_err.colno,
                extracted_json_str[:1000] if len(extracted_json_str) > 1000 else extracted_json_str,
            )
            raise Exception(
                f"Invalid JSON response from Gemini: {str(json_err.msg)} "
                f"(line {json_err.lineno}, column {json_err.colno})"
            ) from json_err

        # Ensure summary_id is set
        if not summary_dict.get("summary_id"):
            summary_dict["summary_id"] = meeting_id

        # Ensure metadata block exists and is populated
        metadata = summary_dict.get("metadata") or {}
        metadata.update(
            {
                "org_id": org_id,
                "rep_id": rep_id,
                "client_id": client_id,
                "language_mix": language_mix,
                "duration": duration,
            }
        )
        summary_dict["metadata"] = metadata

        # Ensure governance block has requires_review flag
        governance = summary_dict.get("governance") or {}
        if "requires_review" not in governance:
            # Auto-set requires_review if confidence < 0.7
            confidence = governance.get("confidence_score", 1.0)
            governance["requires_review"] = confidence < 0.7
        summary_dict["governance"] = governance

        summary = TachlesSummary(**summary_dict)

        logger.info(
            "Summary generated successfully. Confidence: %s",
            summary.governance.confidence_score,
        )

        return summary

    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse JSON from Gemini response for meeting %s: %s",
            meeting_id,
            str(exc),
            exc_info=True,
        )
        # Fallback instead of failing the whole pipeline
        return _build_fallback_summary(
            transcript=transcript or "",
            meeting_id=meeting_id,
            org_id=org_id,
            rep_id=rep_id,
            client_id=client_id,
            duration=duration,
            language_mix=language_mix,
            reason=f"שגיאת JSON מתשובת Gemini: {exc}",
        )

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Summary generation error for meeting %s: %s",
            meeting_id,
            str(exc),
            exc_info=True,
        )
        # Fallback instead of failing the whole pipeline
        return _build_fallback_summary(
            transcript=transcript or "",
            meeting_id=meeting_id,
            org_id=org_id,
            rep_id=rep_id,
            client_id=client_id,
            duration=duration,
            language_mix=language_mix,
            reason=f"שגיאה כללית בתהליך הסיכום: {exc}",
        )


# ============================================
# Helper Functions
# ============================================

def detect_language_mix(transcript: str) -> str:
    """
    Detect language mix in transcript (Hebrew/English).

    Simple heuristic-based detection. Checks for Hebrew characters (U+0590 to U+05FF)
    and English characters. Returns appropriate language mix string.

    Args:
        transcript: Text to analyze (UTF-8 encoded).

    Returns:
        str: Language mix string:
            - "he-IL/en-US" if both Hebrew and English detected
            - "he-IL" if only Hebrew detected
            - "en-US" if only English detected
    """
    hebrew_chars = any("\u0590" <= char <= "\u05FF" for char in transcript)
    english_chars = any(char.isalpha() and ord(char) < 128 for char in transcript)

    if hebrew_chars and english_chars:
        return "he-IL/en-US"
    if hebrew_chars:
        return "he-IL"
    return "en-US"

