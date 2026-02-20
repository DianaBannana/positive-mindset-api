"""
Centralized prompts registry for SalesEcho AI.

This module defines reusable, versioned prompt strings used across the
AI pipeline (Gemini STT/LLM, Tachles summaries, CRM insights, etc.).

Keeping prompts here ensures:
- Single source of truth for business/LLM logic
- Easier experimentation and versioning
- Clear separation between infrastructure and prompt design
"""

# ============================================
# Sales Insights Prompts (Hebrew)
# ============================================

SALES_INSIGHTS_PROMPT_HE: str = """
אתה מומחה לניתוח שיחות מכירה וניהול קשרי לקוחות (CRM). התפקיד שלך הוא לנתח את שיחת האודיו המצורפת ולהפיק סיכום עסקי חד, תמציתי ומכוון פעולה בעברית.

מבנה הסיכום הנדרש:
1. תמצית המפגש: (2-3 משפטים).
2. נקודות מרכזיות שעלו: (רשימת בולטים).
3. התנגדויות לקוח: (זיהוי חששות, מחיר, לו"ז וכו').
4. משימות להמשך (Action Items): (מי עושה מה ומתי).
5. ציון "חום" עסקה: (1-10 עם הסבר קצר).

דגשים:
- כתוב בשפה עסקית וישירה.
- ציין סכומים ותאריכים במדויק.
- הפלט חייב להיות בעברית.
"""

