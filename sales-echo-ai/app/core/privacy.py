"""
Privacy Utility - PII Redaction and Data Protection

This module provides functions to identify and mask sensitive personal information (PII)
before sending text to AI services or storing in logs.

Supported PII types:
- Email addresses
- Phone numbers (Israeli and international)
- Credit card numbers
- Israeli ID numbers (Teudat Zehut)
- Passport numbers
- Bank account numbers (IBAN)
- IP addresses
- Social security numbers (US)
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII that can be detected and redacted."""
    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    ISRAELI_ID = "israeli_id"
    PASSPORT = "passport"
    IBAN = "iban"
    IP_ADDRESS = "ip_address"
    SSN = "ssn"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"


@dataclass
class PIIMatch:
    """Represents a detected PII instance."""
    pii_type: PIIType
    original: str
    masked: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0


@dataclass
class RedactionResult:
    """Result of PII redaction operation."""
    original_text: str
    redacted_text: str
    matches: List[PIIMatch] = field(default_factory=list)
    pii_count: Dict[str, int] = field(default_factory=dict)
    
    @property
    def has_pii(self) -> bool:
        """Check if any PII was detected."""
        return len(self.matches) > 0
    
    @property
    def summary(self) -> str:
        """Get a summary of detected PII."""
        if not self.has_pii:
            return "No PII detected"
        parts = [f"{count} {pii_type}" for pii_type, count in self.pii_count.items()]
        return f"Detected: {', '.join(parts)}"


class PIIRedactor:
    """
    PII detection and redaction utility.
    
    Uses regex patterns to identify sensitive data and mask it with
    configurable replacement strings.
    """
    
    # Regex patterns for different PII types
    PATTERNS: Dict[PIIType, List[Tuple[str, str, float]]] = {
        # Email patterns
        PIIType.EMAIL: [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL]", 0.95),
        ],
        
        # Phone patterns (Israeli and international)
        PIIType.PHONE: [
            # Israeli mobile: 050-1234567, 052-123-4567, +972-50-1234567
            (r'\+972[-\s]?(?:50|51|52|53|54|55|58|59)[-\s]?\d{3}[-\s]?\d{4}\b', "[PHONE]", 0.95),
            (r'\b0(?:50|51|52|53|54|55|58|59)[-\s]?\d{3}[-\s]?\d{4}\b', "[PHONE]", 0.95),
            # Israeli landline: 02-1234567, 03-123-4567
            (r'\b0[2-9][-\s]?\d{3}[-\s]?\d{4}\b', "[PHONE]", 0.9),
            # International format
            (r'\+\d{1,3}[-\s]?\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}\b', "[PHONE]", 0.85),
            # Generic format (10-11 digits)
            (r'\b\d{10,11}\b', "[PHONE]", 0.5),  # Lower confidence - could be other numbers
        ],
        
        # Credit card patterns
        PIIType.CREDIT_CARD: [
            # Visa: 4xxx xxxx xxxx xxxx
            (r'\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "[CREDIT_CARD]", 0.95),
            # Mastercard: 5xxx xxxx xxxx xxxx
            (r'\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "[CREDIT_CARD]", 0.95),
            # Amex: 3xxx xxxxxx xxxxx
            (r'\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b', "[CREDIT_CARD]", 0.95),
            # Israeli credit: 16 digits
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "[CREDIT_CARD]", 0.7),
        ],
        
        # Israeli ID (Teudat Zehut) - 9 digits
        PIIType.ISRAELI_ID: [
            (r'\b\d{9}\b', "[IL_ID]", 0.5),  # Lower confidence - could be other 9-digit numbers
            # With context markers
            (r'(?:ת\.?ז\.?|ID|מספר זהות|תעודת זהות)[-:\s]?\d{9}\b', "[IL_ID]", 0.95),
        ],
        
        # Passport patterns
        PIIType.PASSPORT: [
            # Israeli passport: Letter followed by 7-8 digits
            (r'\b[A-Z]\d{7,8}\b', "[PASSPORT]", 0.6),
            # With context
            (r'(?:passport|דרכון)[-:\s]?[A-Z]?\d{7,9}\b', "[PASSPORT]", 0.9),
        ],
        
        # IBAN patterns
        PIIType.IBAN: [
            # Israeli IBAN: IL followed by 21 digits
            (r'\bIL\d{21}\b', "[IBAN]", 0.95),
            # Generic IBAN
            (r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b', "[IBAN]", 0.7),
        ],
        
        # IP Address patterns
        PIIType.IP_ADDRESS: [
            # IPv4
            (r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', "[IP]", 0.95),
            # IPv6 (simplified)
            (r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b', "[IP]", 0.95),
        ],
        
        # US Social Security Number
        PIIType.SSN: [
            (r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', "[SSN]", 0.7),
            # With context
            (r'(?:SSN|social security)[-:\s]?\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', "[SSN]", 0.95),
        ],
        
        # Date of birth patterns
        PIIType.DATE_OF_BIRTH: [
            # With context markers
            (r'(?:born|DOB|תאריך לידה|נולד)[-:\s]?\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b', "[DOB]", 0.9),
        ],
    }
    
    def __init__(
        self,
        enabled_types: Optional[List[PIIType]] = None,
        min_confidence: float = 0.7,
        preserve_structure: bool = True,
    ):
        """
        Initialize PII Redactor.
        
        Args:
            enabled_types: List of PII types to detect (None = all)
            min_confidence: Minimum confidence threshold for detection
            preserve_structure: If True, maintain text structure (e.g., "[EMAIL:8]" shows length)
        """
        self.enabled_types = enabled_types or list(PIIType)
        self.min_confidence = min_confidence
        self.preserve_structure = preserve_structure
        
        # Pre-compile regex patterns for performance
        self._compiled_patterns: Dict[PIIType, List[Tuple[re.Pattern, str, float]]] = {}
        for pii_type in self.enabled_types:
            if pii_type in self.PATTERNS:
                self._compiled_patterns[pii_type] = [
                    (re.compile(pattern, re.IGNORECASE), replacement, confidence)
                    for pattern, replacement, confidence in self.PATTERNS[pii_type]
                ]
    
    def redact(self, text: str) -> RedactionResult:
        """
        Detect and redact PII from text.
        
        Args:
            text: Input text to process
            
        Returns:
            RedactionResult with redacted text and match details
        """
        if not text:
            return RedactionResult(original_text="", redacted_text="", matches=[], pii_count={})
        
        matches: List[PIIMatch] = []
        pii_count: Dict[str, int] = {}
        
        # Detect all PII instances
        for pii_type, patterns in self._compiled_patterns.items():
            for compiled_pattern, replacement, confidence in patterns:
                if confidence < self.min_confidence:
                    continue
                
                for match in compiled_pattern.finditer(text):
                    original = match.group()
                    
                    # Generate masked value
                    if self.preserve_structure:
                        masked = f"{replacement[:-1]}:{len(original)}]"
                    else:
                        masked = replacement
                    
                    pii_match = PIIMatch(
                        pii_type=pii_type,
                        original=original,
                        masked=masked,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence,
                    )
                    matches.append(pii_match)
                    
                    # Count by type
                    type_name = pii_type.value
                    pii_count[type_name] = pii_count.get(type_name, 0) + 1
        
        # Sort matches by position (reverse order for replacement)
        matches.sort(key=lambda m: m.start_pos, reverse=True)
        
        # Apply redactions
        redacted_text = text
        for match in matches:
            redacted_text = (
                redacted_text[:match.start_pos] +
                match.masked +
                redacted_text[match.end_pos:]
            )
        
        # Re-sort matches by position (normal order for reporting)
        matches.sort(key=lambda m: m.start_pos)
        
        return RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            matches=matches,
            pii_count=pii_count,
        )
    
    def detect_only(self, text: str) -> List[PIIMatch]:
        """
        Detect PII without redacting.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected PII matches
        """
        result = self.redact(text)
        return result.matches
    
    def has_pii(self, text: str) -> bool:
        """
        Quick check if text contains any PII.
        
        Args:
            text: Input text to check
            
        Returns:
            True if PII detected, False otherwise
        """
        return self.redact(text).has_pii


# Default redactor instance
_default_redactor: Optional[PIIRedactor] = None


def get_redactor() -> PIIRedactor:
    """Get or create the default PII redactor."""
    global _default_redactor
    if _default_redactor is None:
        _default_redactor = PIIRedactor()
    return _default_redactor


def redact_pii(text: str, preserve_structure: bool = True) -> str:
    """
    Convenience function to redact PII from text.
    
    Args:
        text: Input text
        preserve_structure: If True, show length in placeholder
        
    Returns:
        Redacted text
    """
    redactor = PIIRedactor(preserve_structure=preserve_structure)
    result = redactor.redact(text)
    
    if result.has_pii:
        logger.info(f"PII redaction: {result.summary}")
    
    return result.redacted_text


def redact_pii_detailed(text: str) -> RedactionResult:
    """
    Redact PII and return detailed results.
    
    Args:
        text: Input text
        
    Returns:
        RedactionResult with full details
    """
    redactor = get_redactor()
    return redactor.redact(text)


def check_for_pii(text: str) -> Dict[str, int]:
    """
    Check text for PII without redacting.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dict mapping PII type to count
    """
    redactor = get_redactor()
    result = redactor.redact(text)
    return result.pii_count


# Specialized redaction functions

def redact_for_ai(text: str) -> str:
    """
    Redact PII before sending to AI services.
    
    Uses aggressive redaction settings to maximize privacy.
    
    Args:
        text: Input text (transcript, summary, etc.)
        
    Returns:
        Privacy-safe text for AI processing
    """
    redactor = PIIRedactor(
        min_confidence=0.5,  # Lower threshold = more aggressive
        preserve_structure=True,
    )
    result = redactor.redact(text)
    
    if result.has_pii:
        logger.warning(
            f"PII detected before AI processing: {result.summary}. "
            f"Text redacted from {len(text)} to {len(result.redacted_text)} chars."
        )
    
    return result.redacted_text


def redact_for_logs(text: str) -> str:
    """
    Redact PII for logging purposes.
    
    Uses standard redaction with structure preserved.
    
    Args:
        text: Text to be logged
        
    Returns:
        Log-safe text
    """
    return redact_pii(text, preserve_structure=True)


def redact_transcript(transcript: str) -> Tuple[str, Dict[str, int]]:
    """
    Redact PII from a transcript before AI analysis.
    
    Args:
        transcript: Full transcript text
        
    Returns:
        Tuple of (redacted_transcript, pii_counts)
    """
    result = redact_pii_detailed(transcript)
    return result.redacted_text, result.pii_count


# Hebrew-specific patterns helper
def add_hebrew_patterns():
    """
    Add additional Hebrew-specific PII patterns.
    
    This extends the default patterns with Hebrew language markers.
    """
    hebrew_patterns = {
        PIIType.PHONE: [
            # Hebrew markers for phone
            (r'(?:טלפון|נייד|פלאפון)[-:\s]?\d{2,3}[-\s]?\d{7}\b', "[PHONE]", 0.95),
        ],
        PIIType.EMAIL: [
            # Hebrew markers for email  
            (r'(?:מייל|דואל|אימייל)[-:\s]?[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL]", 0.95),
        ],
        PIIType.CREDIT_CARD: [
            # Hebrew markers for credit card
            (r'(?:כרטיס אשראי|כרטיס)[-:\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "[CREDIT_CARD]", 0.95),
        ],
    }
    
    for pii_type, patterns in hebrew_patterns.items():
        if pii_type in PIIRedactor.PATTERNS:
            PIIRedactor.PATTERNS[pii_type].extend(patterns)
        else:
            PIIRedactor.PATTERNS[pii_type] = patterns


# Initialize Hebrew patterns on module load
add_hebrew_patterns()
