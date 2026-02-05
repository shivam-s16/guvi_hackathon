"""
Session Manager Module.
Handles conversation sessions, state management, and persistence.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
import asyncio
from app.models import (
    SessionData, ExtractedIntelligenceInternal, 
    ConversationMessage, Message
)
from app.config import get_settings


class SessionManager:
    """
    Manages conversation sessions for the honeypot.
    Stores session state including messages, intelligence, and engagement metrics.
    """
    
    def __init__(self):
        """Initialize session manager with in-memory storage."""
        self.sessions: Dict[str, SessionData] = {}
        self.settings = get_settings()
        self._lock = asyncio.Lock()
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get an existing session by ID."""
        async with self._lock:
            session = self.sessions.get(session_id)
            
            if session:
                # Check if session has expired
                if session.engagement_start:
                    timeout = timedelta(minutes=self.settings.session_timeout_minutes)
                    if datetime.utcnow() - session.engagement_start > timeout:
                        # Session expired, mark as completed
                        session.is_completed = True
                        return session
            
            return session
    
    async def create_session(self, session_id: str) -> SessionData:
        """Create a new session."""
        async with self._lock:
            session = SessionData(
                session_id=session_id,
                engagement_start=datetime.utcnow(),
                messages=[],
                extracted_intelligence=ExtractedIntelligenceInternal(),
                agent_notes=[]
            )
            self.sessions[session_id] = session
            return session
    
    async def get_or_create_session(self, session_id: str) -> SessionData:
        """Get existing session or create a new one."""
        session = await self.get_session(session_id)
        if session is None:
            session = await self.create_session(session_id)
        return session
    
    async def update_session(
        self,
        session_id: str,
        scam_detected: bool = None,
        scam_confidence: float = None,
        new_message: Dict = None,
        intelligence: ExtractedIntelligenceInternal = None,
        agent_note: str = None,
        persona: Dict = None,
        is_completed: bool = None
    ) -> SessionData:
        """Update session with new data."""
        async with self._lock:
            session = self.sessions.get(session_id)
            
            if session is None:
                raise ValueError(f"Session {session_id} not found")
            
            if scam_detected is not None:
                session.scam_detected = scam_detected
            
            if scam_confidence is not None:
                session.scam_confidence = scam_confidence
            
            if new_message is not None:
                session.messages.append(new_message)
            
            if intelligence is not None:
                # Merge intelligence
                session.extracted_intelligence = self._merge_intelligence(
                    session.extracted_intelligence, 
                    intelligence
                )
            
            if agent_note is not None:
                session.agent_notes.append(agent_note)
            
            if persona is not None:
                session.persona = persona
            
            if is_completed is not None:
                session.is_completed = is_completed
            
            return session
    
    def _merge_intelligence(
        self,
        existing: ExtractedIntelligenceInternal,
        new: ExtractedIntelligenceInternal
    ) -> ExtractedIntelligenceInternal:
        """Merge new intelligence into existing."""
        merged = ExtractedIntelligenceInternal(
            bankAccounts=list(set(existing.bankAccounts + new.bankAccounts)),
            upiIds=list(set(existing.upiIds + new.upiIds)),
            phishingLinks=list(set(existing.phishingLinks + new.phishingLinks)),
            phoneNumbers=list(set(existing.phoneNumbers + new.phoneNumbers)),
            suspiciousKeywords=list(set(existing.suspiciousKeywords + new.suspiciousKeywords)),
            emailAddresses=list(set(existing.emailAddresses + new.emailAddresses))
        )
        return merged
    
    async def get_engagement_duration(self, session_id: str) -> int:
        """Get engagement duration in seconds."""
        session = await self.get_session(session_id)
        if session and session.engagement_start:
            duration = datetime.utcnow() - session.engagement_start
            return int(duration.total_seconds())
        return 0
    
    async def get_message_count(self, session_id: str) -> int:
        """Get total messages exchanged in session."""
        session = await self.get_session(session_id)
        if session:
            return len(session.messages)
        return 0
    
    async def should_complete_session(self, session_id: str) -> bool:
        """
        Determine if session should be completed.
        Based on message count, time, or other criteria.
        """
        session = await self.get_session(session_id)
        if session is None:
            return False
        
        if session.is_completed:
            return True
        
        # Check message limit
        if len(session.messages) >= self.settings.max_engagement_messages:
            return True
        
        # Check time limit
        if session.engagement_start:
            timeout = timedelta(minutes=self.settings.session_timeout_minutes)
            if datetime.utcnow() - session.engagement_start > timeout:
                return True
        
        return False
    
    async def complete_session(self, session_id: str) -> SessionData:
        """Mark session as completed."""
        return await self.update_session(session_id, is_completed=True)
    
    async def get_session_summary(self, session_id: str) -> Dict:
        """Get a summary of the session for reporting."""
        session = await self.get_session(session_id)
        if session is None:
            return {}
        
        return {
            "sessionId": session.session_id,
            "scamDetected": session.scam_detected,
            "scamConfidence": session.scam_confidence,
            "totalMessagesExchanged": len(session.messages),
            "engagementDurationSeconds": await self.get_engagement_duration(session_id),
            "extractedIntelligence": {
                "bankAccounts": session.extracted_intelligence.bankAccounts,
                "upiIds": session.extracted_intelligence.upiIds,
                "phishingLinks": session.extracted_intelligence.phishingLinks,
                "phoneNumbers": session.extracted_intelligence.phoneNumbers,
                "suspiciousKeywords": session.extracted_intelligence.suspiciousKeywords
            },
            "agentNotes": ". ".join(session.agent_notes[-5:]),  # Last 5 notes
            "isCompleted": session.is_completed
        }
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        async with self._lock:
            timeout = timedelta(minutes=self.settings.session_timeout_minutes * 2)
            now = datetime.utcnow()
            
            expired_ids = []
            for session_id, session in self.sessions.items():
                if session.engagement_start:
                    if now - session.engagement_start > timeout:
                        expired_ids.append(session_id)
            
            for session_id in expired_ids:
                del self.sessions[session_id]
            
            return len(expired_ids)
    
    async def get_all_active_sessions(self) -> List[str]:
        """Get list of all active session IDs."""
        async with self._lock:
            return [
                sid for sid, session in self.sessions.items()
                if not session.is_completed
            ]


# Global session manager instance
session_manager = SessionManager()
