"""
Transcription Service for SalesEcho AI
Handles audio transcription with Gemini 1.5 Flash (primary and only provider).
Includes audio pre-processing, diarization, usage tracking, and status updates.
"""

import os
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

from google import genai

from app.core.config import settings
from app.core.database import prisma

logger = logging.getLogger(__name__)


# ============================================
# Gemini Client (Lazy Initialization)
# ============================================

_gemini_client: Optional[genai.Client] = None


def _get_gemini_client() -> genai.Client:
    """
    Get or create Gemini client instance using the new google-genai SDK.
    
    Returns:
        genai.Client: Initialized Gemini client instance.
    
    Raises:
        ValueError: If GEMINI_API_KEY is not configured.
    """
    global _gemini_client
    
    if _gemini_client is None:
        # Prefer value from settings (pydantic-settings), but allow raw env override
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("Gemini API key not configured. Set GEMINI_API_KEY in your .env file.")
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY in your .env file.")
        
        # Initialize client - try to specify API version if needed
        try:
            _gemini_client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized successfully (google-genai SDK)")
        except Exception as init_error:
            logger.error(f"Failed to initialize Gemini client: {init_error}")
            raise ValueError(f"Gemini client initialization failed: {init_error}")
    
    return _gemini_client


# ============================================
# Audio Pre-processing Layer
# ============================================

async def normalize_audio(
    input_path: str,
    output_path: Optional[str] = None,
    cleanup_original: bool = False
) -> str:
    """
    Normalize audio file to standardized format using FFmpeg.
    
    Converts any audio format (.m4a, .wav, .webm, etc.) to:
    - Format: MP3
    - Channels: Mono
    - Sample Rate: 16kHz
    - Bitrate: 64kbps
    
    This ensures:
    - Files stay under 25MB limit for OpenAI/Gemini APIs
    - Consistent quality for better STT accuracy
    - Optimal file size for faster uploads
    
    Args:
        input_path: Path to input audio file
        output_path: Optional output path (default: temp file)
        cleanup_original: If True, delete original file after conversion
    
    Returns:
        Path to normalized audio file
    
    Raises:
        ValueError: If FFmpeg is not available or conversion fails
        FileNotFoundError: If input file doesn't exist
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Audio file not found: {input_path}")
    
    # Check if FFmpeg is available
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
            timeout=5
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("FFmpeg not found. Skipping audio normalization. Install FFmpeg for optimal performance.")
        return input_path  # Return original if FFmpeg unavailable
    
    # Generate output path if not provided
    if not output_path:
        temp_dir = Path(tempfile.gettempdir()) / "salesecho_audio"
        temp_dir.mkdir(exist_ok=True)
        output_path = str(temp_dir / f"normalized_{os.path.basename(input_path)}.mp3")
    
    try:
        # FFmpeg command for normalization
        # -i: input file
        # -ac 1: Convert to mono (1 audio channel)
        # -ar 16000: Set sample rate to 16kHz
        # -b:a 64k: Set audio bitrate to 64kbps
        # -f mp3: Output format MP3
        # -y: Overwrite output file if exists
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ac", "1",           # Mono
            "-ar", "16000",       # 16kHz sample rate
            "-b:a", "64k",        # 64kbps bitrate
            "-f", "mp3",          # MP3 format
            "-y",                 # Overwrite
            output_path
        ]
        
        logger.info(f"Normalizing audio: {input_path} -> {output_path}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            check=True
        )
        
        # Verify output file was created and check size
        if not os.path.exists(output_path):
            raise ValueError(f"FFmpeg conversion failed: output file not created")
        
        output_size = os.path.getsize(output_path)
        input_size = os.path.getsize(input_path)
        
        logger.info(
            f"Audio normalization complete. "
            f"Size: {input_size / (1024*1024):.2f}MB -> {output_size / (1024*1024):.2f}MB"
        )
        
        # Check if file exceeds 25MB limit (OpenAI/Gemini limit)
        if output_size > 25 * 1024 * 1024:
            logger.warning(
                f"Normalized audio file ({output_size / (1024*1024):.2f}MB) exceeds 25MB limit. "
                f"May cause API errors."
            )
        
        # Cleanup original file if requested
        if cleanup_original and output_path != input_path:
            try:
                os.remove(input_path)
                logger.debug(f"Cleaned up original file: {input_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup original file: {str(e)}")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg conversion failed: {error_msg}")
        raise ValueError(f"Audio normalization failed: {error_msg}") from e
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out (>5 minutes)")
        raise ValueError("Audio normalization timed out") from None
    except Exception as e:
        logger.error(f"Unexpected error during audio normalization: {str(e)}", exc_info=True)
        raise


def _get_audio_duration_ffmpeg(file_path: str) -> Optional[float]:
    """
    Get accurate audio duration using FFmpeg.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Duration in seconds (or None if cannot determine)
    """
    try:
        # Use FFprobe to get duration
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        
        duration = float(result.stdout.strip())
        return duration
        
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        # Fallback to file size estimation
        return _get_audio_duration(file_path)


# ============================================
# Transcription (Gemini-only)
# ============================================

async def transcribe_audio_with_fallback(
    file_path: str,
    meeting_id: str,
    org_id: str,
    language: str = "he"
) -> Dict[str, Any]:
    """
    Transcribe audio file using Gemini 1.5 Flash (Gemini-only pipeline).
    
    Handles:
    - Audio pre-processing (normalization to MP3, Mono, 16kHz, 64kbps)
    - Transcription via Gemini 1.5 Flash
    - Speaker diarization (Speaker A, Speaker B) for mono recordings
    - Usage tracking (updates organization.usage_minutes)
    - Meeting status updates (COMPLETED or FAILED)
    
    Args:
        file_path: Path to audio file (any format: .m4a, .wav, .webm, etc.)
        meeting_id: UUID of the meeting record
        org_id: Organization UUID for usage tracking
        language: Language code (default: "he" for Hebrew)
    
    Returns:
        Dict containing:
            - transcript (str): Full transcribed text
            - transcript_raw (dict): Raw response with segments, timestamps
            - language (str): Detected language
            - duration (float): Audio duration in seconds
            - provider (str): "gemini"
            - speakers (list): Speaker labels if diarization available
            - normalized_path (str): Path to normalized audio file (if created)
    """
    # Update meeting status to PROCESSING
    await _update_meeting_status(meeting_id, "PROCESSING")
    
    normalized_path = None
    original_path = file_path
    
    try:
        # Step 1: Normalize audio (pre-processing)
        logger.info(f"Pre-processing audio for meeting {meeting_id}: {file_path}")
        try:
            normalized_path = await normalize_audio(file_path)
            file_path = normalized_path  # Use normalized file for transcription
            logger.info(f"Audio normalized successfully: {normalized_path}")
        except Exception as e:
            logger.warning(f"Audio normalization failed, using original file: {str(e)}")
            # Continue with original file if normalization fails
        
        # Step 2: Transcribe with Gemini (single-provider pipeline)
        logger.info(f"Attempting transcription with Gemini for meeting {meeting_id}")
        result = await _transcribe_with_gemini(file_path, language)
        result["provider"] = "gemini"
        result["normalized_path"] = normalized_path if normalized_path else None
        
        # Update usage and status on success
        await _track_usage_and_update_status(meeting_id, org_id, result.get("duration"), "COMPLETED")
        
        # Cleanup normalized file if it's different from original
        if normalized_path and normalized_path != original_path:
            try:
                os.remove(normalized_path)
                logger.debug(f"Cleaned up normalized file: {normalized_path}")
            except Exception:
                pass
        
        return result
        
    except Exception as e:
        # Other errors (file not found, normalization failure, etc.)
        error_type = type(e).__name__
        logger.error(
            f"Transcription failed for meeting {meeting_id} ({error_type}): {str(e)}",
            exc_info=True
        )
        
        # Cleanup normalized file on error
        if normalized_path and normalized_path != original_path:
            try:
                os.remove(normalized_path)
            except:
                pass
        
        await _update_meeting_status(meeting_id, "FAILED")
        await _log_processing_error(meeting_id, {
            "stage": "transcription",
            "error": str(e),
            "error_type": error_type,
            "provider": "unknown"
        })
        raise


async def _transcribe_with_openai(file_path: str, language: str = "he") -> Dict[str, Any]:
    """
    Deprecated OpenAI Whisper transcription helper.
    
    NOTE: The current pipeline is Gemini-only. This function is kept for
    historical/reference purposes and is not used in production.
    """
    raise RuntimeError("OpenAI Whisper transcription is disabled. The pipeline is Gemini-only.")


async def _transcribe_with_gemini(file_path: str, language: str = "he") -> Dict[str, Any]:
    """
    Transcribe audio using Gemini 1.5 Flash with native audio support.
    
    Gemini 1.5 Flash can process audio directly and provide both transcript and summary.
    We leverage this to save tokens by getting structured output in one call.
    
    Args:
        file_path: Path to audio file
        language: Language code (for prompt context)
    
    Returns:
        Dict with transcript, transcript_raw, language, duration, speakers
    """
    client = _get_gemini_client()
    uploaded_file = None
    
    try:
        # Upload audio file using new SDK v1.x
        # SDK v1.x expects 'file' as the keyword argument for the file path
        uploaded_file = client.files.upload(file=file_path)
        
        logger.info(f"Uploaded audio file to Gemini: {uploaded_file.name}")
        
        # Wait for file to be processed (if needed)
        # The new SDK may require waiting for file processing
        if hasattr(uploaded_file, 'wait') and callable(uploaded_file.wait):
            uploaded_file.wait()
        
        # Diarization prompt for speaker separation
        prompt = f"""Transcribe this sales meeting audio recording in {language} language.

CRITICAL REQUIREMENTS:
1. Identify and separate speakers as "Speaker A" and "Speaker B" (or "Rep" and "Client" if context is clear)
2. Format each line as: [Speaker A]: text or [Speaker B]: text
3. For mono recordings, use context clues (content, tone, language patterns) to identify speakers
4. Provide the full transcript with speaker labels

Return the transcript with clear speaker separation."""

        # Discover an appropriate Gemini model dynamically
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
                # Sensible default if discovery fails but API may still accept this ID
                model_name = "gemini-1.5-flash"
            logger.info(f"Using Gemini model for transcription: {model_name}")
        except Exception as discovery_error:
            logger.warning(f"Failed to list Gemini models, falling back to default model id: {discovery_error}")
            model_name = "gemini-1.5-flash"
        
        # Generate transcript with speaker diarization using discovered model
        response = client.models.generate_content(
            model=model_name,
            contents=[
                uploaded_file,  # Uploaded file object (SDK handles it automatically)
                prompt  # Text prompt as string
            ]
        )
        
        # Extract text from response
        # The new SDK returns response with text attribute
        if hasattr(response, 'text'):
            transcript_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            # Fallback: extract from candidates structure
            candidate = response.candidates[0]
            if hasattr(candidate, 'content'):
                content = candidate.content
                if hasattr(content, 'parts') and content.parts:
                    transcript_text = content.parts[0].text
                elif hasattr(content, 'text'):
                    transcript_text = content.text
                else:
                    transcript_text = str(content)
            else:
                transcript_text = str(candidate)
        else:
            transcript_text = str(response)
        
        # Extract speaker information
        speakers = _extract_speakers_from_transcript(transcript_text, [])
        
        # Get file metadata for duration (if available)
        # Note: Gemini doesn't return duration directly, we may need to estimate
        # or get it from the file metadata
        duration = _get_audio_duration(file_path)
        
        transcript_raw = {
            "text": transcript_text,
            "language": language,
            "duration": duration,
            "segments": [],  # Gemini doesn't provide segment-level timestamps
            "speakers": speakers,
            "provider": "gemini",
        }
        
        logger.info(
            f"Gemini transcription completed. Length: {len(transcript_text)} characters, "
            f"Duration: {duration}s, Speakers detected: {len(speakers)}"
        )
        
        # Clean up uploaded file
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                logger.debug(f"Cleaned up uploaded file: {uploaded_file.name}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup uploaded file: {str(cleanup_error)}")
        
        return {
            "transcript": transcript_text,
            "transcript_raw": transcript_raw,
            "language": language,
            "duration": duration,
            "speakers": speakers,
        }
        
    except Exception as e:
        # Clean up uploaded file on error
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
            except:
                pass
        raise Exception(f"Gemini transcription failed: {str(e)}") from e


def _extract_speakers_from_transcript(transcript: str, segments: list) -> list:
    """
    Extract speaker information from transcript.
    
    Looks for patterns like [Speaker A], [Speaker B], [Rep], [Client], etc.
    
    Args:
        transcript: Full transcript text
        segments: Whisper segments (if available from OpenAI)
    
    Returns:
        List of unique speaker labels found
    """
    import re
    
    speakers = set()
    
    # Pattern 1: [Speaker A], [Speaker B], etc.
    pattern1 = r'\[(Speaker\s+[A-Z]|Rep|Client)\]'
    matches = re.findall(pattern1, transcript, re.IGNORECASE)
    speakers.update([m.lower() for m in matches])
    
    # Pattern 2: Speaker A:, Speaker B:, etc.
    pattern2 = r'(Speaker\s+[A-Z]|Rep|Client):'
    matches = re.findall(pattern2, transcript, re.IGNORECASE)
    speakers.update([m.lower() for m in matches])
    
    # Pattern 3: Check segments for speaker labels (if available)
    if segments:
        for segment in segments:
            if isinstance(segment, dict) and "speaker" in segment:
                speakers.add(segment["speaker"].lower())
    
    return sorted(list(speakers)) if speakers else ["speaker_a", "speaker_b"]


def _get_audio_duration(file_path: str) -> Optional[float]:
    """
    Get audio file duration in seconds.
    
    First attempts FFmpeg (accurate), then falls back to file size estimation.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Duration in seconds (or None if cannot determine)
    """
    # Try FFmpeg first (accurate)
    duration = _get_audio_duration_ffmpeg(file_path)
    if duration:
        return duration
    
    # Fallback: Basic estimation
    try:
        # For normalized MP3 at 64kbps mono: ~0.48MB per minute
        # For other formats: rough estimate
        file_size = os.path.getsize(file_path)
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == ".mp3":
            # MP3 at 64kbps mono: ~0.48MB per minute
            estimated_duration = (file_size / (1024 * 1024)) * 60 / 0.48
        else:
            # Generic estimate: ~1MB per minute
            estimated_duration = (file_size / (1024 * 1024)) * 60
        
        logger.debug(f"Estimated audio duration: {estimated_duration:.2f}s (from file size)")
        return estimated_duration
    except:
        return None


# ============================================
# Usage Tracking and Status Updates
# ============================================

async def _track_usage_and_update_status(
    meeting_id: str,
    org_id: str,
    duration_seconds: Optional[float],
    status: str
) -> None:
    """
    Track usage (update organization.usage_minutes) and update meeting status.
    
    Args:
        meeting_id: UUID of the meeting
        org_id: Organization UUID
        duration_seconds: Audio duration in seconds (None if unknown)
        status: Meeting status ("COMPLETED" or "FAILED")
    """
    try:
        # Calculate duration in minutes
        duration_minutes = 0.0
        if duration_seconds:
            duration_minutes = duration_seconds / 60.0
        
        # Update organization usage_minutes
        if duration_minutes > 0:
            # Read current value and increment (Prisma Python doesn't support increment syntax directly)
            org = await prisma.organization.find_unique(where={"id": org_id})
            current_usage = org.usage_minutes if org else 0.0
            new_usage = current_usage + duration_minutes
            
            await prisma.organization.update(
                where={"id": org_id},
                data={"usage_minutes": new_usage}
            )
            logger.info(
                f"Updated usage for org {org_id}: {current_usage:.2f} + {duration_minutes:.2f} = {new_usage:.2f} minutes"
            )
        
        # Update meeting status
        await _update_meeting_status(meeting_id, status)
        
    except Exception as e:
        logger.error(f"Failed to track usage or update status for meeting {meeting_id}: {str(e)}", exc_info=True)
        # Don't raise - this is a side effect, shouldn't fail the transcription


async def _update_meeting_status(meeting_id: str, status: str) -> None:
    """
    Update meeting status in database.
    
    Args:
        meeting_id: UUID of the meeting
        status: Status string (PENDING, PROCESSING, COMPLETED, FAILED)
    """
    try:
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={"status": status}
        )
        logger.debug(f"Updated meeting {meeting_id} status to {status}")
    except Exception as e:
        logger.error(f"Failed to update meeting status: {str(e)}", exc_info=True)
        # Don't raise - status update failure shouldn't break transcription


async def _log_processing_error(meeting_id: str, error_data: Dict[str, Any]) -> None:
    """
    Log processing error to meeting.processing_errors JSON field.
    
    Args:
        meeting_id: UUID of the meeting
        error_data: Error information dict
    """
    try:
        from prisma import Json
        from datetime import datetime
        
        # Get existing errors
        meeting = await prisma.meeting.find_unique(where={"id": meeting_id})
        existing_errors = []
        
        if meeting and meeting.processing_errors:
            if isinstance(meeting.processing_errors, dict):
                existing_errors = meeting.processing_errors.get("errors", [])
            elif isinstance(meeting.processing_errors, list):
                existing_errors = meeting.processing_errors
        
        # Add new error
        error_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        existing_errors.append(error_data)
        
        # Update meeting with errors
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={
                "processing_errors": Json({"errors": existing_errors})
            }
        )
        
        logger.debug(f"Logged processing error for meeting {meeting_id}")
    except Exception as e:
        logger.error(f"Failed to log processing error: {str(e)}", exc_info=True)
        # Don't raise - error logging failure shouldn't break transcription

