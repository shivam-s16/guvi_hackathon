"""
Pydantic models for request/response schemas.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SenderType(str, Enum):
    """Message sender type."""
    SCAMMER = "scammer"
    USER = "user"


class ChannelType(str, Enum):
    """Communication channel type."""
    SMS = "SMS"
    WHATSAPP = "WhatsApp"
    EMAIL = "Email"
    CHAT = "Chat"


# ============= Request Models =============

class Message(BaseModel):
    """Individual message in a conversation."""
    sender: SenderType
    text: str
    timestamp: datetime


class ConversationMessage(BaseModel):
    """Message in conversation history."""
    sender: SenderType
    text: str
    timestamp: datetime


class Metadata(BaseModel):
    """Request metadata."""
    channel: Optional[ChannelType] = ChannelType.SMS
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"


class HoneypotRequest(BaseModel):
    """Incoming API request model."""
    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Current incoming message")
    conversationHistory: List[ConversationMessage] = Field(
        default=[],
        description="Previous messages in the conversation"
    )
    metadata: Optional[Metadata] = Field(default=None, description="Optional metadata")


# ============= Response Models =============

class EngagementMetrics(BaseModel):
    """Metrics about the engagement with the scammer."""
    engagementDurationSeconds: int = 0
    totalMessagesExchanged: int = 0


class ExtractedIntelligence(BaseModel):
    """Intelligence extracted from the conversation."""
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)
    emailAddresses: List[str] = Field(default_factory=list)

class BehaviorMetricsResponse(BaseModel):
    """Behavioral analysis metrics."""
    intentConfidence: float = 0.0
    escalationRate: int = 0
    aggressionSlope: float = 0.0


class HoneypotResponse(BaseModel):
    """API response model - detailed version."""
    status: str = "success"
    scamDetected: bool = False
    scamConfidence: float = 0.0  # 0-1 confidence score
    agentResponse: Optional[str] = None
    engagementMetrics: EngagementMetrics = Field(default_factory=EngagementMetrics)
    extractedIntelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    behaviorMetrics: BehaviorMetricsResponse = Field(default_factory=BehaviorMetricsResponse)
    agentNotes: str = ""
    sessionActive: bool = True



class SimpleResponse(BaseModel):
    """
    Simple API response model - as per GUVI evaluation format.
    
    Example:
    {
        "status": "success",
        "reply": "Why is my account being suspended?"
    }
    """
    status: str = "success"
    reply: str = ""


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = "error"
    error: str
    details: Optional[str] = None


# ============= Session Models =============

class SessionData(BaseModel):
    """Session storage model."""
    session_id: str
    scam_detected: bool = False
    scam_confidence: float = 0.0
    engagement_start: Optional[datetime] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agent_notes: List[str] = Field(default_factory=list)
    persona: Dict[str, Any] = Field(default_factory=dict)
    is_completed: bool = False


# ============= GUVI Callback Models =============

class GuviCallbackPayload(BaseModel):
    """Payload for GUVI final result callback."""
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: Dict[str, List[str]]
    agentNotes: str
