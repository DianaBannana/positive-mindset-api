"""
API Endpoints for Meeting Management
Handles audio upload, transcription, and summary generation
"""

import os
import uuid
import logging
from typing import Optional, List
from pathlib import Path
import tempfile
import json
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse

from prisma import Json

from app.core.database import get_db, prisma
from app.core.config import settings
from app.core.utils import generate_slug
from app.services.ai_service import generate_summary, detect_language_mix
from app.services.transcription_service import transcribe_audio_with_fallback
from app.models.meeting_models import MeetingUploadResponse, TachlesSummary, MeetingResponse

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meetings", tags=["meetings"])


# ============================================
# Helper Functions
# ============================================

def save_uploaded_file(file: UploadFile) -> str:
    """
    Save uploaded file to temporary directory
    
    Returns:
        Path to saved file
    """
    # Create temp directory if it doesn't exist
    temp_dir = Path(tempfile.gettempdir()) / "salesecho_uploads"
    temp_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix if file.filename else ".tmp"
    temp_file_path = temp_dir / f"{uuid.uuid4()}{file_ext}"
    
    # Save file
    with open(temp_file_path, "wb") as f:
        content = file.file.read()
        f.write(content)
    
    logger.info(f"Saved uploaded file to: {temp_file_path}")
    return str(temp_file_path)


def cleanup_temp_file(file_path: str):
    """Remove temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")


async def log_processing_error(meeting_id: str, error: Exception, stage: str):
    """Log processing error to database"""
    try:
        error_data = {
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Get existing errors or create new array
        meeting = await prisma.meeting.find_unique(where={"id": meeting_id})
        existing_errors = []
        
        if meeting and meeting.processing_errors:
            # Prisma Python returns JSON as dict/list, ensure it's a list
            if isinstance(meeting.processing_errors, list):
                existing_errors = list(meeting.processing_errors)
            elif isinstance(meeting.processing_errors, dict):
                # If it's a dict, convert to list
                existing_errors = [meeting.processing_errors]
        
        existing_errors.append(error_data)
        
        # Update meeting with error
        # Prisma Python JSON fields: Use Prisma.Json wrapper for proper type handling
        try:
            await prisma.meeting.update(
                where={"id": meeting_id},
                data={"processing_errors": Json(existing_errors)}
            )
        except Exception as json_error:
            # If Json wrapper fails, try without wrapper (some versions may accept dict/list directly)
            logger.warning(f"Json wrapper failed, trying direct assignment: {str(json_error)}")
            try:
                await prisma.meeting.update(
                    where={"id": meeting_id},
                    data={"processing_errors": existing_errors}
                )
            except Exception as e2:
                # If both fail, log but don't crash - error is already logged above
                logger.error(f"Failed to update processing_errors in database: {str(e2)}")
                pass
        
        logger.error(f"Logged processing error for meeting {meeting_id}: {error_data}")
    
    except Exception as e:
        logger.error(f"Failed to log processing error: {str(e)}", exc_info=True)


def _normalize_transcript_raw(value):
    """
    Normalize transcript_raw into a JSON-serializable dict suitable for Prisma.

    - If value is None or empty, return None
    - If dict, return as-is
    - If string, try json.loads, else wrap as {"text": value}
    - For any other type, stringify into a small dict
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
            # Parsed but not a dict (e.g. list/primitive) – wrap original text
            return {"text": value}
        except json.JSONDecodeError:
            return {"text": value}
    # Fallback for unexpected types (e.g. SDK objects)
    try:
        json.dumps(value, default=str)
        return {"payload": str(value)}
    except Exception:
        return {"text": str(value)}


# ============================================
# API Endpoints
# ============================================

@router.post("/upload", response_model=MeetingUploadResponse)
async def upload_meeting_audio(
    org_id: str = Form(...),
    user_id: str = Form(...),
    client_name: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """
    Upload audio file for meeting transcription and summary generation
    
    Process:
    1. Save uploaded file temporarily
    2. Create Meeting record in database
    3. Transcribe audio using Whisper
    4. Generate Tachles summary using GPT-4o
    5. Update Meeting record with results
    6. Clean up temporary file
    """
    meeting_id = str(uuid.uuid4())
    temp_file_path = None
    
    try:
        # Validate and fix UUIDs
        def is_valid_uuid(uuid_string):
            try:
                uuid.UUID(uuid_string)
                return True
            except (ValueError, TypeError):
                return False
        
        # DEV_ONLY_WARNING: In development mode, use DEV_ORG_ID from environment if provided
        # This ensures consistent org_id across upload and fetch operations
        # MUST be removed before production - replace with Auth middleware
        if settings.dev_org_id and (not is_valid_uuid(org_id) or org_id == "default-org-id"):
            logger.warning(
                f"DEV_ONLY: Invalid or default org_id: {org_id}. "
                f"Using DEV_ORG_ID from environment: {settings.dev_org_id}"
            )
            org_id = settings.dev_org_id
        
        # Handle org_id - ensure it exists in database
        if not is_valid_uuid(org_id) or org_id == "default-org-id":
            logger.warning(f"Invalid or default org_id: {org_id}. Looking up or creating default organization...")
            # Try to find an existing organization
            user_org = await prisma.organization.find_first()
            if user_org:
                org_id = user_org.id
                logger.info(f"Using existing organization: {org_id}")
            else:
                # Create a default organization with unique slug using utility function
                unique_slug = await generate_slug("Default Organization")
                default_org = await prisma.organization.create(
                    data={
                        "name": "Default Organization",
                        "slug": unique_slug,
                    }
                )
                org_id = default_org.id
                logger.info(f"Created default organization: {org_id} with slug: {unique_slug}")
        else:
            # Validate that org_id exists in database
            existing_org = await prisma.organization.find_unique(where={"id": org_id})
            if not existing_org:
                logger.warning(f"Organization {org_id} does not exist. Creating default organization...")
                # Create a default organization with unique slug using utility function
                unique_slug = await generate_slug("Default Organization")
                default_org = await prisma.organization.create(
                    data={
                        "name": "Default Organization",
                        "slug": unique_slug,
                    }
                )
                org_id = default_org.id
                logger.info(f"Created default organization: {org_id} with slug: {unique_slug}")
        
        # Validate user_id - ensure it exists in database
        if not is_valid_uuid(user_id):
            logger.warning(f"Invalid user_id format: {user_id}. Creating user record...")
            # Create a user record with the org_id
            try:
                new_user = await prisma.user.create(
                    data={
                        "id": str(uuid.uuid4()),
                        "org_id": org_id,
                        "email": user_id if "@" in user_id else f"{user_id}@temp.local",
                        "name": "Temporary User",
                    }
                )
                user_id = new_user.id
                logger.info(f"Created user: {user_id}")
            except Exception as e:
                logger.error(f"Failed to create user: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid user_id format and could not create user: {user_id}"
                )
        else:
            # Validate that user_id exists in database, create if not
            existing_user = await prisma.user.find_unique(where={"id": user_id})
            if not existing_user:
                logger.warning(f"User {user_id} does not exist. Creating user record...")
                try:
                    new_user = await prisma.user.create(
                        data={
                            "id": user_id,
                            "org_id": org_id,
                            "email": f"user-{user_id[:8]}@temp.local",
                            "name": "Temporary User",
                        }
                    )
                    logger.info(f"Created user: {user_id}")
                except Exception as e:
                    logger.error(f"Failed to create user: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not create user record: {str(e)}"
                    )
        
        # Validate client_id if provided
        if client_id and not is_valid_uuid(client_id):
            logger.warning(f"Invalid client_id format: {client_id}, setting to None")
            client_id = None
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an audio file"
            )
        
        # Save uploaded file
        temp_file_path = save_uploaded_file(file)
        
        # Create Meeting record with initial status
        meeting = await prisma.meeting.create(
            data={
                "id": meeting_id,
                "org_id": org_id,
                "user_id": user_id,
                "client_name": client_name,
                "client_id": client_id,
                "status": "PENDING",
                "audio_url": temp_file_path,  # Temporary path for now
            }
        )
        
        logger.info(f"Created meeting record: {meeting_id}")
        
        # Step 1: Transcribe audio with fallback (includes normalization, OpenAI/Gemini, status updates, usage tracking)
        try:
            transcription_result = await transcribe_audio_with_fallback(
                file_path=temp_file_path,
                meeting_id=meeting_id,
                org_id=org_id,
                language="he"
            )
            
            transcript = transcription_result.get("transcript", "")
            raw_value = transcription_result.get("transcript_raw")
            transcript_raw = _normalize_transcript_raw(raw_value)
            duration = transcription_result.get("duration")
            detected_language = transcription_result.get("language", "he")
            provider = transcription_result.get("provider", "unknown")
            
            # Detect language mix
            language_mix = detect_language_mix(transcript) if transcript else None
            
            # Update meeting with transcript (status already updated by transcription_service)
            try:
                # Wrap transcript_raw with Json() for Prisma JSON field type safety
                transcript_raw_wrapped = Json(transcript_raw) if transcript_raw is not None else None
                
                await prisma.meeting.update(
                    where={"id": meeting_id},
                    data={
                        "transcript": transcript,
                        "transcript_raw": transcript_raw_wrapped,
                        "duration_seconds": int(duration) if duration else None,
                        "language_mix": language_mix,
                        # Status is already set to COMPLETED by transcription_service
                    }
                )
            except Exception as db_error:
                logger.error(
                    "Failed to update meeting %s with transcript. "
                    "Types: transcript_raw=%s (%s)",
                    meeting_id,
                    transcript_raw,
                    type(transcript_raw),
                    exc_info=True,
                )
                raise
            
            logger.info(f"Transcription completed for meeting: {meeting_id} (provider: {provider})")
        
        except Exception as e:
            await log_processing_error(meeting_id, e, "transcription")
            await prisma.meeting.update(
                where={"id": meeting_id},
                data={"status": "FAILED"}
            )
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {str(e)}"
            )
        
        # Step 2: Generate summary
        try:
            summary = await generate_summary(
                transcript=transcript,
                meeting_id=meeting_id,
                org_id=org_id,
                rep_id=user_id,
                client_id=client_id,
                duration=int(duration) if duration else None,
                language_mix=language_mix
            )
            
            # Convert summary to dict for JSON storage
            summary_dict = summary.model_dump()
            
            # Update meeting with summary
            # Wrap summary_dict with Json() for Prisma JSON field type safety
            await prisma.meeting.update(
                where={"id": meeting_id},
                data={
                    "summary": Json(summary_dict),
                    "summary_text": summary.content.summary_text if hasattr(summary, "content") else None,
                    "confidence_score": summary.governance.confidence_score if hasattr(summary, "governance") else None,
                    "status": "COMPLETED",
                }
            )
            
            logger.info(f"Summary generated for meeting: {meeting_id}")
        
        except Exception as e:
            await log_processing_error(meeting_id, e, "summary_generation")
            # Don't fail the request, just log the error
            logger.error(f"Summary generation failed for meeting {meeting_id}: {str(e)}")
            summary = None
        
        # Clean up temporary file
        cleanup_temp_file(temp_file_path)
        
        # Return response
        return MeetingUploadResponse(
            meeting_id=meeting_id,
            status="success" if summary else "partial",
            message="Meeting processed successfully" if summary else "Transcription completed, but summary generation failed",
            transcript=transcript,
            summary=summary
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Log error
        if meeting_id:
            await log_processing_error(meeting_id, e, "upload")
            try:
                await prisma.meeting.update(
                    where={"id": meeting_id},
                    data={"status": "FAILED"}
                )
            except:
                pass
        
        # Clean up temp file if it exists
        if temp_file_path:
            cleanup_temp_file(temp_file_path)
        
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process meeting: {str(e)}"
        )


@router.get("", response_model=List[MeetingResponse])
async def get_meetings(org_id: str, user_id: Optional[str] = None):
    """
    Get all meetings for an organization.
    
    SECURITY: This endpoint strictly filters by org_id. No cross-tenant data access.
    
    In development mode, if no meetings found and DEV_ORG_ID is set, it will use that.
    In production, this will be replaced with Auth middleware that extracts org_id from JWT.
    """
    try:
        # DEBUG: Print org_id being searched
        print(f"DEBUG: Searching for meetings with org_id: {org_id}")
        logger.info(f"Fetching meetings for org_id: {org_id}, user_id: {user_id}")
        
        # SECURITY: Always filter by org_id - no global fetches
        meetings = await prisma.meeting.find_many(
            where={"org_id": org_id},
        )
        print(f"DEBUG: Found {len(meetings)} meetings for org_id: {org_id}")
        
        # If no meetings found and user_id is provided, try to find user's actual org_id
        # This is a development convenience - in production, org_id comes from JWT
        if len(meetings) == 0 and user_id:
            logger.info(f"No meetings found for org_id {org_id}, trying to find user's org_id...")
            try:
                user = await prisma.user.find_unique(where={"id": user_id})
                if user and user.org_id:
                    logger.info(f"Found user's org_id: {user.org_id}, fetching meetings...")
                    meetings = await prisma.meeting.find_many(
                        where={"org_id": user.org_id},
                    )
                    logger.info(f"Found {len(meetings)} meetings for user's org_id")
            except Exception as user_err:
                logger.warning(f"Failed to find user's org_id: {str(user_err)}")
        
        # DEV_ONLY_WARNING: Development fallback using DEV_ORG_ID from environment
        # This ensures consistent org_id during development testing.
        # MUST be removed before production - replace with proper Auth middleware.
        if len(meetings) == 0 and settings.dev_org_id:
            logger.warning(
                f"DEV_ONLY: No meetings found for org_id {org_id} and user_id {user_id}. "
                f"Using DEV_ORG_ID from environment: {settings.dev_org_id}"
            )
            meetings = await prisma.meeting.find_many(
                where={"org_id": settings.dev_org_id},
            )
            logger.info(f"DEV_ONLY: Found {len(meetings)} meetings for DEV_ORG_ID")
        
        # SECURITY: Never return meetings from multiple orgs - if we found meetings,
        # verify they all belong to the requested org_id
        if meetings:
            mismatched_orgs = [m for m in meetings if m.org_id != org_id]
            if mismatched_orgs:
                logger.error(
                    f"SECURITY VIOLATION: Found {len(mismatched_orgs)} meetings with mismatched org_id. "
                    f"Requested: {org_id}, Found: {[m.org_id for m in mismatched_orgs]}"
                )
                # Filter out mismatched meetings
                meetings = [m for m in meetings if m.org_id == org_id]
        
        # TEMPORARY DEBUG FALLBACK - DEV_ONLY: Fetch last 5 meetings to prove DB connection
        if len(meetings) == 0:
            logger.warning(
                f"DEBUG: No meetings found for org_id: {org_id}, user_id: {user_id}. "
                "Fetching last 5 meetings regardless of org_id to verify DB connection..."
            )
            print(f"DEBUG: No meetings found for org_id {org_id}. Fetching last 5 meetings from DB...")
            # TEMPORARY: Fetch last 5 meetings to prove DB is working
            try:
                # Fetch all meetings and take last 5 (Prisma Python doesn't support order in find_many)
                all_meetings_raw = await prisma.meeting.find_many(take=10)
                # Sort by created_at descending and take first 5
                all_meetings = sorted(all_meetings_raw, key=lambda m: m.created_at or datetime.min, reverse=True)[:5]
                print(f"DEBUG: Found {len(all_meetings)} total meetings in database (last 5)")
                if all_meetings:
                    sample_org_ids = [m.org_id for m in all_meetings]
                    logger.warning(f"DEBUG: Database has {len(all_meetings)} meetings. Sample org_ids: {sample_org_ids}")
                    print(f"DEBUG: Sample org_ids in DB: {sample_org_ids}")
                else:
                    logger.warning("DEBUG: Database is empty - no meetings exist at all.")
                    print("DEBUG: Database is empty - no meetings exist at all.")
            except Exception as db_err:
                logger.error(f"DEBUG: Failed to fetch meetings from DB: {str(db_err)}")
                print(f"DEBUG: Failed to fetch meetings from DB: {str(db_err)}")
            
            logger.info(
                f"No meetings found for org_id: {org_id}, user_id: {user_id}. "
                "This is expected if the organization has no meetings yet."
            )
        
        logger.info(f"Returning {len(meetings)} meetings for org_id: {org_id}")
        # Convert Prisma models to Pydantic response models (handles JSON fields flexibly)
        return [MeetingResponse.model_validate(meeting) for meeting in meetings]
    except Exception as e:
        logger.error(f"Error fetching meetings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {str(e)}")


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: str, org_id: Optional[str] = None):
    """
    Get meeting details by ID.
    
    SECURITY: In production, org_id will come from Auth middleware (JWT token).
    Currently accepts org_id as query parameter for development.
    
    TODO: Replace org_id parameter with Auth middleware dependency.
    """
    try:
        # SECURITY: Always filter by org_id if provided
        # TODO: Replace with Auth middleware that extracts org_id from JWT
        where_clause = {"id": meeting_id}
        if org_id:
            where_clause["org_id"] = org_id
            logger.info(f"Fetching meeting {meeting_id} for org_id: {org_id}")
        else:
            logger.warning(
                f"SECURITY WARNING: get_meeting called without org_id filter. "
                f"This should only happen in development. Meeting ID: {meeting_id}"
            )
        
        meeting = await prisma.meeting.find_unique(
            where=where_clause,
            include={
                "organization": True,
                "user": True,
            }
        )
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # SECURITY: Double-check org_id match if org_id was provided
        if org_id and meeting.org_id != org_id:
            logger.error(
                f"SECURITY VIOLATION: Meeting {meeting_id} belongs to org {meeting.org_id}, "
                f"but request specified org {org_id}. Access denied."
            )
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert Prisma model to Pydantic response model (handles JSON fields flexibly)
        return MeetingResponse.model_validate(meeting)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching meeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
