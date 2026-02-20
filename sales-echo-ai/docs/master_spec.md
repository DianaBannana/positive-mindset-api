



סיכום שיחה:
"דף הסבר" (Context) שמתאר לא רק את הטכנולוגיה, אלא את הכוונה העסקית שעמדה מאחורי ההחלטות שלנו.
הנה סיכום התהליך שעברנו והתוצרים הסופיים:
📝 סיכום תהליך האפיון: SalesEcho AI
1. המטרה (The Mission)
יצירת כלי עבודה לאנשי מכירות (שטח וטלפוניה) שפותר את "צוואר הבקבוק" של תיעוד פגישות. המטרה הייתה לבנות מערכת שהיא לא רק "מתמללת", אלא מנוע נתונים שיודע להזין את ה-CRM באופן אוטומטי תוך שמירה על רמת אבטחה של ארגונים גדולים (Enterprise-Ready).
2. מה ניסינו להשיג? (Objectives)
מינימום חיכוך (Low Friction): איש מכירות לא צריך להקליד. הוא מדבר (Debrief) או שהמערכת מאזינה, והנתונים נשלפים לבד.
אמינות גבוהה (Trust): בניית מנגנון "אישור אנושי" (Review Card) כך שאיש המכירות הוא הפוסק האחרון לפני שהמידע נכנס ל-CRM.
מוכנות לארגונים (Scalability): התייחסות למודלים של עלויות (Token Caps), בידוד נתונים בין לקוחות (Multi-tenancy), ואבטחה (KMS, Audit Logs).
פיתוח מהיר: אפיון ברמת פירוט שמאפשר לכלי AI (כמו Cursor) לכתוב את רוב הקוד במינימום טעויות.
3. התוצרים העיקריים שנוצרו (Deliverables)
א. מסמך אפיון דרישות (PRD)
מסמך המתאר "מה המוצר עושה". הוא כולל:
מסעות משתמש (User Journeys) לסוגי מכירות שונים.
הגדרת גבולות (Scope) – מה המוצר לא עושה (חשוב מאוד למניעת בזבוז זמן פיתוח).
מדיניות כשלים (Failure Policy) וטיפול ב"הזיות" של ה-AI.
ב. מסמך ארכיטקטורה טכנית (TAD)
מסמך המתאר "איך המוצר בנוי". הוא כולל:
Stack טכנולוגי: PostgreSQL, FastAPI, OpenAI/Gemini, React Native.
AI Pipeline: שלבי העיבוד מתמלול ועד אימות (Verification).
Data Contract: מבנה JSON אחיד שמהווה את שפת המשותפת בין כל חלקי המערכת.
Governance: ניהול גרסאות מודלים ו-Feature Flags.
ג. תוכנית עבודה מודולרית (Implementation Plan)
חלוקת הפרויקט ל-8 מודלים (0 עד 7) המאפשרת פיתוח מדורג ובריא:
תשתית ושלד (Boilerplate).
בסיס נתונים (Schema).
ליבת ה-AI (Pipeline).
ממשק משתמש (UI).
אינטגרציות (CRM).
מובייל.
אבטחה וניהול (Auth/Admin).
4. נקודות מפתח להצלחה (Takeaways)
ה-System Prompt: יצרנו הנחיה חכמה שמוציאה נתונים מובנים עם ציוני ביטחון (Confidence) והסברים (Explainability).
בידוד (Isolation): הקפדנו על ארכיטקטורה שבה כל ארגון מופרד לחלוטין ברמת הנתונים.
חיסכון בעלויות: הכנסנו מנגנוני בקרה על צריכת ה-AI כבר בשלב האפיון.
5. קבצים מעודכנים (Copy-Paste Ready)
מכיוון שאני AI, אני לא יכול לשלוח קובץ ZIP פיזי, אבל ריכזתי לך כאן את הכל כטקסט רציף. את יכולה להעתיק את הבלוק הבא ולשמור אותו כקובץ master_spec.md:
Markdown

# SALES ECHO AI - MASTER SPECIFICATION## [SECTION 1: PRD]- Focus: Call-to-CRM Automation.- Goal: Human-in-the-loop validation of AI summaries.- Scope: Mobile Debrief, Phone Streaming, Zoom/Teams.- RACI: Sales Rep is accountable for data accuracy.## [SECTION 2: TAD]- Backend: FastAPI/Node.js.- DB: PostgreSQL + Redis.- AI: Whisper (STT) + GPT-4o/Gemini 1.5 (LLM).- Contract: Structured JSON with meta, content, entities, and governance.## [SECTION 3: IMPLEMENTATION MODULES]0. Boilerplate (FastAPI/Node)1. Schema (Prisma/RLS)2. AI Pipeline (STT/LLM/Verify)3. Review Card UI (React/Tailwind)4. CRM Sync (Hubspot OAuth)5. Mobile (React Native)6. Auth & API Gateway7. Admin Dashboard & Billing



תוצר:
Master Specification
📄 SalesEcho AI - Master Specification (PRD + TAD)
1. Product Requirements (PRD)
1.1 Vision
A Call-to-CRM automation tool that eliminates manual data entry for sales reps by summarizing meetings and syncing structured data to CRMs with a human-in-the-loop approval process.
1.2 Core Features (P0)
Multi-Channel Input: Mobile debrief (voice), Phone streaming, Video bot.
AI Engine: Bilingual STT (Heb/Eng), Diarization, Entity/Task extraction.
Review Card UI: Quick approval interface with source offsets (Explainability).
CRM Integration: Two-way sync with HubSpot and Salesforce.
1.3 Scope Boundaries
Out of Scope: Sales forecasting, automated coaching, real-time scripting.
1.4 Failure & Reliability
Fallback: If primary STT/LLM fails, use secondary provider.
Queueing: Pending syncs during CRM downtime.
Confidence: Scores < 0.8 trigger manual review requirement.
2. Technical Architecture (TAD)
2.1 System Overview
2.2 Tech Stack
Backend: FastAPI (Python) or Node.js (TypeScript).
DB: PostgreSQL (Core) + Redis (Queue/Cache).
AI: OpenAI GPT-4o / Gemini 1.5 Pro + Whisper v3.
Frontend: React (Web Dashboard) + React Native (Mobile).
Auth: Auth0/Clerk with RBAC and Tenant Isolation.
2.3 Data Contract (JSON Schema)
JSON

{
  "summary_id": "uuid",
  "meta": { "org_id": "id", "rep_id": "id", "duration": 120 },
  "content": {
    "summary_text": "string",
    "action_items": [{"task": "string", "due": "date", "confidence": 0.9}],
    "entities": {
      "deal_value": {"value": 15000, "currency": "USD", "confidence": 0.8, "source": "quote"}
    }
  },
  "governance": { "hallucination_check": "passed", "confidence_overall": 0.9 }
}
2.4 Security & Compliance
Zero Retention: Option for immediate audio deletion.
Data Residency: Support for regional storage (IL/US/EU).
Audit Trail: Immutable logs of every CRM write operation.
3. Implementation Roadmap (Cursor Modules)
Module 0: Project Boilerplate (Folders, Env, Middleware). [DONE]
Module 1: Database Schema (Prisma/SQL, Multi-tenancy RLS). [DONE]
Module 2: AI Pipeline (Core) (STT -> Diarization -> LLM -> Verification). [DONE]
Module 3: Review Card UI (Frontend, Edit-in-place, Confidence highlighting).
Module 4: HubSpot Sync (OAuth2, Timeline & Deal update logic).
Module 5: Mobile App (Recording, Offline storage, S3 upload).
Module 6: API Gateway + Auth (JWT, RBAC, SCIM readiness).
Module 7: Admin Dashboard (Cost tracking, AI error budget).
4. System Prompt (The Brain)
"Analyze the transcript between a salesperson and a client. Extract a 2-3 sentence summary, action items with assignees/due dates, and CRM entities (amounts, dates, emails). For each extracted item, provide a confidence score (0-1) and the exact source snippet from the transcript. Handle Hebrew/English code-switching. Format the output as JSON according to the provided schema."
סיכום תהליך האפיון שלנו:
זיקקנו את הצורך: מעבר מסיכום כללי לניהול נתונים ב-CRM.
הגדרנו את ה-UX: דגש על מובייל ושטח (Debrief) מול דסקטופ (ניהול).
בנינו חוסן (Enterprise): הכנסנו מנגנוני בידוד נתונים, ניהול מודלים, ועלויות.


התוכנית שלSalesEcho AI 
. תוכנית פיתוח בשלבים (מותאמת ל-Cursor)

Cursor הוא הכלי האידיאלי לפרויקט הזה, במיוחד בזכות היכולת שלו לקרוא את כל ה-Context של הפרויקט.

**שלב 1: תשתית ושלד (Module 0 & 1)**

* **פעולה:** הקמת Backend ב-FastAPI וחיבור ל-PostgreSQL עם Prisma.
* **טיפ ל-Cursor:** תני לו את קובץ ה-`master_spec.md` ופשוט תגידי לו: "Initialize a FastAPI project with Prisma and the DB schema defined in the Master Spec. Include Multi-tenancy RLS."

**שלב 2: ליבת ה-AI (Module 2)**

* **פעולה:** מימוש ה-Pipeline: קבלת קובץ קול -> Whisper -> העברת הטקסט ל-LLM עם ה-System Prompt -> הפקת JSON מובנה.
* **דגש:** עבודה עם ה-Data Contract שהגדרתם. זה "חוזה העבודה" של המערכת.

**שלב 3: ה-Review Card וממשק המשתמש (Module 3)**

* **פעולה:** בניית ה-Frontend ב-React. הדגש הוא על עריכה מהירה (Edit-in-place) והצגת ציוני הביטחון (Confidence scores).

**שלב 4: אינטגרציות (Module 4)**

* **פעולה:** חיבור ל-HubSpot/Salesforce. מומלץ להשתמש ב-Webhooks וב-OAuth2.

**שלב 5: מובייל ומערכת ניהול (Module 5-7)**

* **פעולה:** יצירת האפליקציה ב-React Native להקלטה בשטח.

### 3. סוכנים חכמים (Prompts) לעבודה ב-Cursor

כדי ש-Cursor (או סוכני AI אחרים) יכתבו קוד איכותי, השתמשי בפרומפטים הבאים כ-`System Prompts` בתוך ה-Chat או ה-Composer:

#### פרומפט לסוכן הארכיטקטורה (The Architect Agent)

> "You are a Senior Fullstack Architect. Your goal is to implement the SalesEcho AI system based on the provided Master Specification. Follow the Data Contract strictly. Use FastAPI for the backend and React for the frontend. Ensure all code is modular, type-safe (TypeScript/Pydantic), and includes comprehensive error handling for AI API failures."

#### פרומפט לסוכן הבדיקות (The QA & Test Agent)

> "You are an Expert QA Engineer focusing on AI systems. Write unit tests for the AI Pipeline. Create a test suite that simulates 'hallucinations' in the LLM output and verifies that our 'Confidence Score' logic correctly identifies them. Ensure that the CRM sync module has 100% test coverage for edge cases like expired OAuth tokens."

#### פרומפט לסוכן הפרומפטים (Prompt Engineer Agent)

> "You are a Prompt Engineer. Help me refine the 'System Prompt' in the Master Spec. The goal is to maximize the extraction of CRM entities (Deal Value, Dates, Emails) from messy, bilingual (Hebrew-English) transcripts. Ensure the output is always valid JSON and includes source snippets for explainability."







SALES ECHO AI - MASTER SPECIFICATION v3.0 Hebrew-First & Enterprise-Ready Edition1. 
PRODUCT REQUIREMENTS (PRD)1.1 Vision & MissionSalesEcho AI is a "Call-to-CRM" engine designed specifically for the Israeli market. It eliminates manual data entry by converting voice (Mobile Debriefs, Zoom, Phone) into structured CRM data.Primary Focus: Hebrew/English "Heblish" nuance.Value Prop: From "Talking" to "CRM Data" in < 30 seconds.1.2 Core Features (P0)Bilingual STT: High-accuracy Hebrew/English transcription with speaker diarization.Review Card UI (RTL): A specialized interface for sales reps to verify and edit AI summaries before they sync to CRM.Human-in-the-loop: The Sales Rep is the final authority.CRM Sync: Two-way integration with HubSpot/Salesforce.1.3 Israeli-Market OptimizationsHeblish Mastery: Support for technical English terms inside Hebrew sentences.The "Tachles" Summary: AI summaries must be concise, bulleted, and action-oriented (no "fluff").Local Entity Recognition: Detection of ILS (₪), Israeli ID/Company numbers, and local date formats.Context Retention: Automatic retrieval of the last 3 meeting summaries with the client to maintain continuity.2. TECHNICAL ARCHITECTURE (TAD)2.1 Tech StackBackend: FastAPI (Python) - Modular & Async.Database: PostgreSQL (via Supabase/Neon) + Prisma ORM.AI Engine: OpenAI Whisper v3 (STT) + GPT-4o/Gemini 1.5 Pro (LLM).Frontend: React (Web) + React Native (Mobile/Expo).Data Isolation: Multi-tenancy at the Row Level (RLS).2.2 Data Contract (JSON Schema)JSON{
  "summary_id": "uuid",
  "metadata": { 
    "org_id": "id", 
    "rep_id": "id", 
    "client_id": "id", 
    "language_mix": "he-IL/en-US" 
  },
  "content": {
    "summary_text": "Direct, bulleted Hebrew text",
    "action_items": [{"task": "string", "due": "date", "confidence": 0.9}],
    "crm_entities": {
      "deal_value": {"value": 0, "currency": "ILS/USD", "source": "transcript snippet"}
    }
  },
  "governance": { 
    "feedback_loop_applied": false,
    "confidence_score": 0.95 
  }
}
2.3 Security & PrivacyTransitory Storage: Raw audio files are deleted automatically after 24 hours.Audit Trail: Every CRM write operation is logged with a link to the original transcript source.3. IMPLEMENTATION ROADMAP (CURSOR MODULES)ModuleFocusKey DeliverableStatusM0BoilerplateFastAPI structure + RTL support config.[DONE]M1DB SchemaPrisma tables with Multi-tenancy & Feedback Loop.[DONE]M2AI PipelineAudio -> Whisper -> "Tachles" LLM Prompt -> JSON.[DONE]M3Review CardReact UI (RTL) with source-highlighting.In ProgressM4CRM IntegrationHubSpot OAuth & Note/Deal creation logic.PendingM5Feedback EngineTable for storing manual corrections to improve AI accuracy.Pending4. SPECIALIZED AGENT PROMPTS (THE BRAIN)4.1 The Architect (Implementation Lead)"You are a Senior Fullstack Architect. Build the SalesEcho AI foundation. Ensure strict data isolation (Multi-tenancy), modular architecture, and robust error handling. All UI components must support RTL (Right-to-Left) for Hebrew users by default. Use FastAPI and Prisma."4.2 The Prompt Engineer (Hebrew/NLP Expert)"You are an Israeli Sales Operations expert. Refine the system prompt to extract CRM entities from messy, bilingual (Heblish) transcripts.Use 'Tachles' style Hebrew (concise, direct).Recognize Israeli date formats and ILS (₪) currency.Provide a confidence score and the verbatim source quote for every extracted field."4.3 The QA Agent (The Reliability Officer)"You are an Expert QA Engineer. Create test suites that simulate 'Jewish Holiday' context (delays), Hebrew slang, and CRM API timeouts. Ensure the data sync only happens after the 'Human-in-the-loop' flag is true."5. REFINEMENT & LEARNING (FEEDBACK LOOP)The system shall maintain a Correction table. When a user edits an AI-generated field in the Review Card, the original vs. edited version is stored to refine the LLM system prompt in future iterations.