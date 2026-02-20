"""
CRM Adapter Module

Unified interface for CRM integrations (HubSpot, Priority, Salesforce, etc.)
Handles contact creation, deal updates, task creation, and data sync.
"""

import logging
from typing import Optional, Dict, Any, List, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import uuid

logger = logging.getLogger(__name__)


class CRMProvider(Enum):
    """Supported CRM providers."""
    HUBSPOT = "hubspot"
    PRIORITY = "priority"
    SALESFORCE = "salesforce"
    PIPEDRIVE = "pipedrive"
    MOCK = "mock"  # For development/testing


class EntityType(Enum):
    """CRM entity types."""
    CONTACT = "contact"
    COMPANY = "company"
    DEAL = "deal"
    TASK = "task"
    NOTE = "note"
    MEETING = "meeting"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DealStage(Enum):
    """Standard deal stages."""
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


@dataclass
class CRMContact:
    """Standardized contact entity."""
    id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    source: str = "salesecho"
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or "Unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "company": self.company,
            "job_title": self.job_title,
            "source": self.source,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CRMDeal:
    """Standardized deal/opportunity entity."""
    id: Optional[str] = None
    name: str = ""
    value: float = 0.0
    currency: str = "ILS"
    stage: DealStage = DealStage.LEAD
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    probability: int = 0
    notes: str = ""
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "currency": self.currency,
            "stage": self.stage.value,
            "contact_id": self.contact_id,
            "company_id": self.company_id,
            "expected_close_date": self.expected_close_date.isoformat() if self.expected_close_date else None,
            "probability": self.probability,
            "notes": self.notes,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CRMTask:
    """Standardized task entity."""
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    due_date: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[str] = None
    contact_id: Optional[str] = None
    deal_id: Optional[str] = None
    status: str = "open"
    completed: bool = False
    source_meeting_id: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority.value,
            "assignee_id": self.assignee_id,
            "contact_id": self.contact_id,
            "deal_id": self.deal_id,
            "status": self.status,
            "completed": self.completed,
            "source_meeting_id": self.source_meeting_id,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CRMNote:
    """Standardized note/activity entity."""
    id: Optional[str] = None
    content: str = ""
    contact_id: Optional[str] = None
    deal_id: Optional[str] = None
    meeting_id: Optional[str] = None
    note_type: str = "meeting_summary"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "contact_id": self.contact_id,
            "deal_id": self.deal_id,
            "meeting_id": self.meeting_id,
            "note_type": self.note_type,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SyncResult:
    """Result of a CRM sync operation."""
    success: bool
    entity_type: EntityType
    entity_id: Optional[str] = None
    provider: CRMProvider = CRMProvider.MOCK
    message: str = ""
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    synced_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "provider": self.provider.value,
            "message": self.message,
            "errors": self.errors,
            "metadata": self.metadata,
            "synced_at": self.synced_at.isoformat(),
        }


class CRMProviderInterface(ABC):
    """Abstract interface for CRM providers."""
    
    @abstractmethod
    async def create_contact(self, contact: CRMContact) -> SyncResult:
        pass
    
    @abstractmethod
    async def update_contact(self, contact_id: str, data: Dict[str, Any]) -> SyncResult:
        pass
    
    @abstractmethod
    async def create_deal(self, deal: CRMDeal) -> SyncResult:
        pass
    
    @abstractmethod
    async def update_deal(self, deal_id: str, data: Dict[str, Any]) -> SyncResult:
        pass
    
    @abstractmethod
    async def create_task(self, task: CRMTask) -> SyncResult:
        pass
    
    @abstractmethod
    async def create_note(self, note: CRMNote) -> SyncResult:
        pass
    
    @abstractmethod
    async def search_contacts(self, query: str) -> List[CRMContact]:
        pass


class MockCRMProvider(CRMProviderInterface):
    """
    Mock CRM provider for development and testing.
    
    Simulates CRM operations without external API calls.
    """
    
    def __init__(self):
        self.contacts: Dict[str, CRMContact] = {}
        self.deals: Dict[str, CRMDeal] = {}
        self.tasks: Dict[str, CRMTask] = {}
        self.notes: Dict[str, CRMNote] = {}
    
    async def create_contact(self, contact: CRMContact) -> SyncResult:
        """Create a mock contact."""
        contact_id = str(uuid.uuid4())
        contact.id = contact_id
        self.contacts[contact_id] = contact
        
        logger.info(f"[MockCRM] Created contact: {contact.full_name} ({contact_id})")
        
        return SyncResult(
            success=True,
            entity_type=EntityType.CONTACT,
            entity_id=contact_id,
            provider=CRMProvider.MOCK,
            message=f"Contact '{contact.full_name}' created successfully",
            metadata={"contact": contact.to_dict()},
        )
    
    async def update_contact(self, contact_id: str, data: Dict[str, Any]) -> SyncResult:
        """Update a mock contact."""
        if contact_id not in self.contacts:
            return SyncResult(
                success=False,
                entity_type=EntityType.CONTACT,
                entity_id=contact_id,
                provider=CRMProvider.MOCK,
                message="Contact not found",
                errors=["Contact ID does not exist"],
            )
        
        contact = self.contacts[contact_id]
        for key, value in data.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        logger.info(f"[MockCRM] Updated contact: {contact_id}")
        
        return SyncResult(
            success=True,
            entity_type=EntityType.CONTACT,
            entity_id=contact_id,
            provider=CRMProvider.MOCK,
            message="Contact updated successfully",
        )
    
    async def create_deal(self, deal: CRMDeal) -> SyncResult:
        """Create a mock deal."""
        deal_id = str(uuid.uuid4())
        deal.id = deal_id
        self.deals[deal_id] = deal
        
        logger.info(f"[MockCRM] Created deal: {deal.name} (₪{deal.value:,.0f})")
        
        return SyncResult(
            success=True,
            entity_type=EntityType.DEAL,
            entity_id=deal_id,
            provider=CRMProvider.MOCK,
            message=f"Deal '{deal.name}' created successfully",
            metadata={"deal": deal.to_dict()},
        )
    
    async def update_deal(self, deal_id: str, data: Dict[str, Any]) -> SyncResult:
        """Update a mock deal."""
        if deal_id not in self.deals:
            return SyncResult(
                success=False,
                entity_type=EntityType.DEAL,
                entity_id=deal_id,
                provider=CRMProvider.MOCK,
                message="Deal not found",
                errors=["Deal ID does not exist"],
            )
        
        deal = self.deals[deal_id]
        for key, value in data.items():
            if hasattr(deal, key):
                setattr(deal, key, value)
        
        logger.info(f"[MockCRM] Updated deal: {deal_id}")
        
        return SyncResult(
            success=True,
            entity_type=EntityType.DEAL,
            entity_id=deal_id,
            provider=CRMProvider.MOCK,
            message="Deal updated successfully",
        )
    
    async def create_task(self, task: CRMTask) -> SyncResult:
        """Create a mock task."""
        task_id = str(uuid.uuid4())
        task.id = task_id
        self.tasks[task_id] = task
        
        logger.info(f"[MockCRM] Created task: {task.title}")
        
        return SyncResult(
            success=True,
            entity_type=EntityType.TASK,
            entity_id=task_id,
            provider=CRMProvider.MOCK,
            message=f"Task '{task.title}' created successfully",
            metadata={"task": task.to_dict()},
        )
    
    async def create_note(self, note: CRMNote) -> SyncResult:
        """Create a mock note."""
        note_id = str(uuid.uuid4())
        note.id = note_id
        self.notes[note_id] = note
        
        logger.info(f"[MockCRM] Created note for meeting: {note.meeting_id}")
        
        return SyncResult(
            success=True,
            entity_type=EntityType.NOTE,
            entity_id=note_id,
            provider=CRMProvider.MOCK,
            message="Note created successfully",
            metadata={"note": note.to_dict()},
        )
    
    async def search_contacts(self, query: str) -> List[CRMContact]:
        """Search mock contacts."""
        query_lower = query.lower()
        results = []
        
        for contact in self.contacts.values():
            if (
                query_lower in (contact.email or "").lower()
                or query_lower in contact.full_name.lower()
                or query_lower in (contact.company or "").lower()
            ):
                results.append(contact)
        
        return results


class CRMAdapter:
    """
    Unified CRM adapter supporting multiple providers.
    
    Provides a consistent interface for CRM operations across
    different CRM systems (HubSpot, Priority, Salesforce, etc.)
    """
    
    def __init__(self, provider: CRMProvider = CRMProvider.MOCK):
        """
        Initialize CRM adapter.
        
        Args:
            provider: CRM provider to use
        """
        self.provider = provider
        self._client = self._create_client(provider)
    
    def _create_client(self, provider: CRMProvider) -> CRMProviderInterface:
        """Create the appropriate CRM client."""
        if provider == CRMProvider.MOCK:
            return MockCRMProvider()
        elif provider == CRMProvider.HUBSPOT:
            # TODO: Implement HubSpot client
            logger.warning("HubSpot not implemented, falling back to mock")
            return MockCRMProvider()
        elif provider == CRMProvider.PRIORITY:
            # TODO: Implement Priority client
            logger.warning("Priority not implemented, falling back to mock")
            return MockCRMProvider()
        else:
            logger.warning(f"Unknown provider {provider}, using mock")
            return MockCRMProvider()
    
    async def sync_meeting_to_crm(
        self,
        meeting_id: str,
        summary: Dict[str, Any],
        client_name: Optional[str] = None,
        client_email: Optional[str] = None,
        create_contact: bool = True,
        create_tasks: bool = True,
        create_note: bool = True,
    ) -> List[SyncResult]:
        """
        Sync a meeting and its summary to CRM.
        
        Args:
            meeting_id: Internal meeting ID
            summary: Meeting summary content
            client_name: Client name for contact creation
            client_email: Client email for contact lookup/creation
            create_contact: Whether to create/update contact
            create_tasks: Whether to create tasks from action items
            create_note: Whether to create a meeting note
            
        Returns:
            List of SyncResult for each operation
        """
        results = []
        contact_id = None
        deal_id = None
        
        # Step 1: Create or find contact
        if create_contact and (client_name or client_email):
            contact_result = await self._sync_contact(client_name, client_email, summary)
            results.append(contact_result)
            if contact_result.success:
                contact_id = contact_result.entity_id
        
        # Step 2: Create/update deal if deal value present
        crm_entities = summary.get("crm_entities", {})
        deal_value = crm_entities.get("deal_value") if crm_entities else None
        if deal_value and deal_value.get("value"):
            deal_result = await self._sync_deal(
                client_name or "Unknown",
                deal_value,
                contact_id,
                summary,
            )
            results.append(deal_result)
            if deal_result.success:
                deal_id = deal_result.entity_id
        
        # Step 3: Create tasks from action items
        if create_tasks:
            action_items = summary.get("action_items", [])
            for item in action_items:
                task_result = await self._create_task_from_action_item(
                    item, meeting_id, contact_id, deal_id
                )
                results.append(task_result)
        
        # Step 4: Create meeting note
        if create_note:
            note_result = await self._create_meeting_note(
                meeting_id, summary, contact_id, deal_id
            )
            results.append(note_result)
        
        return results
    
    async def _sync_contact(
        self,
        client_name: Optional[str],
        client_email: Optional[str],
        summary: Dict[str, Any],
    ) -> SyncResult:
        """Create or update contact from meeting data."""
        # Parse name into first/last
        first_name, last_name = "", ""
        if client_name:
            parts = client_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
        
        # Extract contact email from CRM entities if not provided
        if not client_email:
            crm_entities = summary.get("crm_entities", {})
            contact_email_entity = crm_entities.get("contact_email") if crm_entities else None
            if contact_email_entity:
                client_email = contact_email_entity.get("value")
        
        contact = CRMContact(
            email=client_email,
            first_name=first_name,
            last_name=last_name,
            source="salesecho_meeting",
            custom_fields={
                "last_meeting_date": datetime.utcnow().isoformat(),
            },
        )
        
        return await self._client.create_contact(contact)
    
    async def _sync_deal(
        self,
        client_name: str,
        deal_value: Dict[str, Any],
        contact_id: Optional[str],
        summary: Dict[str, Any],
    ) -> SyncResult:
        """Create or update deal from meeting data."""
        value = deal_value.get("value", 0)
        currency = deal_value.get("currency", "ILS")
        
        # Determine stage based on deal heat
        governance = summary.get("governance", {})
        confidence = governance.get("confidence_score", 0.5)
        
        if confidence >= 0.8:
            stage = DealStage.PROPOSAL
        elif confidence >= 0.6:
            stage = DealStage.QUALIFIED
        else:
            stage = DealStage.LEAD
        
        deal = CRMDeal(
            name=f"Deal - {client_name}",
            value=value,
            currency=currency,
            stage=stage,
            contact_id=contact_id,
            probability=int(confidence * 100),
            notes=summary.get("summary_text", ""),
        )
        
        return await self._client.create_deal(deal)
    
    async def _create_task_from_action_item(
        self,
        action_item: Dict[str, Any],
        meeting_id: str,
        contact_id: Optional[str],
        deal_id: Optional[str],
    ) -> SyncResult:
        """Create a CRM task from an action item."""
        title = action_item.get("task", "Follow up")
        due = action_item.get("due")
        assignee = action_item.get("assignee")
        confidence = action_item.get("confidence", 0.5)
        
        # Parse due date
        due_date = None
        if due:
            try:
                # Simple date parsing - could be enhanced
                from .calendar import calendar_module
                due_date = calendar_module._parse_date_string(due)
            except Exception:
                pass
        
        # Determine priority based on confidence
        if confidence >= 0.9:
            priority = TaskPriority.HIGH
        elif confidence >= 0.7:
            priority = TaskPriority.MEDIUM
        else:
            priority = TaskPriority.LOW
        
        task = CRMTask(
            title=title[:100],  # Truncate if too long
            description=f"Action item from meeting.\n\nOriginal: {title}",
            due_date=due_date,
            priority=priority,
            contact_id=contact_id,
            deal_id=deal_id,
            source_meeting_id=meeting_id,
            custom_fields={
                "assignee_name": assignee,
                "confidence": confidence,
                "source": action_item.get("source"),
            },
        )
        
        return await self._client.create_task(task)
    
    async def _create_meeting_note(
        self,
        meeting_id: str,
        summary: Dict[str, Any],
        contact_id: Optional[str],
        deal_id: Optional[str],
    ) -> SyncResult:
        """Create a CRM note with meeting summary."""
        # Build note content
        content_parts = ["## Meeting Summary", ""]
        
        summary_text = summary.get("summary_text", "")
        if summary_text:
            content_parts.append(summary_text)
            content_parts.append("")
        
        # Add action items
        action_items = summary.get("action_items", [])
        if action_items:
            content_parts.append("### Action Items")
            for item in action_items:
                task = item.get("task", "")
                content_parts.append(f"- {task}")
            content_parts.append("")
        
        # Add governance info
        governance = summary.get("governance", {})
        if governance:
            confidence = governance.get("confidence_score", 0)
            content_parts.append(f"*Confidence Score: {confidence:.0%}*")
        
        note = CRMNote(
            content="\n".join(content_parts),
            contact_id=contact_id,
            deal_id=deal_id,
            meeting_id=meeting_id,
            note_type="meeting_summary",
        )
        
        return await self._client.create_note(note)
    
    async def create_contact(
        self,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        job_title: Optional[str] = None,
    ) -> SyncResult:
        """
        Create a new contact in CRM.
        
        Args:
            email: Contact email
            first_name: First name
            last_name: Last name
            phone: Phone number
            company: Company name
            job_title: Job title
            
        Returns:
            SyncResult with contact ID
        """
        contact = CRMContact(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            company=company,
            job_title=job_title,
        )
        return await self._client.create_contact(contact)
    
    async def create_task(
        self,
        title: str,
        description: str = "",
        due_date: Optional[datetime] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        contact_id: Optional[str] = None,
        deal_id: Optional[str] = None,
    ) -> SyncResult:
        """
        Create a new task in CRM.
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date
            priority: Task priority
            contact_id: Associated contact ID
            deal_id: Associated deal ID
            
        Returns:
            SyncResult with task ID
        """
        task = CRMTask(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            contact_id=contact_id,
            deal_id=deal_id,
        )
        return await self._client.create_task(task)


# Module instance for easy import
crm_adapter = CRMAdapter()
