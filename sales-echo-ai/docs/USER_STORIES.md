# SalesEcho AI - User Stories

## Overview
This document contains detailed user stories for SalesEcho AI, each with context, acceptance criteria, and technical considerations.

---

## Story #1: The Field Record (Offline & Mobile)

### Story
**As a** field sales rep (Yossi)  
**I want to** record a 60-sec voice note immediately after a meeting, even without internet  
**So that** I don't forget key details while they're fresh in my mind

### Context
Field sales reps often conduct meetings in locations with poor or no internet connectivity (conference rooms, client offices, outdoor venues). The ability to record immediately after a meeting is critical for capturing accurate information before memory fades.

### Acceptance Criteria
- ✅ Mobile-first UI with prominent record button
- ✅ Record button works instantly (no loading delay)
- ✅ Local storage queue for offline recordings
- ✅ Automatic sync when internet connection is restored
- ✅ Push notification when the summary is ready
- ✅ Visual indicator showing queued recordings count
- ✅ Error handling for storage quota exceeded

### Technical Notes
- Use React Native's AsyncStorage or SQLite for local queue
- Implement background sync service
- Queue metadata: timestamp, file size, meeting context (client name, location)

---

## Story #2: The Quick Edit (Tachles Style)

### Story
**As a** Sales Manager (Liat)  
**I want to** click and edit any AI-generated field  
**So that** I can correct mistakes (e.g., deal value, dates) before syncing to CRM

### Context
AI extraction is not 100% accurate. Sales managers need a fast, intuitive way to review and correct AI-generated summaries before they enter the CRM system. The "Tachles" (direct, no-fluff) style emphasizes speed and efficiency.

### Acceptance Criteria
- ✅ Every summary field is an inline-editable input
- ✅ High/Low confidence indicators (color-coded: green ≥0.7, yellow 0.5-0.7, red <0.5)
- ✅ One-click save (no separate "Save" button needed)
- ✅ Edits are logged to `corrections` table for AI feedback loops
- ✅ Auto-save after 2 seconds of inactivity
- ✅ Undo/Redo functionality
- ✅ Visual diff showing what changed

### Technical Notes
- Use React's contentEditable or controlled inputs
- Track field_path for nested JSON fields
- Store old_value and new_value in corrections table
- Confidence score displayed as badge next to each field

---

## Story #3: Smart CRM Matching

### Story
**As a** sales rep  
**I want to** have the system automatically find the correct Deal/Contact in HubSpot  
**So that** I don't create duplicates or sync to the wrong record

### Context
Sales reps often work with existing clients and deals. Manually searching for the right CRM record is time-consuming and error-prone. The system should intelligently match meeting data to existing CRM entities.

### Acceptance Criteria
- ✅ Search by Name/Email/Company in HubSpot
- ✅ If multiple deals exist, prompt for selection with preview cards
- ✅ If none found, offer 'Create New Deal' button
- ✅ Fuzzy matching for name variations (e.g., "John Smith" vs "J. Smith")
- ✅ Display deal stage, value, and last activity date in selection UI
- ✅ Remember user's selection for future meetings with same client

### Technical Notes
- Use HubSpot Search API (v3) for entity search
- Implement fuzzy matching algorithm (Levenshtein distance)
- Cache recent matches in local storage
- Store matched CRM entity ID in `meeting.client_id`

---

## Story #4: Manager's Bird's Eye View

### Story
**As a** Sales Manager  
**I want to** see a dashboard showing team activity (calls recorded, deal sizes, overdue follow-ups)  
**So that** I can coach effectively and identify bottlenecks

### Context
Sales managers need visibility into team performance and activity. They need to quickly identify reps who need support, deals that are stuck, and follow-ups that are overdue.

### Acceptance Criteria
- ✅ Filter by Rep/Status/Value/Date Range
- ✅ Red alerts for missing CRM updates (>3 days since meeting)
- ✅ Direct link to full meeting summaries from dashboard
- ✅ Summary cards showing: Total calls, Total deal value, Average confidence score
- ✅ Timeline view of team activity
- ✅ Export to CSV functionality
- ✅ Real-time updates (WebSocket or polling)

### Technical Notes
- Aggregate queries on `meetings` table filtered by `org_id`
- Use Prisma aggregation functions for statistics
- Implement pagination for large datasets
- Cache dashboard data with 5-minute TTL

---

## Story #5: Explainability (Source Proof)

### Story
**As a** sales rep  
**I want to** see exactly why the AI extracted a specific date or value  
**So that** I can trust the output and verify accuracy

### Context
Trust in AI systems requires transparency. Sales reps need to see the source evidence for every extracted entity to verify correctness and build confidence in the system.

### Acceptance Criteria
- ✅ Clicking a field highlights the specific transcript snippet
- ✅ Displays confidence score (0.0-1.0) with color coding
- ✅ Shows timestamp in audio (if available)
- ✅ Displays language detection (he/en/he-en) for the snippet
- ✅ "Show Source" button on every extracted entity
- ✅ Side-by-side view: transcript on left, extracted data on right

### Technical Notes
- Store `source` field in every extracted entity (from System Prompt v2.0)
- Use transcript_raw JSON for timestamp mapping
- Implement text highlighting with scroll-to functionality
- Store character offsets for precise snippet extraction

---

## Story #6: Heblish Mastery

### Story
**As a** high-tech sales rep  
**I want to** speak in a mix of Hebrew and English (e.g., 'The deployment was successful')  
**So that** the AI transcribes it perfectly without "gibberish"

### Context
Israeli tech sales reps frequently code-switch between Hebrew and English, especially when discussing technical terms, product names, or international clients. The system must handle this naturally.

### Acceptance Criteria
- ✅ No 'gibberish' in technical terms (e.g., "API", "deployment", "SaaS")
- ✅ Consistent spelling for English terms within Hebrew sentences
- ✅ Proper capitalization for proper nouns and acronyms
- ✅ Handles common tech terms: API, SDK, CRM, B2B, etc.
- ✅ Language mix detection: "he-IL/en-US" in metadata
- ✅ Transcript preserves original language mix

### Technical Notes
- Use OpenAI Whisper with language="he" but allow auto-detection
- Post-process transcript to normalize common tech terms
- Store language_mix in meeting record
- System Prompt v2.0 includes Heblish optimization rules

---

## Story #7: Mono-Recording Speaker Separation (Diarization)

### Story
**As a** manager reviewing mobile/PBX recordings (Mono files)  
**I want to** see a clear separation between 'Rep' and 'Client'  
**So that** I can attribute action items to the correct party

### Context
Many recordings come from mobile phones or PBX systems that produce mono audio files. Speaker diarization is essential for understanding who said what and correctly attributing action items.

### Acceptance Criteria
- ✅ AI-based speaker signatures (Speaker 1, Speaker 2)
- ✅ Attribution of action items to the correct party
- ✅ Visual timeline showing speaker segments
- ✅ Label assignment: "Rep" vs "Client" (user can correct)
- ✅ Works with mono audio files (no stereo requirement)
- ✅ Minimum 2 speakers detected, maximum 4 speakers

### Technical Notes
- Use AssemblyAI or similar service for speaker diarization
- Store speaker segments in `transcript_raw` JSON
- Map action items to speaker IDs
- Allow manual correction of speaker labels
- Fallback: If diarization fails, prompt user to identify speakers

---

## Story #8: Privacy & Zero-Retention

### Story
**As a** CISO  
**I want to** have audio files deleted permanently after the JSON summary is generated  
**So that** we comply with privacy laws (GDPR, Israeli Privacy Law)

### Context
Audio recordings contain sensitive personal information. Many organizations require zero-retention policies where audio is deleted immediately after processing to minimize data exposure.

### Acceptance Criteria
- ✅ Automated 'Delete on Finish' flag (configurable per org)
- ✅ Success logs for deletion in `audio_deleted_at` field
- ✅ Data isolation via RLS (org_id filtering)
- ✅ Configurable retention policy (default: 24 hours, max: 7 days)
- ✅ Audit trail showing when audio was deleted
- ✅ Option to extend retention for specific meetings (with approval)

### Technical Notes
- Use `audio_deletion_scheduled_at` and `retention_policy_hours` in Meeting model
- Background job to delete audio files from S3/storage
- Store deletion confirmation in `audio_deleted_at` timestamp
- RLS policies ensure org-level isolation
- Log deletion events to audit trail

---

## Story #9: New Lead Discovery

### Story
**As a** sales rep at a conference  
**I want to** have the AI detect new emails/names in my voice note  
**So that** I can create a CRM contact from scratch with one click

### Context
Sales reps often meet new prospects at conferences, trade shows, or networking events. They need to quickly capture contact information from voice notes and create CRM records without manual data entry.

### Acceptance Criteria
- ✅ Entity extraction (Name, Email, Company) from transcript
- ✅ CRM existence check (search by email/name)
- ✅ 'One-Click Create' button if contact doesn't exist
- ✅ Pre-filled form with extracted data (user can edit)
- ✅ Confidence score for each extracted entity
- ✅ Batch creation for multiple contacts in one meeting

### Technical Notes
- Use GPT-4o entity extraction from System Prompt v2.0
- Store entities in `crm_entities` section of summary
- HubSpot API: POST /crm/v3/objects/contacts
- Validate email format before creation
- Store created contact ID in `meeting.client_id`

---

## Story Priority Matrix

| Story | Priority | Complexity | Dependencies |
|-------|----------|------------|--------------|
| #1: Field Record | P0 | Medium | Module 5 (Mobile) |
| #2: Quick Edit | P0 | Low | Module 3 (UI) |
| #3: CRM Matching | P1 | Medium | Module 4 (CRM Sync) |
| #4: Manager Dashboard | P1 | High | Module 3, Module 7 |
| #5: Explainability | P0 | Low | Module 2 (AI Pipeline) |
| #6: Heblish | P0 | Low | Module 2 (AI Pipeline) |
| #7: Diarization | P1 | High | Module 2 (AI Pipeline) |
| #8: Zero-Retention | P0 | Medium | Module 1 (Schema) |
| #9: New Lead Discovery | P1 | Medium | Module 2, Module 4 |

---

## Implementation Notes

- All stories require multi-tenancy enforcement (org_id filtering)
- Stories #1, #5, #6, #8 are already partially implemented in Module 2
- Stories #2, #3, #4, #9 require Module 3 (UI) and Module 4 (CRM)
- Story #7 requires additional AI service integration (AssemblyAI or similar)
