"""
Action Dispatcher

Central orchestration engine for processing AI summaries and dispatching
actions to appropriate modules (WhatsApp, Email, Calendar, CRM).

This dispatcher is designed to:
1. Parse AI-generated summaries for actionable intents
2. Route actions to specialized modules
3. Handle failures gracefully with retries
4. Maintain audit trails for all dispatched actions
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import traceback

from app.modules.whatsapp import WhatsAppModule, WhatsAppMessage
from app.modules.email import EmailModule, EmailDraft
from app.modules.calendar import CalendarModule, CalendarEvent
from app.modules.crm_adapter import CRMAdapter, SyncResult

logger = logging.getLogger(__name__)


class ActionIntent(Enum):
    """Recognized action intents from AI summaries."""
    SEND_WHATSAPP = "send_whatsapp"
    SEND_EMAIL = "send_email"
    SCHEDULE_MEETING = "schedule_meeting"
    CREATE_TASK = "create_task"
    UPDATE_CRM = "update_crm"
    CREATE_CONTACT = "create_contact"
    SEND_FOLLOW_UP = "send_follow_up"
    SET_REMINDER = "set_reminder"


class ActionStatus(Enum):
    """Status of dispatched actions."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class ActionResult:
    """Result of a dispatched action."""
    action_id: str
    intent: ActionIntent
    status: ActionStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "intent": self.intent.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


@dataclass
class DispatchContext:
    """Context for action dispatch operations."""
    meeting_id: str
    org_id: str
    user_id: str
    summary: Dict[str, Any]
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    language: str = "he"
    dry_run: bool = False


class ActionDispatcher:
    """
    Central dispatcher for processing AI summaries and triggering actions.
    
    The dispatcher analyzes AI-generated meeting summaries, identifies
    actionable intents, and routes them to appropriate handler modules.
    
    Features:
    - Intent detection from summary content
    - Async parallel action execution
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    - Action audit trail
    """
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    DEFAULT_TIMEOUT = 30.0  # seconds
    
    def __init__(
        self,
        whatsapp_module: Optional[WhatsAppModule] = None,
        email_module: Optional[EmailModule] = None,
        calendar_module: Optional[CalendarModule] = None,
        crm_adapter: Optional[CRMAdapter] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize the Action Dispatcher.
        
        Args:
            whatsapp_module: WhatsApp module instance
            email_module: Email module instance
            calendar_module: Calendar module instance
            crm_adapter: CRM adapter instance
            max_retries: Maximum retry attempts for failed actions
            retry_delay: Base delay between retries (exponential backoff)
            timeout: Action execution timeout in seconds
        """
        self.whatsapp = whatsapp_module or WhatsAppModule()
        self.email = email_module or EmailModule()
        self.calendar = calendar_module or CalendarModule()
        self.crm = crm_adapter or CRMAdapter()
        
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # Action history for audit
        self._action_history: List[ActionResult] = []
        
        # Register intent handlers
        self._handlers: Dict[ActionIntent, Callable] = {
            ActionIntent.SEND_WHATSAPP: self._handle_whatsapp,
            ActionIntent.SEND_EMAIL: self._handle_email,
            ActionIntent.SCHEDULE_MEETING: self._handle_schedule,
            ActionIntent.CREATE_TASK: self._handle_create_task,
            ActionIntent.UPDATE_CRM: self._handle_crm_update,
            ActionIntent.CREATE_CONTACT: self._handle_create_contact,
            ActionIntent.SEND_FOLLOW_UP: self._handle_follow_up,
            ActionIntent.SET_REMINDER: self._handle_reminder,
        }
    
    async def process_summary(
        self,
        context: DispatchContext,
        auto_dispatch: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a meeting summary and identify/execute actions.
        
        Args:
            context: Dispatch context with meeting data
            auto_dispatch: Whether to automatically execute detected actions
            
        Returns:
            Dictionary with detected intents and results
        """
        logger.info(f"Processing summary for meeting {context.meeting_id}")
        
        # Detect intents from summary
        detected_intents = await self.detect_intents(context.summary)
        
        results = {
            "meeting_id": context.meeting_id,
            "detected_intents": [i.value for i in detected_intents],
            "actions": [],
            "processed_at": datetime.utcnow().isoformat(),
        }
        
        if auto_dispatch and not context.dry_run:
            # Execute all detected actions
            action_results = await self.dispatch_all(detected_intents, context)
            results["actions"] = [r.to_dict() for r in action_results]
        
        return results
    
    async def detect_intents(self, summary: Dict[str, Any]) -> List[ActionIntent]:
        """
        Analyze summary content to detect actionable intents.
        
        Args:
            summary: Meeting summary content
            
        Returns:
            List of detected ActionIntent
        """
        intents = []
        
        # Check for action items -> task creation
        action_items = summary.get("action_items", [])
        if action_items:
            intents.append(ActionIntent.CREATE_TASK)
        
        # Check for CRM entities -> CRM update
        crm_entities = summary.get("crm_entities", {})
        if crm_entities:
            deal_value = crm_entities.get("deal_value")
            contact_email = crm_entities.get("contact_email")
            
            if deal_value and deal_value.get("value"):
                intents.append(ActionIntent.UPDATE_CRM)
            
            if contact_email and contact_email.get("value"):
                intents.append(ActionIntent.CREATE_CONTACT)
        
        # Check for next meeting date -> scheduling
        if crm_entities:
            next_meeting = crm_entities.get("next_meeting_date")
            if next_meeting and next_meeting.get("value"):
                intents.append(ActionIntent.SCHEDULE_MEETING)
        
        # Always suggest follow-up for completed meetings
        if summary.get("summary_text"):
            intents.append(ActionIntent.SEND_FOLLOW_UP)
        
        # Deduplicate while preserving order
        seen = set()
        unique_intents = []
        for intent in intents:
            if intent not in seen:
                seen.add(intent)
                unique_intents.append(intent)
        
        logger.info(f"Detected intents: {[i.value for i in unique_intents]}")
        return unique_intents
    
    async def dispatch_all(
        self,
        intents: List[ActionIntent],
        context: DispatchContext,
    ) -> List[ActionResult]:
        """
        Dispatch all detected intents in parallel.
        
        Args:
            intents: List of intents to dispatch
            context: Dispatch context
            
        Returns:
            List of ActionResult
        """
        if not intents:
            return []
        
        # Create tasks for parallel execution
        tasks = []
        for intent in intents:
            task = asyncio.create_task(
                self.dispatch_single(intent, context),
                name=f"dispatch_{intent.value}",
            )
            tasks.append(task)
        
        # Wait for all with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout * len(tasks),
            )
        except asyncio.TimeoutError:
            logger.error("Dispatch timeout - some actions may not have completed")
            results = []
            for task in tasks:
                if task.done():
                    results.append(task.result())
                else:
                    task.cancel()
                    results.append(ActionResult(
                        action_id=f"timeout_{datetime.utcnow().timestamp()}",
                        intent=ActionIntent.SEND_FOLLOW_UP,
                        status=ActionStatus.FAILED,
                        error="Action timed out",
                    ))
        
        # Process results
        action_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                intent = intents[i] if i < len(intents) else ActionIntent.SEND_FOLLOW_UP
                action_results.append(ActionResult(
                    action_id=f"error_{datetime.utcnow().timestamp()}",
                    intent=intent,
                    status=ActionStatus.FAILED,
                    error=str(result),
                ))
            elif isinstance(result, ActionResult):
                action_results.append(result)
        
        # Store in history
        self._action_history.extend(action_results)
        
        return action_results
    
    async def dispatch_single(
        self,
        intent: ActionIntent,
        context: DispatchContext,
        retry_count: int = 0,
    ) -> ActionResult:
        """
        Dispatch a single action with retry logic.
        
        Args:
            intent: The action intent to dispatch
            context: Dispatch context
            retry_count: Current retry attempt
            
        Returns:
            ActionResult
        """
        import uuid
        action_id = str(uuid.uuid4())
        
        result = ActionResult(
            action_id=action_id,
            intent=intent,
            status=ActionStatus.IN_PROGRESS,
            retry_count=retry_count,
        )
        
        handler = self._handlers.get(intent)
        if not handler:
            result.status = ActionStatus.FAILED
            result.error = f"No handler for intent: {intent.value}"
            result.completed_at = datetime.utcnow()
            return result
        
        try:
            # Execute handler with timeout
            handler_result = await asyncio.wait_for(
                handler(context),
                timeout=self.timeout,
            )
            
            result.status = ActionStatus.COMPLETED
            result.result = handler_result
            result.completed_at = datetime.utcnow()
            
            logger.info(f"Action {intent.value} completed successfully")
            
        except asyncio.TimeoutError:
            result.status = ActionStatus.FAILED
            result.error = "Handler execution timed out"
            result.completed_at = datetime.utcnow()
            logger.error(f"Action {intent.value} timed out")
            
        except Exception as e:
            logger.error(f"Action {intent.value} failed: {str(e)}")
            
            # Retry logic
            if retry_count < self.max_retries:
                result.status = ActionStatus.RETRYING
                delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                
                logger.info(f"Retrying {intent.value} in {delay}s (attempt {retry_count + 1})")
                await asyncio.sleep(delay)
                
                return await self.dispatch_single(intent, context, retry_count + 1)
            
            result.status = ActionStatus.FAILED
            result.error = str(e)
            result.metadata["traceback"] = traceback.format_exc()
            result.completed_at = datetime.utcnow()
        
        return result
    
    # ==================== Intent Handlers ====================
    
    async def _handle_whatsapp(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle WhatsApp message generation."""
        message = await self.whatsapp.generate_summary_message(
            summary=context.summary,
            client_name=context.client_name or "Client",
            sender_name=context.sender_name,
            language=context.language,
            recipient_phone=context.client_phone,
        )
        
        return {
            "type": "whatsapp",
            "message": message.message_text,
            "wa_me_url": message.to_wa_me_url(),
            "template": message.template.value,
        }
    
    async def _handle_email(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle email draft generation."""
        if not context.client_email:
            raise ValueError("Client email required for email dispatch")
        
        draft = await self.email.generate_follow_up_email(
            summary=context.summary,
            recipient_email=context.client_email,
            recipient_name=context.client_name or "Client",
            sender_name=context.sender_name or "SalesEcho AI",
            language=context.language,
        )
        
        return draft.to_dict()
    
    async def _handle_schedule(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle calendar event creation."""
        events = await self.calendar.extract_events_from_summary(
            summary=context.summary,
            client_name=context.client_name or "Client",
            client_email=context.client_email,
            organizer_email=context.sender_email,
        )
        
        return {
            "type": "calendar",
            "events": [
                {
                    "title": e.title,
                    "start": e.start_time.isoformat(),
                    "end": e.end_time.isoformat(),
                    "google_format": e.to_google_format(),
                    "ical": e.to_ical(),
                }
                for e in events
            ],
        }
    
    async def _handle_create_task(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle task creation in CRM."""
        results = []
        action_items = context.summary.get("action_items", [])
        
        for item in action_items:
            result = await self.crm.create_task(
                title=item.get("task", "Follow up"),
                description=f"From meeting {context.meeting_id}",
                contact_id=None,  # Would need contact lookup
            )
            results.append(result.to_dict())
        
        return {
            "type": "tasks",
            "created_count": len(results),
            "results": results,
        }
    
    async def _handle_crm_update(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle CRM sync (contacts, deals, tasks, notes)."""
        results = await self.crm.sync_meeting_to_crm(
            meeting_id=context.meeting_id,
            summary=context.summary,
            client_name=context.client_name,
            client_email=context.client_email,
            create_contact=True,
            create_tasks=True,
            create_note=True,
        )
        
        return {
            "type": "crm_sync",
            "sync_results": [r.to_dict() for r in results],
            "success_count": sum(1 for r in results if r.success),
            "failure_count": sum(1 for r in results if not r.success),
        }
    
    async def _handle_create_contact(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle contact creation in CRM."""
        # Parse name
        first_name, last_name = "", ""
        if context.client_name:
            parts = context.client_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
        
        result = await self.crm.create_contact(
            email=context.client_email,
            first_name=first_name,
            last_name=last_name,
            phone=context.client_phone,
        )
        
        return result.to_dict()
    
    async def _handle_follow_up(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle follow-up generation (WhatsApp + Email combo)."""
        results = {}
        
        # Generate WhatsApp message
        whatsapp_msg = await self.whatsapp.generate_summary_message(
            summary=context.summary,
            client_name=context.client_name or "Client",
            sender_name=context.sender_name,
            language=context.language,
        )
        results["whatsapp"] = {
            "message": whatsapp_msg.message_text,
            "wa_me_url": whatsapp_msg.to_wa_me_url(),
        }
        
        # Generate email if we have an address
        if context.client_email:
            email_draft = await self.email.generate_follow_up_email(
                summary=context.summary,
                recipient_email=context.client_email,
                recipient_name=context.client_name or "Client",
                sender_name=context.sender_name or "SalesEcho AI",
                language=context.language,
            )
            results["email"] = email_draft.to_dict()
        
        return {
            "type": "follow_up",
            "channels": results,
        }
    
    async def _handle_reminder(self, context: DispatchContext) -> Dict[str, Any]:
        """Handle reminder creation."""
        # Extract action items with due dates
        action_items = context.summary.get("action_items", [])
        reminders = []
        
        for item in action_items:
            due = item.get("due")
            if due:
                reminders.append({
                    "task": item.get("task"),
                    "due": due,
                    "assignee": item.get("assignee"),
                })
        
        return {
            "type": "reminders",
            "reminder_count": len(reminders),
            "reminders": reminders,
        }
    
    # ==================== Utility Methods ====================
    
    def get_action_history(
        self,
        meeting_id: Optional[str] = None,
        intent: Optional[ActionIntent] = None,
        status: Optional[ActionStatus] = None,
        limit: int = 100,
    ) -> List[ActionResult]:
        """
        Get action history with optional filters.
        
        Args:
            meeting_id: Filter by meeting ID
            intent: Filter by intent type
            status: Filter by status
            limit: Maximum results to return
            
        Returns:
            List of ActionResult matching filters
        """
        results = self._action_history
        
        if meeting_id:
            results = [r for r in results if r.metadata.get("meeting_id") == meeting_id]
        if intent:
            results = [r for r in results if r.intent == intent]
        if status:
            results = [r for r in results if r.status == status]
        
        return results[-limit:]
    
    def clear_history(self) -> None:
        """Clear action history."""
        self._action_history = []


# Singleton dispatcher instance
_dispatcher: Optional[ActionDispatcher] = None


def get_dispatcher() -> ActionDispatcher:
    """Get or create the global dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = ActionDispatcher()
    return _dispatcher


async def dispatch_meeting_actions(
    meeting_id: str,
    org_id: str,
    user_id: str,
    summary: Dict[str, Any],
    client_name: Optional[str] = None,
    client_email: Optional[str] = None,
    auto_dispatch: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to dispatch actions for a meeting.
    
    Args:
        meeting_id: Meeting ID
        org_id: Organization ID
        user_id: User ID
        summary: Meeting summary
        client_name: Client name
        client_email: Client email
        auto_dispatch: Whether to auto-execute actions
        
    Returns:
        Dispatch results
    """
    dispatcher = get_dispatcher()
    context = DispatchContext(
        meeting_id=meeting_id,
        org_id=org_id,
        user_id=user_id,
        summary=summary,
        client_name=client_name,
        client_email=client_email,
    )
    
    return await dispatcher.process_summary(context, auto_dispatch=auto_dispatch)
