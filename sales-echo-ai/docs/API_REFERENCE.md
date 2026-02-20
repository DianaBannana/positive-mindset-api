# SalesEcho AI - API Reference

## Integration Guide for PBX Providers & Enterprise Telephony Systems

**Version**: 1.0  
**Last Updated**: February 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
   - [Webhook Ingestion](#webhook-ingestion)
   - [WhatsApp Voice Messages](#whatsapp-voice-messages)
   - [Status Check](#status-check)
4. [Payload Examples](#payload-examples)
5. [Callbacks](#callbacks)
6. [Error Handling](#error-handling)
7. [Rate Limits & Quotas](#rate-limits--quotas)
8. [Security Best Practices](#security-best-practices)

---

## Overview

SalesEcho AI provides a webhook-based API for ingesting call recordings from enterprise PBX systems, cloud telephony platforms, and messaging services like WhatsApp.

### Supported Sources

| Source Type | Endpoint | Audio Formats |
|-------------|----------|---------------|
| PBX / Call Recording | `/api/v1/ingest/webhook` | MP3, WAV, M4A, OGG |
| WhatsApp Voice | `/api/v1/ingest/whatsapp` | OGG (Opus), M4A |
| Direct Upload | `/api/v1/ingest/webhook` | MP3, WAV, M4A |

### Integration Flow

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Your PBX      │ ──▶  │  SalesEcho API   │ ──▶  │  AI Processing  │
│   System        │      │  (Webhook)       │      │  Pipeline       │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                       │                         │
         │ 1. Call ends          │                         │
         │ 2. POST recording     │                         │
         │    URL + metadata     │ 3. Download audio       │
         │                       │ 4. Transcribe (Gemini)  │
         │                       │ 5. Generate summary     │
         │                       │ 6. Extract actions      │
         │                       │                         │
         │◀─────────────────────────────────────────────────│
         │      7. Callback with results (optional)        │
```

---

## Authentication

### API Key Authentication

All API requests require authentication via API key in the header.

| Header | Value | Required |
|--------|-------|----------|
| `X-API-Key` | Your SalesEcho API key | ✅ Yes |
| `X-Org-ID` | Your organization UUID | ✅ Yes |

### Obtaining API Keys

1. Log into the SalesEcho dashboard
2. Navigate to **Settings → API Keys**
3. Click **Generate New Key**
4. Copy the key immediately (shown only once)

### Key Types

| Prefix | Environment | Usage |
|--------|-------------|-------|
| `salesecho_live_` | Production | Real call processing, counts towards quota |
| `salesecho_test_` | Testing | Sandbox mode, no quota impact |

### Example Header

```http
POST /api/v1/ingest/webhook HTTP/1.1
Host: api.salesecho.ai
X-API-Key: <your-api-key>
X-Org-ID: <your-org-uuid>
Content-Type: multipart/form-data
```

---

## Endpoints

### Webhook Ingestion

**Endpoint**: `POST /api/v1/ingest/webhook`

**Description**: Primary endpoint for PBX and call recording integrations.

#### Request Format

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `recording_url` | string | Yes* | URL to download the audio file |
| `file` | file | Yes* | Direct file upload (multipart) |
| `client_phone` | string | No | Client's phone number (E.164 format) |
| `client_name` | string | No | Client's name |
| `user_id` | string | No | Sales rep's user ID |
| `callback_url` | string | No | URL to POST results when complete |

*Either `recording_url` OR `file` is required.

#### cURL Example (URL-based)

```bash
curl -X POST https://api.salesecho.ai/api/v1/ingest/webhook \
  -H "X-API-Key: YOUR_SALESECHO_API_KEY" \
  -H "X-Org-ID: your-org-uuid" \
  -F "recording_url=https://your-pbx.com/recordings/call_123.mp3" \
  -F "client_phone=+972501234567" \
  -F "client_name=John Doe" \
  -F "callback_url=https://your-system.com/webhook/salesecho"
```

#### cURL Example (File Upload)

```bash
curl -X POST https://api.salesecho.ai/api/v1/ingest/webhook \
  -H "X-API-Key: YOUR_SALESECHO_API_KEY" \
  -H "X-Org-ID: your-org-uuid" \
  -F "file=@/path/to/recording.mp3" \
  -F "client_phone=+972501234567"
```

#### Success Response

```json
{
  "success": true,
  "meeting_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "status": "PENDING",
  "message": "Recording received. Processing started.",
  "processing_started": true
}
```

---

### WhatsApp Voice Messages

**Endpoint**: `POST /api/v1/ingest/whatsapp`

**Description**: Specialized endpoint for WhatsApp voice message integrations (Twilio, Meta Cloud API).

#### Request Body (JSON)

```json
{
  "media_url": "https://api.twilio.com/.../Media/...",
  "media_content_type": "audio/ogg",
  "sender_phone": "+972501234567",
  "sender_name": "John Doe",
  "message_id": "SM1234567890",
  "timestamp": "2026-02-20T10:30:00Z",
  "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "callback_url": "https://your-system.com/webhook/complete"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `media_url` | string | ✅ Yes | URL to download voice message |
| `sender_phone` | string | ✅ Yes | Sender's WhatsApp number (E.164) |
| `media_content_type` | string | No | MIME type (default: audio/ogg) |
| `sender_name` | string | No | Sender's profile name |
| `message_id` | string | No | WhatsApp message ID (for deduplication) |
| `timestamp` | string | No | ISO 8601 timestamp |
| `rep_phone` | string | No | Sales rep's phone (to identify rep) |
| `callback_url` | string | No | Callback URL for results |

#### cURL Example

```bash
curl -X POST https://api.salesecho.ai/api/v1/ingest/whatsapp \
  -H "X-API-Key: YOUR_SALESECHO_API_KEY" \
  -H "X-Org-ID: your-org-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://api.twilio.com/.../Media/...",
    "sender_phone": "+972501234567",
    "sender_name": "John Doe",
    "message_id": "SM1234567890"
  }'
```

---

### Status Check

**Endpoint**: `GET /api/v1/ingest/status/{meeting_id}`

**Description**: Check the processing status of an ingested recording.

#### Request

```bash
curl -X GET "https://api.salesecho.ai/api/v1/ingest/status/d290f1ee-6c54-4b01-90e6-d701748f0851" \
  -H "X-API-Key: YOUR_SALESECHO_API_KEY" \
  -H "X-Org-ID: your-org-uuid"
```

#### Response

```json
{
  "meeting_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "status": "COMPLETED",
  "transcript_ready": true,
  "summary_ready": true,
  "created_at": "2026-02-20T10:30:00Z",
  "completed_at": "2026-02-20T10:32:15Z"
}
```

#### Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Recording received, queued for processing |
| `PROCESSING` | Currently transcribing/summarizing |
| `COMPLETED` | Successfully processed |
| `FAILED` | Processing failed (check error details) |

---

## Payload Examples

### Asterisk PBX Integration

```bash
# In your Asterisk dialplan or AGI script:
curl -X POST https://api.salesecho.ai/api/v1/ingest/webhook \
  -H "X-API-Key: ${SALESECHO_API_KEY}" \
  -H "X-Org-ID: ${SALESECHO_ORG_ID}" \
  -F "recording_url=http://your-asterisk-server/monitor/${UNIQUEID}.wav" \
  -F "client_phone=${CALLERID(num)}" \
  -F "user_id=${AGENT_ID}"
```

### 3CX Integration

```json
// 3CX Webhook payload transformation
{
  "recording_url": "https://your-3cx.com/recordings/${call_id}.mp3",
  "client_phone": "${caller_number}",
  "client_name": "${caller_name}",
  "user_id": "${extension}",
  "callback_url": "https://your-3cx.com/api/salesecho-callback"
}
```

### FreePBX Integration

```php
<?php
// FreePBX post-call hook
$payload = [
    'recording_url' => $recording_path,
    'client_phone' => $caller_id,
    'user_id' => $extension,
];

$ch = curl_init('https://api.salesecho.ai/api/v1/ingest/webhook');
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: ' . getenv('SALESECHO_API_KEY'),
    'X-Org-ID: ' . getenv('SALESECHO_ORG_ID'),
]);
$response = curl_exec($ch);
```

### Twilio Voice Integration

```javascript
// Node.js - Twilio webhook handler
app.post('/twilio/recording-complete', async (req, res) => {
  const { RecordingUrl, From, To, CallSid } = req.body;
  
  await fetch('https://api.salesecho.ai/api/v1/ingest/webhook', {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.SALESECHO_API_KEY,
      'X-Org-ID': process.env.SALESECHO_ORG_ID,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      recording_url: RecordingUrl + '.mp3',
      client_phone: From,
      callback_url: 'https://your-app.com/salesecho-callback',
    }),
  });
  
  res.status(200).send('OK');
});
```

---

## Callbacks

When `callback_url` is provided, SalesEcho will POST results upon completion.

### Callback Payload

```json
{
  "meeting_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "status": "COMPLETED",
  "summary": {
    "content": {
      "summary_text": "Call with John about software pricing...",
      "key_points": ["Discussed enterprise tier", "Budget: $50,000"],
      "action_items": [
        {
          "task": "Send proposal by Friday",
          "assignee": "rep",
          "due": "2026-02-25"
        }
      ],
      "deal_heat": "hot",
      "crm_entities": {
        "deal_value": {"value": 50000, "currency": "USD"},
        "next_meeting_date": {"value": "2026-02-25T14:00:00Z"}
      }
    },
    "governance": {
      "confidence_score": 0.87,
      "sentiment_score": 0.65
    }
  },
  "client_name": "John Doe",
  "client_phone": "+972501234567",
  "duration_seconds": 342
}
```

### Callback Security

- Callbacks are sent via HTTPS only
- Include `X-SalesEcho-Signature` header for verification
- Signature: `HMAC-SHA256(payload, webhook_secret)`

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request (invalid parameters) |
| `401` | Unauthorized (invalid API key) |
| `402` | Payment required (quota exceeded) |
| `404` | Not found |
| `429` | Rate limit exceeded |
| `500` | Server error |

### Error Response Format

```json
{
  "detail": "Invalid API key",
  "error_code": "AUTH_FAILED"
}
```

### Quota Exceeded (402)

```json
{
  "detail": {
    "error": "quota_exceeded",
    "reason": "meetings_quota",
    "usage": {
      "meetings": {"used": 10, "limit": 10, "remaining": 0}
    },
    "message": "You've used all 10 meetings in your plan. Upgrade for more."
  }
}
```

---

## Rate Limits & Quotas

### Rate Limits

| Plan | Requests/minute | Concurrent |
|------|-----------------|------------|
| Trial | 10 | 2 |
| Starter | 60 | 5 |
| Pro | 120 | 10 |
| Enterprise | Unlimited | 50 |

### Quotas (Monthly)

| Plan | Meetings | Audio Minutes |
|------|----------|---------------|
| Trial | 10 | 60 |
| Starter | 50 | 300 |
| Pro | 200 | 1000 |
| Enterprise | Unlimited | Unlimited |

---

## Security Best Practices

### 1. Secure API Keys

```bash
# Store as environment variables
export SALESECHO_API_KEY=salesecho_xxxxx
export SALESECHO_ORG_ID=550e8400-...

# Never commit to source control
echo "SALESECHO_API_KEY" >> .gitignore
```

### 2. Verify Callbacks

```python
import hmac
import hashlib

def verify_callback(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 3. Use HTTPS Only

All API requests must use HTTPS. HTTP requests will be rejected.

### 4. Restrict Recording URLs

If using `recording_url`, ensure your audio files are:
- Time-limited (signed URLs with expiration)
- IP-restricted if possible
- Deleted after successful ingestion

---

## Support

- **Documentation**: https://docs.salesecho.ai
- **Email**: support@salesecho.ai
- **Status Page**: https://status.salesecho.ai

---

*© 2026 SalesEcho AI. All rights reserved.*
