"""
WhatsApp Integration Module

Handles formatting and preparation of WhatsApp messages based on meeting summaries.
Supports both individual messages and group broadcasts.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageTemplate(Enum):
    """Pre-defined message templates for different scenarios."""
    SUMMARY = "summary"
    ACTION_ITEMS = "action_items"
    FOLLOW_UP = "follow_up"
    DEAL_UPDATE = "deal_update"


@dataclass
class WhatsAppMessage:
    """Structured WhatsApp message ready for delivery."""
    recipient_phone: Optional[str]
    message_text: str
    template: MessageTemplate
    metadata: Dict[str, Any]
    created_at: datetime
    
    def to_wa_me_url(self) -> str:
        """Generate wa.me URL for web-based sending."""
        import urllib.parse
        encoded = urllib.parse.quote(self.message_text)
        if self.recipient_phone:
            return f"https://wa.me/{self.recipient_phone}?text={encoded}"
        return f"https://wa.me/?text={encoded}"


class WhatsAppModule:
    """
    WhatsApp message generation and formatting module.
    
    This module transforms meeting summaries into professionally formatted
    WhatsApp messages suitable for sending to clients or team members.
    """
    
    def __init__(self, default_language: str = "he"):
        """
        Initialize WhatsApp module.
        
        Args:
            default_language: Default language for messages ("he" or "en")
        """
        self.default_language = default_language
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load message templates for different languages."""
        return {
            "he": {
                "greeting": "היי {name},",
                "summary_intro": "הנה סיכום השיחה שלנו:",
                "action_items_header": "📋 משימות לביצוע:",
                "next_steps_header": "👉 צעדים הבאים:",
                "deal_value_label": "💰 ערך עסקה:",
                "deadline_label": "📅 דדליין:",
                "signature": "בברכה,\n{sender_name}",
                "follow_up_intro": "רציתי לעקוב בנוגע לשיחה שלנו מ-{date}.",
            },
            "en": {
                "greeting": "Hi {name},",
                "summary_intro": "Here's a summary of our call:",
                "action_items_header": "📋 Action Items:",
                "next_steps_header": "👉 Next Steps:",
                "deal_value_label": "💰 Deal Value:",
                "deadline_label": "📅 Deadline:",
                "signature": "Best regards,\n{sender_name}",
                "follow_up_intro": "I wanted to follow up on our conversation from {date}.",
            }
        }
    
    async def generate_summary_message(
        self,
        summary: Dict[str, Any],
        client_name: str,
        sender_name: Optional[str] = None,
        language: Optional[str] = None,
        recipient_phone: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Generate a formatted summary message for WhatsApp.
        
        Args:
            summary: The meeting summary content
            client_name: Name of the client/recipient
            sender_name: Name of the sender (optional)
            language: Message language ("he" or "en")
            recipient_phone: Phone number in international format
            
        Returns:
            WhatsAppMessage ready for delivery
        """
        lang = language or self.default_language
        t = self.templates.get(lang, self.templates["en"])
        
        lines = []
        
        # Greeting
        lines.append(t["greeting"].format(name=client_name))
        lines.append("")
        lines.append(t["summary_intro"])
        lines.append("")
        
        # Main summary text
        if summary.get("summary_text"):
            lines.append(summary["summary_text"])
            lines.append("")
        
        # Action items
        action_items = summary.get("action_items", [])
        if action_items:
            lines.append(t["action_items_header"])
            for idx, item in enumerate(action_items, 1):
                task = item.get("task", "")
                due = item.get("due")
                assignee = item.get("assignee")
                
                line = f"{idx}. {task}"
                if due:
                    line += f" ({t['deadline_label']} {due})"
                if assignee:
                    line += f" - {assignee}"
                lines.append(line)
            lines.append("")
        
        # Deal value if present
        crm_entities = summary.get("crm_entities", {})
        deal_value = crm_entities.get("deal_value") if crm_entities else None
        if deal_value and deal_value.get("value"):
            currency = deal_value.get("currency", "₪")
            value = deal_value.get("value")
            lines.append(f"{t['deal_value_label']} {currency}{value:,.0f}")
            lines.append("")
        
        # Signature
        if sender_name:
            lines.append(t["signature"].format(sender_name=sender_name))
        
        message_text = "\n".join(lines)
        
        return WhatsAppMessage(
            recipient_phone=recipient_phone,
            message_text=message_text,
            template=MessageTemplate.SUMMARY,
            metadata={
                "client_name": client_name,
                "language": lang,
                "action_item_count": len(action_items),
            },
            created_at=datetime.utcnow(),
        )
    
    async def generate_action_items_message(
        self,
        action_items: List[Dict[str, Any]],
        client_name: str,
        language: Optional[str] = None,
        recipient_phone: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Generate a focused action items message.
        
        Args:
            action_items: List of action items from summary
            client_name: Name of the client/recipient
            language: Message language
            recipient_phone: Phone number
            
        Returns:
            WhatsAppMessage with action items
        """
        lang = language or self.default_language
        t = self.templates.get(lang, self.templates["en"])
        
        lines = [
            t["greeting"].format(name=client_name),
            "",
            t["action_items_header"],
        ]
        
        for idx, item in enumerate(action_items, 1):
            task = item.get("task", "")
            due = item.get("due")
            line = f"{idx}. {task}"
            if due:
                line += f" (עד: {due})" if lang == "he" else f" (by: {due})"
            lines.append(line)
        
        return WhatsAppMessage(
            recipient_phone=recipient_phone,
            message_text="\n".join(lines),
            template=MessageTemplate.ACTION_ITEMS,
            metadata={
                "client_name": client_name,
                "item_count": len(action_items),
            },
            created_at=datetime.utcnow(),
        )
    
    async def generate_follow_up_reminder(
        self,
        meeting_date: datetime,
        client_name: str,
        key_points: List[str],
        language: Optional[str] = None,
        recipient_phone: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Generate a follow-up reminder message.
        
        Args:
            meeting_date: Date of the original meeting
            client_name: Client name
            key_points: Key points to mention
            language: Message language
            recipient_phone: Phone number
            
        Returns:
            WhatsAppMessage for follow-up
        """
        lang = language or self.default_language
        t = self.templates.get(lang, self.templates["en"])
        
        date_str = meeting_date.strftime("%d/%m/%Y")
        
        lines = [
            t["greeting"].format(name=client_name),
            "",
            t["follow_up_intro"].format(date=date_str),
            "",
        ]
        
        if key_points:
            for point in key_points:
                lines.append(f"• {point}")
        
        return WhatsAppMessage(
            recipient_phone=recipient_phone,
            message_text="\n".join(lines),
            template=MessageTemplate.FOLLOW_UP,
            metadata={
                "meeting_date": date_str,
                "client_name": client_name,
            },
            created_at=datetime.utcnow(),
        )
    
    def format_phone_number(self, phone: str, country_code: str = "972") -> str:
        """
        Format phone number for WhatsApp API.
        
        Args:
            phone: Raw phone number
            country_code: Country code (default: Israel)
            
        Returns:
            Formatted phone number in international format
        """
        # Remove all non-digits
        digits = "".join(c for c in phone if c.isdigit())
        
        # Handle Israeli numbers
        if digits.startswith("0"):
            digits = country_code + digits[1:]
        elif not digits.startswith(country_code):
            digits = country_code + digits
        
        return digits


# Module instance for easy import
whatsapp_module = WhatsAppModule()
