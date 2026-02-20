"""
Calendar Integration Module

Extracts dates/times from meeting summaries and formats them for calendar APIs.
Supports Google Calendar, Microsoft Outlook, and iCal formats.
"""

import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class CalendarProvider(Enum):
    """Supported calendar providers."""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    ICAL = "ical"


class EventType(Enum):
    """Types of calendar events."""
    FOLLOW_UP = "follow_up"
    DEMO = "demo"
    PROPOSAL_REVIEW = "proposal_review"
    CONTRACT_SIGNING = "contract_signing"
    CHECK_IN = "check_in"


@dataclass
class CalendarEvent:
    """Structured calendar event ready for API submission."""
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    event_type: EventType = EventType.FOLLOW_UP
    reminders: List[int] = field(default_factory=lambda: [30, 1440])  # 30min, 1 day
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def uid(self) -> str:
        """Generate unique event ID."""
        content = f"{self.title}{self.start_time.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_google_format(self) -> Dict[str, Any]:
        """Format event for Google Calendar API."""
        event = {
            "summary": self.title,
            "description": self.description,
            "start": {
                "dateTime": self.start_time.isoformat(),
                "timeZone": "Asia/Jerusalem",
            },
            "end": {
                "dateTime": self.end_time.isoformat(),
                "timeZone": "Asia/Jerusalem",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": m} for m in self.reminders
                ],
            },
        }
        
        if self.location:
            event["location"] = self.location
        
        if self.attendees:
            event["attendees"] = [{"email": email} for email in self.attendees]
        
        return event
    
    def to_outlook_format(self) -> Dict[str, Any]:
        """Format event for Microsoft Graph API."""
        event = {
            "subject": self.title,
            "body": {
                "contentType": "HTML",
                "content": self.description,
            },
            "start": {
                "dateTime": self.start_time.isoformat(),
                "timeZone": "Israel Standard Time",
            },
            "end": {
                "dateTime": self.end_time.isoformat(),
                "timeZone": "Israel Standard Time",
            },
            "isReminderOn": True,
            "reminderMinutesBeforeStart": self.reminders[0] if self.reminders else 30,
        }
        
        if self.location:
            event["location"] = {"displayName": self.location}
        
        if self.attendees:
            event["attendees"] = [
                {
                    "emailAddress": {"address": email},
                    "type": "required"
                }
                for email in self.attendees
            ]
        
        return event
    
    def to_ical(self) -> str:
        """Generate iCal format string."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//SalesEcho AI//Calendar//EN",
            "BEGIN:VEVENT",
            f"UID:{self.uid}@salesecho.ai",
            f"DTSTART:{self.start_time.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{self.end_time.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{self.title}",
            f"DESCRIPTION:{self.description.replace(chr(10), '\\n')}",
        ]
        
        if self.location:
            lines.append(f"LOCATION:{self.location}")
        
        for attendee in self.attendees:
            lines.append(f"ATTENDEE:mailto:{attendee}")
        
        lines.extend([
            "END:VEVENT",
            "END:VCALENDAR",
        ])
        
        return "\r\n".join(lines)


class CalendarModule:
    """
    Calendar event extraction and formatting module.
    
    Parses meeting summaries to extract scheduling information and
    generates properly formatted calendar events.
    """
    
    # Hebrew day names for parsing
    HEBREW_DAYS = {
        "ראשון": 0, "שני": 1, "שלישי": 2, "רביעי": 3,
        "חמישי": 4, "שישי": 5, "שבת": 6,
    }
    
    # Hebrew month names
    HEBREW_MONTHS = {
        "ינואר": 1, "פברואר": 2, "מרץ": 3, "אפריל": 4,
        "מאי": 5, "יוני": 6, "יולי": 7, "אוגוסט": 8,
        "ספטמבר": 9, "אוקטובר": 10, "נובמבר": 11, "דצמבר": 12,
    }
    
    # Time patterns
    TIME_PATTERNS = [
        r'(\d{1,2}):(\d{2})',  # 14:30
        r'(\d{1,2})h(\d{2})',  # 14h30
        r'(\d{1,2})\s*(am|pm|AM|PM)',  # 2pm
        r'בשעה\s*(\d{1,2}):?(\d{2})?',  # בשעה 14:30
    ]
    
    # Date patterns
    DATE_PATTERNS = [
        r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})',  # 25/12/2025
        r'(\d{1,2})\s+(?:ב)?([א-ת]+)\s+(\d{4})?',  # 25 בדצמבר 2025
    ]
    
    def __init__(self, default_duration_minutes: int = 60):
        """
        Initialize Calendar module.
        
        Args:
            default_duration_minutes: Default meeting duration
        """
        self.default_duration = timedelta(minutes=default_duration_minutes)
    
    async def extract_events_from_summary(
        self,
        summary: Dict[str, Any],
        client_name: str,
        client_email: Optional[str] = None,
        organizer_email: Optional[str] = None,
    ) -> List[CalendarEvent]:
        """
        Extract calendar events from a meeting summary.
        
        Args:
            summary: Meeting summary content
            client_name: Client name for event titles
            client_email: Client email to add as attendee
            organizer_email: Organizer's email
            
        Returns:
            List of CalendarEvent objects
        """
        events = []
        
        # Check for explicit next_meeting_date in CRM entities
        crm_entities = summary.get("crm_entities", {})
        next_meeting = crm_entities.get("next_meeting_date") if crm_entities else None
        
        if next_meeting and next_meeting.get("value"):
            date_str = next_meeting.get("value")
            parsed_date = self._parse_date_string(date_str)
            
            if parsed_date:
                event = await self._create_follow_up_event(
                    start_time=parsed_date,
                    client_name=client_name,
                    summary=summary,
                    client_email=client_email,
                    organizer_email=organizer_email,
                )
                events.append(event)
        
        # Extract dates from action items
        action_items = summary.get("action_items", [])
        for item in action_items:
            due = item.get("due")
            if due:
                parsed_date = self._parse_date_string(due)
                if parsed_date:
                    task = item.get("task", "Follow up")
                    event = CalendarEvent(
                        title=f"Task: {task[:50]}",
                        description=f"Action item from meeting with {client_name}:\n\n{task}",
                        start_time=parsed_date,
                        end_time=parsed_date + timedelta(minutes=30),
                        event_type=EventType.CHECK_IN,
                        attendees=[e for e in [organizer_email] if e],
                        metadata={
                            "source": "action_item",
                            "original_task": task,
                        },
                    )
                    events.append(event)
        
        # Parse summary text for date mentions
        summary_text = summary.get("summary_text", "")
        text_events = await self._extract_dates_from_text(
            summary_text, client_name, client_email, organizer_email
        )
        events.extend(text_events)
        
        return events
    
    async def _create_follow_up_event(
        self,
        start_time: datetime,
        client_name: str,
        summary: Dict[str, Any],
        client_email: Optional[str] = None,
        organizer_email: Optional[str] = None,
    ) -> CalendarEvent:
        """Create a follow-up meeting event."""
        attendees = []
        if client_email:
            attendees.append(client_email)
        if organizer_email:
            attendees.append(organizer_email)
        
        # Build description from summary
        description_parts = [
            f"Follow-up meeting with {client_name}",
            "",
            "Previous meeting summary:",
            summary.get("summary_text", "No summary available"),
        ]
        
        action_items = summary.get("action_items", [])
        if action_items:
            description_parts.append("")
            description_parts.append("Open action items:")
            for item in action_items:
                description_parts.append(f"• {item.get('task', '')}")
        
        return CalendarEvent(
            title=f"Follow-up: {client_name}",
            description="\n".join(description_parts),
            start_time=start_time,
            end_time=start_time + self.default_duration,
            attendees=attendees,
            event_type=EventType.FOLLOW_UP,
            reminders=[30, 1440, 10080],  # 30min, 1 day, 1 week
            metadata={
                "client_name": client_name,
                "source": "crm_entities",
            },
        )
    
    async def _extract_dates_from_text(
        self,
        text: str,
        client_name: str,
        client_email: Optional[str],
        organizer_email: Optional[str],
    ) -> List[CalendarEvent]:
        """Extract date mentions from free text."""
        events = []
        
        # Common patterns for scheduling mentions
        scheduling_patterns = [
            r'נקבע\s+ל?-?\s*(.+?)(?:\.|$)',  # נקבע ל-25/12
            r'פגישה\s+ב?-?\s*(.+?)(?:\.|$)',  # פגישה ב-25/12
            r'meeting\s+(?:on|at)\s+(.+?)(?:\.|$)',  # meeting on Dec 25
            r'scheduled\s+(?:for|on)\s+(.+?)(?:\.|$)',  # scheduled for Dec 25
            r'call\s+(?:on|at)\s+(.+?)(?:\.|$)',  # call on Monday
        ]
        
        for pattern in scheduling_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1).strip()
                parsed_date = self._parse_date_string(date_str)
                
                if parsed_date:
                    attendees = [e for e in [client_email, organizer_email] if e]
                    event = CalendarEvent(
                        title=f"Meeting: {client_name}",
                        description=f"Extracted from meeting notes:\n\n{match.group(0)}",
                        start_time=parsed_date,
                        end_time=parsed_date + self.default_duration,
                        attendees=attendees,
                        event_type=EventType.FOLLOW_UP,
                        metadata={
                            "source": "text_extraction",
                            "original_text": match.group(0),
                        },
                    )
                    events.append(event)
        
        return events
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """
        Parse a date string into a datetime object.
        
        Handles various formats:
        - DD/MM/YYYY, DD-MM-YYYY
        - Hebrew month names (25 בדצמבר)
        - Relative dates (מחר, בעוד שבוע)
        - ISO format
        """
        if not date_str:
            return None
        
        date_str = date_str.strip()
        now = datetime.now()
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass
        
        # Try DD/MM/YYYY format
        date_match = re.match(r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})', date_str)
        if date_match:
            day, month, year = date_match.groups()
            year = int(year)
            if year < 100:
                year += 2000
            try:
                # Extract time if present
                time_match = re.search(r'(\d{1,2}):(\d{2})', date_str)
                hour = int(time_match.group(1)) if time_match else 10
                minute = int(time_match.group(2)) if time_match else 0
                
                return datetime(year, int(month), int(day), hour, minute)
            except ValueError:
                pass
        
        # Try Hebrew month names
        for heb_month, month_num in self.HEBREW_MONTHS.items():
            if heb_month in date_str:
                day_match = re.search(r'(\d{1,2})', date_str)
                if day_match:
                    day = int(day_match.group(1))
                    year_match = re.search(r'(\d{4})', date_str)
                    year = int(year_match.group(1)) if year_match else now.year
                    
                    # If month is in the past, assume next year
                    target = datetime(year, month_num, day, 10, 0)
                    if target < now:
                        target = target.replace(year=year + 1)
                    return target
        
        # Handle relative dates
        relative_patterns = {
            r'מחר|tomorrow': timedelta(days=1),
            r'בעוד שבוע|next week|in a week': timedelta(weeks=1),
            r'בעוד יומיים|in two days': timedelta(days=2),
            r'בעוד חודש|next month|in a month': timedelta(days=30),
        }
        
        for pattern, delta in relative_patterns.items():
            if re.search(pattern, date_str, re.IGNORECASE):
                future = now + delta
                return future.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Handle day names
        for heb_day, day_num in self.HEBREW_DAYS.items():
            if heb_day in date_str:
                current_day = now.weekday()
                days_ahead = day_num - current_day
                if days_ahead <= 0:
                    days_ahead += 7
                target = now + timedelta(days=days_ahead)
                return target.replace(hour=10, minute=0, second=0, microsecond=0)
        
        return None
    
    async def create_quick_event(
        self,
        title: str,
        date: datetime,
        duration_minutes: int = 60,
        attendees: Optional[List[str]] = None,
        description: str = "",
    ) -> CalendarEvent:
        """
        Create a quick calendar event with minimal input.
        
        Args:
            title: Event title
            date: Start date/time
            duration_minutes: Event duration
            attendees: List of attendee emails
            description: Event description
            
        Returns:
            CalendarEvent ready for submission
        """
        return CalendarEvent(
            title=title,
            description=description,
            start_time=date,
            end_time=date + timedelta(minutes=duration_minutes),
            attendees=attendees or [],
            event_type=EventType.FOLLOW_UP,
        )


# Module instance for easy import
calendar_module = CalendarModule()
