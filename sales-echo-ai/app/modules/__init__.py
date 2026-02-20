"""
SalesEcho AI - Action Modules

This package contains specialized modules for handling different action types
extracted from sales call summaries. Each module is responsible for a specific
integration or communication channel.

Modules:
- whatsapp: WhatsApp message formatting and delivery
- email: Professional email draft generation
- calendar: Calendar event creation and scheduling
- crm_adapter: CRM integration (HubSpot, Priority, etc.)
"""

from .whatsapp import WhatsAppModule
from .email import EmailModule
from .calendar import CalendarModule
from .crm_adapter import CRMAdapter

__all__ = [
    "WhatsAppModule",
    "EmailModule", 
    "CalendarModule",
    "CRMAdapter",
]
