# SalesEcho AI - Product Requirements Document (PRD)

## Version: 2.0
**Last Updated**: 2026-02-12  
**Status**: Active Development

---

## 1. Executive Summary

SalesEcho AI is an enterprise-ready Call-to-CRM automation engine designed for the Israeli market. It converts voice recordings (mobile debriefs, phone calls, Zoom meetings) into structured CRM data with human-in-the-loop validation.

### 1.1 Value Proposition
- **From Voice to CRM in < 30 seconds**: Eliminate manual data entry
- **Hebrew/English Bilingual**: Native support for "Heblish" (code-switching)
- **Enterprise Security**: Multi-tenancy, RLS, zero-retention policies
- **Human-in-the-Loop**: Sales rep is final authority before CRM sync

### 1.2 Target Users
- **Primary**: Field sales reps, Inside sales reps
- **Secondary**: Sales managers, CSOs, CRM administrators
- **Tertiary**: CISO, Compliance officers

---

## 2. Core Features (P0 - Must Have)

### 2.1 Bilingual Speech-to-Text (STT)
- **Provider**: OpenAI Whisper v3
- **Languages**: Hebrew (primary), English, Heblish (mixed)
- **Accuracy**: >95% for clear audio, >85% for noisy environments
- **Speaker Diarization**: Mono file support (2-4 speakers)

### 2.2 Structured AI Summary ("Tachles" Style)
- **Model**: GPT-4o
- **Output Format**: Structured JSON (Data Contract)
- **Content**: Summary text, action items, CRM entities (deal value, dates, emails)
- **Confidence Scores**: 0.0-1.0 for every extracted item
- **Source Quotes**: Exact transcript snippets for explainability

### 2.3 Review Card UI (RTL Support)
- **Framework**: React + Tailwind CSS
- **Features**: Inline editing, confidence indicators, one-click save
- **RTL**: Full Hebrew RTL support
- **Mobile**: Responsive design, touch-optimized

### 2.4 Human-in-the-Loop Validation
- **Approval Workflow**: Sales rep reviews → edits → approves → syncs
- **Feedback Loop**: Corrections logged to `corrections` table for AI improvement
- **Review Flag**: Auto-flag low confidence (<0.7) for mandatory review

### 2.5 CRM Sync (HubSpot/Salesforce)
- **OAuth2**: Secure token storage in `crm_integrations` table
- **Smart Matching**: Auto-find existing deals/contacts
- **Two-way Sync**: Create/update deals, contacts, notes, timeline events
- **Retry Mechanism**: Automatic retry with exponential backoff

### 2.6 Mobile Debrief (Offline-First)
- **Platform**: React Native (Expo)
- **Offline Queue**: Local storage for recordings without internet
- **Auto-Sync**: Background sync when connection restored
- **Push Notifications**: Alert when summary is ready

---

## 3. Technical Constraints

### 3.1 Offline Queueing
- **Requirement**: Mobile app must function without internet
- **Storage**: Local SQLite/AsyncStorage for queued recordings
- **Sync Strategy**: Background job with conflict resolution
- **Queue Limit**: Max 50 recordings per device (configurable)
- **Error Handling**: Retry failed syncs, manual retry option

### 3.2 Usage-Based Billing
- **Metric**: Audio minutes processed per organization
- **Tracking**: `usage_minutes` field in `organizations` table
- **Caps**: Token caps per org (configurable in `settings` JSON)
- **Billing Cycle**: Monthly aggregation
- **Alerts**: 80%, 90%, 100% usage notifications

### 3.3 Data Privacy & Compliance
- **Zero-Retention Policy**: Audio files deleted after processing (configurable)
- **GDPR Compliance**: Right to deletion, data portability
- **Israeli Privacy Law**: Data residency options
- **RLS Enforcement**: Row-level security at database level

### 3.4 Performance Requirements
- **Transcription**: < 2x audio duration (e.g., 60s audio → <120s processing)
- **Summary Generation**: < 30 seconds for typical meeting (5-10 min audio)
- **API Response Time**: < 500ms for non-AI endpoints
- **Mobile Sync**: < 5 seconds per recording

---

## 4. Data Contract

### 4.1 Summary JSON Structure
```json
{
  "summary_id": "uuid",
  "metadata": {
    "org_id": "uuid",
    "rep_id": "uuid",
    "client_id": "uuid | null",
    "language_mix": "he-IL/en-US",
    "duration": 3600
  },
  "content": {
    "summary_text": "Bulleted Hebrew text",
    "action_items": [
      {
        "task": "string",
        "due": "ISO date | null",
        "assignee": "string | null",
        "confidence": 0.0-1.0,
        "source": "transcript snippet",
        "language": "he|en|he-en"
      }
    ],
    "crm_entities": {
      "deal_value": {
        "value": 50000,
        "currency": "ILS|USD",
        "confidence": 0.0-1.0,
        "source": "transcript snippet",
        "language": "he|en|he-en"
      },
      "next_meeting_date": {
        "value": "ISO date",
        "confidence": 0.0-1.0,
        "source": "transcript snippet",
        "language": "he|en|he-en"
      },
      "contact_email": {
        "value": "email@example.com",
        "confidence": 0.0-1.0,
        "source": "transcript snippet",
        "language": "he|en|he-en"
      }
    }
  },
  "governance": {
    "feedback_loop_applied": false,
    "confidence_score": 0.0-1.0,
    "hallucination_check": "passed|failed|pending",
    "requires_review": true|false
  }
}
```

### 4.2 Validation Rules
- All confidence scores: 0.0 ≤ score ≤ 1.0
- All dates: ISO 8601 format (YYYY-MM-DD)
- All currencies: ILS or USD
- All sources: Non-empty string (exact transcript quote)

---

## 5. User Journeys

### 5.1 Field Sales Rep (Mobile Debrief)
1. Rep finishes client meeting
2. Opens mobile app, taps "Record"
3. Speaks 60-second debrief (offline OK)
4. Recording queued locally
5. App syncs when internet available
6. Push notification: "Summary ready"
7. Rep reviews summary, edits if needed
8. Rep approves → syncs to HubSpot

### 5.2 Sales Manager (Dashboard Review)
1. Manager opens dashboard
2. Sees team activity, deal sizes, alerts
3. Clicks on red alert (overdue follow-up)
4. Views meeting summary
5. Clicks "Show Source" to verify AI extraction
6. Approves or requests rep to edit

### 5.3 CISO (Compliance Audit)
1. CISO reviews audit logs
2. Verifies audio deletion timestamps
3. Checks RLS policies are active
4. Confirms data isolation between orgs
5. Exports compliance report

---

## 6. Out of Scope (Explicitly Excluded)

- ❌ Real-time transcription during live calls
- ❌ Video analysis (audio-only)
- ❌ Multi-language support beyond Hebrew/English
- ❌ Custom CRM integrations (HubSpot/Salesforce only)
- ❌ On-premise deployment (SaaS only)
- ❌ White-label solutions (single-branded)

---

## 7. Success Metrics

### 7.1 User Adoption
- **Target**: 80% of sales reps use mobile debrief weekly
- **Measurement**: Active users per org per week

### 7.2 Accuracy
- **Target**: <5% correction rate (95%+ AI accuracy)
- **Measurement**: Corrections table / Total summaries

### 7.3 Time Savings
- **Target**: 10 minutes saved per meeting (vs manual entry)
- **Measurement**: Time from recording to CRM sync

### 7.4 CRM Sync Success
- **Target**: 99% sync success rate
- **Measurement**: Successful syncs / Total sync attempts

---

## 8. Dependencies

- OpenAI API (Whisper, GPT-4o)
- HubSpot API (OAuth2, CRM objects)
- Supabase (PostgreSQL, RLS, Auth)
- React Native (Mobile app)
- AssemblyAI or similar (Speaker diarization)

---

## 9. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API downtime | High | Fallback to Gemini 1.5 Pro |
| Audio quality issues | Medium | Pre-processing, noise reduction |
| CRM API rate limits | Medium | Queue with exponential backoff |
| Data privacy breach | Critical | RLS, encryption, zero-retention |
| Mobile storage limits | Low | Queue size limits, cloud backup |

---

## 10. Future Enhancements (P1/P2)

- Salesforce integration (beyond HubSpot)
- Custom entity extraction (org-specific fields)
- Voice cloning for rep verification
- Multi-meeting context analysis
- Predictive deal scoring
