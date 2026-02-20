"""
AI Pipeline Integration Test
Tests the complete transcription service with fallback logic (OpenAI → Gemini 1.5 Flash)
Includes audio normalization, transcription, usage tracking, and status updates.
"""

import asyncio
import os
from dotenv import load_dotenv
from app.services.transcription_service import transcribe_audio_with_fallback
from app.core.database import prisma

load_dotenv()


async def test_ai_pipeline():
    """
    Run integration test for the complete AI pipeline.
    
    Tests:
    - Audio normalization (FFmpeg)
    - Primary transcription (OpenAI Whisper v3)
    - Fallback transcription (Gemini 1.5 Flash)
    - Usage tracking (organization.usage_minutes)
    - Status updates (meeting.status)
    - Error logging (meeting.processing_errors)
    """
    await prisma.connect()
    
    try:
        # Test audio file path (should be in project root)
        audio_path = 'test_audio.mp3.m4a'
        
        if not os.path.exists(audio_path):
            print(f'❌ Error: Audio file {audio_path} not found in project root.')
            print('   Please ensure test_audio.mp3.m4a exists in the project root directory.')
            return
        
        # Fetch test organization
        org = await prisma.organization.find_first()
        if not org:
            print('❌ Error: No organization found in database.')
            print('   Please ensure migrations have been run and at least one organization exists.')
            return
        
        # Fetch test user
        user = await prisma.user.find_first(where={"org_id": org.id})
        if not user:
            print('❌ Error: No user found in database.')
            print('   Please ensure at least one user exists for the organization.')
            return
        
        # Create test meeting
        meeting = await prisma.meeting.create(
            data={
                'org_id': org.id,
                'user_id': user.id,
                'client_name': 'AI Pipeline Test Client',
                'status': 'PENDING'
            }
        )
        
        print('=' * 60)
        print('🧪 AI Pipeline Integration Test')
        print('=' * 60)
        print(f'📁 Audio File: {audio_path}')
        print(f'🏢 Organization: {org.name} ({org.id})')
        print(f'👤 User: {user.id}')
        print(f'📋 Meeting ID: {meeting.id}')
        print('---')
        print('🔄 Starting pipeline: Normalization → Transcription → Summary')
        print('   (Will fallback to Gemini 1.5 Flash if OpenAI fails)')
        print('---')
        
        try:
            # Execute transcription service
            # Signature: transcribe_audio_with_fallback(file_path, meeting_id, org_id, language="he")
            result = await transcribe_audio_with_fallback(
                file_path=audio_path,
                meeting_id=meeting.id,
                org_id=org.id,
                language="he"
            )
            
            print('\n✅ Pipeline completed successfully!')
            print('=' * 60)
            print('📊 Results:')
            print('---')
            
            # Display transcript preview
            transcript = result.get("transcript", "")
            if transcript:
                preview = transcript[:200] + "..." if len(transcript) > 200 else transcript
                print(f'📝 Transcript Preview: {preview}')
            else:
                print('📝 Transcript: Not available')
            
            # Display provider info
            provider = result.get("provider", "unknown")
            print(f'🌐 Provider: {provider}')
            
            # Display duration
            duration = result.get("duration", 0)
            if duration:
                print(f'⏱️  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)')
            else:
                print('⏱️  Duration: Not available')
            
            # Display speakers
            speakers = result.get("speakers", [])
            if speakers:
                print(f'🗣️  Speakers Detected: {", ".join(speakers)}')
            else:
                print('🗣️  Speakers: None detected')
            
            # Display language
            language = result.get("language", "unknown")
            print(f'🌍 Language: {language}')
            
            print('---')
            
            # Fetch updated meeting from database
            updated_meeting = await prisma.meeting.find_unique(where={"id": meeting.id})
            if updated_meeting:
                print('📋 Database Status:')
                print(f'   Status: {updated_meeting.status}')
                if updated_meeting.duration_seconds:
                    print(f'   Duration (seconds): {updated_meeting.duration_seconds}')
                if updated_meeting.language_mix:
                    print(f'   Language Mix: {updated_meeting.language_mix}')
                
                # Check for processing errors
                if updated_meeting.processing_errors:
                    print(f'   ⚠️  Processing Errors: {updated_meeting.processing_errors}')
                else:
                    print('   ✅ No processing errors')
            
            # Fetch updated organization for usage tracking
            updated_org = await prisma.organization.find_unique(where={"id": org.id})
            if updated_org:
                print(f'   Usage Minutes (Organization): {updated_org.usage_minutes:.2f} minutes')
            
            print('---')
            print('✅ Test completed successfully!')
            print('=' * 60)
            
        except Exception as e:
            print(f'\n❌ Pipeline test failed: {str(e)}')
            print('=' * 60)
            import traceback
            traceback.print_exc()
            
            # Check for errors in database
            updated_meeting = await prisma.meeting.find_unique(where={"id": meeting.id})
            if updated_meeting and updated_meeting.processing_errors:
                print('\n📋 Processing Errors Logged:')
                print(updated_meeting.processing_errors)
            
            print('=' * 60)
                
    finally:
        await prisma.disconnect()
        print('\n🔌 Disconnected from database')


if __name__ == '__main__':
    asyncio.run(test_ai_pipeline())
