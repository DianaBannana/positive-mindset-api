"""
Email Module

Generates professional email drafts based on meeting summaries.
Supports follow-up emails, summary emails, and action item reminders.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class EmailType(Enum):
    """Types of email templates."""
    FOLLOW_UP = "follow_up"
    SUMMARY = "summary"
    ACTION_REMINDER = "action_reminder"
    PROPOSAL = "proposal"
    THANK_YOU = "thank_you"


class EmailPriority(Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class EmailDraft:
    """Structured email draft ready for sending."""
    to: List[str]
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    email_type: EmailType = EmailType.FOLLOW_UP
    priority: EmailPriority = EmailPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "email_type": self.email_type.value,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class EmailModule:
    """
    Professional email generation module.
    
    Generates well-formatted email drafts based on meeting summaries,
    supporting Hebrew and English with proper formatting.
    """
    
    def __init__(self, default_language: str = "he"):
        """
        Initialize Email module.
        
        Args:
            default_language: Default language for emails
        """
        self.default_language = default_language
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load email templates for different languages."""
        return {
            "he": {
                "follow_up_subject": "המשך לשיחה שלנו - {topic}",
                "summary_subject": "סיכום פגישה - {date}",
                "action_reminder_subject": "תזכורת: משימות פתוחות מהשיחה שלנו",
                "greeting": "שלום {name},",
                "follow_up_intro": "תודה על הזמן שהקדשת לשיחה שלנו. להלן סיכום הנקודות העיקריות שדנו בהן:",
                "summary_intro": "מצורף סיכום הפגישה שלנו מתאריך {date}:",
                "action_items_header": "משימות לביצוע:",
                "next_steps_header": "צעדים הבאים:",
                "deal_section": "פרטי העסקה:",
                "timeline_label": "לוח זמנים:",
                "closing": "אשמח לענות על כל שאלה.",
                "signature": "בברכה,\n{sender_name}\n{sender_title}\n{company_name}",
                "thank_you": "תודה רבה על שיתוף הפעולה.",
            },
            "en": {
                "follow_up_subject": "Following up on our conversation - {topic}",
                "summary_subject": "Meeting Summary - {date}",
                "action_reminder_subject": "Reminder: Open action items from our call",
                "greeting": "Hi {name},",
                "follow_up_intro": "Thank you for taking the time to speak with me. Here's a summary of the key points we discussed:",
                "summary_intro": "Please find below the summary of our meeting on {date}:",
                "action_items_header": "Action Items:",
                "next_steps_header": "Next Steps:",
                "deal_section": "Deal Details:",
                "timeline_label": "Timeline:",
                "closing": "Please don't hesitate to reach out if you have any questions.",
                "signature": "Best regards,\n{sender_name}\n{sender_title}\n{company_name}",
                "thank_you": "Thank you for your collaboration.",
            }
        }
    
    async def generate_follow_up_email(
        self,
        summary: Dict[str, Any],
        recipient_email: str,
        recipient_name: str,
        sender_name: str,
        sender_title: Optional[str] = None,
        company_name: Optional[str] = None,
        meeting_topic: Optional[str] = None,
        language: Optional[str] = None,
        include_action_items: bool = True,
    ) -> EmailDraft:
        """
        Generate a professional follow-up email.
        
        Args:
            summary: Meeting summary content
            recipient_email: Recipient's email address
            recipient_name: Recipient's name
            sender_name: Sender's name
            sender_title: Sender's job title
            company_name: Company name
            meeting_topic: Topic for subject line
            language: Email language
            include_action_items: Whether to include action items
            
        Returns:
            EmailDraft ready for sending
        """
        lang = language or self.default_language
        t = self.templates.get(lang, self.templates["en"])
        
        # Subject line
        topic = meeting_topic or self._extract_topic(summary)
        subject = t["follow_up_subject"].format(topic=topic)
        
        # Build HTML body
        html_parts = []
        text_parts = []
        
        # Greeting
        greeting = t["greeting"].format(name=recipient_name)
        html_parts.append(f"<p>{greeting}</p>")
        text_parts.append(greeting)
        text_parts.append("")
        
        # Intro
        html_parts.append(f"<p>{t['follow_up_intro']}</p>")
        text_parts.append(t["follow_up_intro"])
        text_parts.append("")
        
        # Summary text
        summary_text = summary.get("summary_text", "")
        if summary_text:
            html_parts.append(f"<p>{summary_text}</p>")
            text_parts.append(summary_text)
            text_parts.append("")
        
        # Action items
        action_items = summary.get("action_items", [])
        if include_action_items and action_items:
            html_parts.append(f"<p><strong>{t['action_items_header']}</strong></p>")
            html_parts.append("<ul>")
            text_parts.append(t["action_items_header"])
            
            for item in action_items:
                task = item.get("task", "")
                due = item.get("due")
                assignee = item.get("assignee")
                
                item_text = task
                if due:
                    item_text += f" (Due: {due})"
                if assignee:
                    item_text += f" - {assignee}"
                
                html_parts.append(f"<li>{item_text}</li>")
                text_parts.append(f"• {item_text}")
            
            html_parts.append("</ul>")
            text_parts.append("")
        
        # Deal value if present
        crm_entities = summary.get("crm_entities", {})
        deal_value = crm_entities.get("deal_value") if crm_entities else None
        if deal_value and deal_value.get("value"):
            currency = deal_value.get("currency", "₪")
            value = deal_value.get("value")
            deal_text = f"{t['deal_section']} {currency}{value:,.0f}"
            html_parts.append(f"<p><strong>{deal_text}</strong></p>")
            text_parts.append(deal_text)
            text_parts.append("")
        
        # Closing
        html_parts.append(f"<p>{t['closing']}</p>")
        text_parts.append(t["closing"])
        text_parts.append("")
        
        # Signature
        sig_parts = [sender_name]
        if sender_title:
            sig_parts.append(sender_title)
        if company_name:
            sig_parts.append(company_name)
        
        signature_text = "\n".join(sig_parts)
        signature_html = "<br>".join(sig_parts)
        
        html_parts.append(f"<p>{signature_html}</p>")
        text_parts.append(signature_text)
        
        # Set direction for Hebrew
        dir_attr = 'dir="rtl"' if lang == "he" else 'dir="ltr"'
        body_html = f'<div {dir_attr}>{"".join(html_parts)}</div>'
        body_text = "\n".join(text_parts)
        
        return EmailDraft(
            to=[recipient_email],
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            email_type=EmailType.FOLLOW_UP,
            priority=self._determine_priority(summary),
            metadata={
                "recipient_name": recipient_name,
                "sender_name": sender_name,
                "language": lang,
                "action_item_count": len(action_items),
                "has_deal_value": deal_value is not None,
            },
        )
    
    async def generate_summary_email(
        self,
        summary: Dict[str, Any],
        recipient_emails: List[str],
        meeting_date: datetime,
        sender_name: str,
        language: Optional[str] = None,
    ) -> EmailDraft:
        """
        Generate a meeting summary email for distribution.
        
        Args:
            summary: Meeting summary content
            recipient_emails: List of recipient emails
            meeting_date: Date of the meeting
            sender_name: Sender's name
            language: Email language
            
        Returns:
            EmailDraft with full meeting summary
        """
        lang = language or self.default_language
        t = self.templates.get(lang, self.templates["en"])
        
        date_str = meeting_date.strftime("%d/%m/%Y")
        subject = t["summary_subject"].format(date=date_str)
        
        html_parts = []
        text_parts = []
        
        # Header
        header = t["summary_intro"].format(date=date_str)
        html_parts.append(f"<h2>{header}</h2>")
        text_parts.append(header)
        text_parts.append("=" * 50)
        text_parts.append("")
        
        # Summary text
        summary_text = summary.get("summary_text", "")
        if summary_text:
            html_parts.append(f"<p>{summary_text}</p>")
            text_parts.append(summary_text)
            text_parts.append("")
        
        # Action items section
        action_items = summary.get("action_items", [])
        if action_items:
            html_parts.append(f"<h3>{t['action_items_header']}</h3>")
            html_parts.append("<table border='1' cellpadding='8' style='border-collapse: collapse;'>")
            html_parts.append("<tr><th>#</th><th>Task</th><th>Assignee</th><th>Due</th></tr>")
            
            text_parts.append(t["action_items_header"])
            text_parts.append("-" * 40)
            
            for idx, item in enumerate(action_items, 1):
                task = item.get("task", "")
                due = item.get("due", "-")
                assignee = item.get("assignee", "-")
                
                html_parts.append(f"<tr><td>{idx}</td><td>{task}</td><td>{assignee}</td><td>{due}</td></tr>")
                text_parts.append(f"{idx}. {task} | {assignee} | {due}")
            
            html_parts.append("</table>")
            text_parts.append("")
        
        # Thank you
        html_parts.append(f"<p>{t['thank_you']}</p>")
        html_parts.append(f"<p>{sender_name}</p>")
        text_parts.append(t["thank_you"])
        text_parts.append(sender_name)
        
        dir_attr = 'dir="rtl"' if lang == "he" else 'dir="ltr"'
        body_html = f'<div {dir_attr}>{"".join(html_parts)}</div>'
        body_text = "\n".join(text_parts)
        
        return EmailDraft(
            to=recipient_emails,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            email_type=EmailType.SUMMARY,
            metadata={
                "meeting_date": date_str,
                "recipient_count": len(recipient_emails),
                "action_item_count": len(action_items),
            },
        )
    
    async def generate_action_reminder(
        self,
        action_items: List[Dict[str, Any]],
        recipient_email: str,
        recipient_name: str,
        original_meeting_date: datetime,
        language: Optional[str] = None,
    ) -> EmailDraft:
        """
        Generate an action item reminder email.
        
        Args:
            action_items: List of pending action items
            recipient_email: Recipient's email
            recipient_name: Recipient's name
            original_meeting_date: Date of original meeting
            language: Email language
            
        Returns:
            EmailDraft with action reminders
        """
        lang = language or self.default_language
        t = self.templates.get(lang, self.templates["en"])
        
        subject = t["action_reminder_subject"]
        date_str = original_meeting_date.strftime("%d/%m/%Y")
        
        html_parts = [
            f"<p>{t['greeting'].format(name=recipient_name)}</p>",
            f"<p>This is a reminder about the following action items from our meeting on {date_str}:</p>",
            "<ul>",
        ]
        
        text_parts = [
            t["greeting"].format(name=recipient_name),
            "",
            f"Action items from meeting on {date_str}:",
            "",
        ]
        
        for item in action_items:
            task = item.get("task", "")
            due = item.get("due")
            
            item_html = f"<li><strong>{task}</strong>"
            item_text = f"• {task}"
            
            if due:
                item_html += f" <em>(Due: {due})</em>"
                item_text += f" (Due: {due})"
            
            item_html += "</li>"
            html_parts.append(item_html)
            text_parts.append(item_text)
        
        html_parts.append("</ul>")
        html_parts.append(f"<p>{t['closing']}</p>")
        text_parts.append("")
        text_parts.append(t["closing"])
        
        dir_attr = 'dir="rtl"' if lang == "he" else 'dir="ltr"'
        
        return EmailDraft(
            to=[recipient_email],
            subject=subject,
            body_html=f'<div {dir_attr}>{"".join(html_parts)}</div>',
            body_text="\n".join(text_parts),
            email_type=EmailType.ACTION_REMINDER,
            priority=EmailPriority.HIGH,
            metadata={
                "recipient_name": recipient_name,
                "action_item_count": len(action_items),
                "meeting_date": date_str,
            },
        )
    
    def _extract_topic(self, summary: Dict[str, Any]) -> str:
        """Extract a topic from the summary for subject line."""
        summary_text = summary.get("summary_text", "")
        if not summary_text:
            return "Our Discussion"
        
        # Take first sentence or first 50 chars
        first_sentence = re.split(r'[.!?]', summary_text)[0]
        if len(first_sentence) > 50:
            return first_sentence[:47] + "..."
        return first_sentence
    
    def _determine_priority(self, summary: Dict[str, Any]) -> EmailPriority:
        """Determine email priority based on summary content."""
        # High priority if deal value > 100K or requires review
        governance = summary.get("governance", {})
        if governance.get("requires_review"):
            return EmailPriority.HIGH
        
        crm_entities = summary.get("crm_entities", {})
        deal_value = crm_entities.get("deal_value") if crm_entities else None
        if deal_value and deal_value.get("value", 0) > 100000:
            return EmailPriority.HIGH
        
        return EmailPriority.NORMAL


# Module instance for easy import
email_module = EmailModule()
