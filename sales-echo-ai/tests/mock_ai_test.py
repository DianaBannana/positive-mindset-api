import asyncio
import json
import uuid
from datetime import datetime
from app.core.database import prisma  # ודאי שהנתיב ל-Prisma Client נכון
from prisma import Json

# 1. נתוני דמה (Mock) לפי Prompt v2.0
MOCK_TRANSCRIPT = """
נציג: שלום דנה, כאן יוסי מאלטא. לגבי הפרויקט ב-Gan Yavne, אנחנו מדברים על 50,000 ש"ח.
לקוחה: זה נשמע הוגן. מתי מתחילים?
נציג: יום ראשון הבא בבוקר. אני אשלח לך סיכום ב-WhatsApp.
"""

MOCK_AI_JSON = {
    "summary": 'סיכום פרויקט אלטא בגן יבנה. עלות מוערכת: 50,000 שח. תחילת עבודה ביום ראשון.',
    "action_items": [
        {"task": "שליחת סיכום ב-WhatsApp", "assignee": "נציג", "due_date": "2026-02-15"}
    ],
    "entities": {
        "deal_value": 50000,
        "currency": "ILS",
        "next_meeting": "2026-02-15",
        "pain_points": ["צורך בתיעוד מסודר"]
    },
    "confidence_scores": {
        "summary": 0.98,
        "deal_value": 0.95
    },
    "source_quotes": ['50,000 ש"ח', "יום ראשון הבא"],  # Fixed: Use single quotes for outer string
    "requires_review": False
}

# 2. פונקציית הבדיקה
async def run_mock_test():
    print("🚀 Starting Local Pipeline Test (Mocking OpenAI)...")
    
    # מזהים קבועים מה-Seed שלנו
    org_id = "123e4567-e89b-12d3-a456-426614174000"
    user_id = "789e0123-e45b-67c8-d901-234567890abc"
    
    try:
        # התחברות לבסיס הנתונים
        await prisma.connect()
        print("🔗 Database connected.")

        # דימוי השמירה ל-DB (כאילו OpenAI כבר החזיר תשובה)
        # שימי לב: אנחנו בודקים כאן שה-Schema מקבלת את ה-JSON שלנו
        new_meeting = await prisma.meeting.create(
            data={
                "id": str(uuid.uuid4()),
                "org_id": org_id,
                "user_id": user_id,
                "client_name": "Elta Test Client",
                "transcript": MOCK_TRANSCRIPT,
                "summary": Json(MOCK_AI_JSON),  # Use Prisma.Json wrapper for JSON fields
                "summary_text": MOCK_AI_JSON["summary"],
                "status": "processed",  # Use lowercase status matching schema
                "language_mix": "he-IL/en-US",
                "confidence_score": 0.95
                # created_at is auto-generated, don't pass it
            }
        )
        
        print(f"✅ SUCCESS! Meeting created with ID: {new_meeting.id}")
        print(f"📊 Summary stored correctly in JSON format.")

    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        print("\n💡 Tip: Check if your Prisma schema matches the field names above.")
    
    finally:
        await prisma.disconnect()
        print("🔌 Database disconnected.")

if __name__ == "__main__":
    asyncio.run(run_mock_test())