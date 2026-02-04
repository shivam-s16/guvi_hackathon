"""
GUVI Callback Service.
Sends final results to the GUVI evaluation endpoint.

MANDATORY for hackathon evaluation - results must be sent to:
POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
"""

import httpx
import logging
from typing import Dict, Optional
from datetime import datetime
from app.models import GuviCallbackPayload, SessionData
from app.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GuviCallbackService:
    """
    Service to send final honeypot results to GUVI evaluation endpoint.
    
    This callback is MANDATORY for hackathon scoring.
    Must be sent after:
    - Scam intent is confirmed (scamDetected = true)
    - AI Agent has completed sufficient engagement
    - Intelligence extraction is finished
    """
    
    def __init__(self):
        """Initialize the callback service."""
        self.settings = get_settings()
        self.callback_url = self.settings.guvi_callback_url
        self.last_callback_result = None
    
    async def send_final_result(
        self,
        session: SessionData,
        engagement_duration: int = 0
    ) -> Dict:
        """
        Send the final result to GUVI evaluation endpoint.
        
        This is the MANDATORY callback for hackathon evaluation.
        
        Args:
            session: The completed session data
            engagement_duration: Total engagement time in seconds
            
        Returns:
            Response from GUVI API
        """
        # Build the exact payload format required by GUVI
        payload = {
            "sessionId": session.session_id,
            "scamDetected": session.scam_detected,
            "totalMessagesExchanged": len(session.messages),
            "extractedIntelligence": {
                "bankAccounts": session.extracted_intelligence.bankAccounts,
                "upiIds": session.extracted_intelligence.upiIds,
                "phishingLinks": session.extracted_intelligence.phishingLinks,
                "phoneNumbers": session.extracted_intelligence.phoneNumbers,
                "suspiciousKeywords": session.extracted_intelligence.suspiciousKeywords
            },
            "agentNotes": self._build_agent_notes(session)
        }
        
        logger.info(f"📤 Sending GUVI callback for session: {session.session_id}")
        logger.info(f"   Payload: scamDetected={payload['scamDetected']}, messages={payload['totalMessagesExchanged']}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.callback_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                result = {
                    "success": response.status_code in [200, 201, 202],
                    "status_code": response.status_code,
                    "response": response.text,
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": session.session_id,
                    "payload_sent": payload
                }
                
                self.last_callback_result = result
                
                if result["success"]:
                    logger.info(f"✅ GUVI callback SUCCESS for session {session.session_id}")
                else:
                    logger.warning(f"⚠️ GUVI callback returned {response.status_code}: {response.text}")
                
                return result
                
        except httpx.TimeoutException:
            error_result = {
                "success": False,
                "error": "Request timed out after 10 seconds",
                "status_code": None,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session.session_id
            }
            logger.error(f"❌ GUVI callback TIMEOUT for session {session.session_id}")
            self.last_callback_result = error_result
            return error_result
            
        except httpx.RequestError as e:
            error_result = {
                "success": False,
                "error": str(e),
                "status_code": None,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session.session_id
            }
            logger.error(f"❌ GUVI callback ERROR for session {session.session_id}: {e}")
            self.last_callback_result = error_result
            return error_result
    
    def _build_agent_notes(self, session: SessionData) -> str:
        """
        Build comprehensive agent notes summary from session.
        This describes scammer behavior and tactics used.
        """
        notes_parts = []
        
        # Add scam detection info
        if session.scam_detected:
            notes_parts.append(f"Scam detected with {session.scam_confidence:.0%} confidence")
        
        # Analyze scammer tactics
        tactics = self._analyze_scammer_tactics(session)
        if tactics:
            notes_parts.append(f"Tactics used: {', '.join(tactics)}")
        
        # Add intelligence summary
        intel = session.extracted_intelligence
        intel_items = []
        if intel.bankAccounts:
            intel_items.append(f"{len(intel.bankAccounts)} bank account(s)")
        if intel.upiIds:
            intel_items.append(f"{len(intel.upiIds)} UPI ID(s)")
        if intel.phoneNumbers:
            intel_items.append(f"{len(intel.phoneNumbers)} phone number(s)")
        if intel.phishingLinks:
            intel_items.append(f"{len(intel.phishingLinks)} phishing link(s)")
        
        if intel_items:
            notes_parts.append(f"Extracted: {', '.join(intel_items)}")
        
        # Add engagement summary
        notes_parts.append(f"Total messages exchanged: {len(session.messages)}")
        
        # Add keyword summary
        if intel.suspiciousKeywords:
            top_keywords = intel.suspiciousKeywords[:5]
            notes_parts.append(f"Key terms: {', '.join(top_keywords)}")
        
        return ". ".join(notes_parts)
    
    def _analyze_scammer_tactics(self, session: SessionData) -> list:
        """Analyze conversation to identify scammer tactics."""
        tactics = []
        
        # Combine all message texts for analysis
        all_text = " ".join([msg.get("text", "") for msg in session.messages]).lower()
        
        # Check for various tactics
        if any(word in all_text for word in ["urgent", "immediately", "now", "quickly", "fast"]):
            tactics.append("urgency pressure")
        
        if any(word in all_text for word in ["blocked", "suspended", "frozen", "terminated"]):
            tactics.append("account threat")
        
        if any(word in all_text for word in ["police", "arrest", "legal", "court", "warrant"]):
            tactics.append("legal threat/impersonation")
        
        if any(word in all_text for word in ["otp", "pin", "password", "cvv"]):
            tactics.append("credential harvesting")
        
        if any(word in all_text for word in ["transfer", "send money", "pay", "rs.", "₹"]):
            tactics.append("payment redirection")
        
        if any(word in all_text for word in ["won", "prize", "lottery", "reward", "cashback"]):
            tactics.append("prize/lottery bait")
        
        if any(word in all_text for word in ["click", "link", "http", "website"]):
            tactics.append("phishing attempt")
        
        if any(word in all_text for word in ["kyc", "verify", "update", "confirm"]):
            tactics.append("fake verification")
        
        return tactics
    
    async def send_result_direct(
        self,
        session_id: str,
        scam_detected: bool,
        total_messages: int,
        intelligence: Dict,
        agent_notes: str
    ) -> Dict:
        """
        Direct method to send results to GUVI.
        Uses the exact payload format required.
        
        Args:
            session_id: Unique session ID from the platform
            scam_detected: Whether scam intent was confirmed
            total_messages: Total number of messages exchanged
            intelligence: Extracted intelligence dict
            agent_notes: Summary of scammer behavior
            
        Returns:
            Response from GUVI API
        """
        # Build exact payload format
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": {
                "bankAccounts": intelligence.get("bankAccounts", []),
                "upiIds": intelligence.get("upiIds", []),
                "phishingLinks": intelligence.get("phishingLinks", []),
                "phoneNumbers": intelligence.get("phoneNumbers", []),
                "suspiciousKeywords": intelligence.get("suspiciousKeywords", [])
            },
            "agentNotes": agent_notes
        }
        
        logger.info(f"📤 Sending direct GUVI callback for session: {session_id}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.callback_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                result = {
                    "success": response.status_code in [200, 201, 202],
                    "status_code": response.status_code,
                    "response": response.text,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload_sent": payload
                }
                
                self.last_callback_result = result
                
                if result["success"]:
                    logger.info(f"✅ GUVI callback SUCCESS")
                else:
                    logger.warning(f"⚠️ GUVI callback returned {response.status_code}")
                
                return result
                
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ GUVI callback ERROR: {e}")
            self.last_callback_result = error_result
            return error_result
    
    def get_last_callback_result(self) -> Optional[Dict]:
        """Get the result of the last callback attempt."""
        return self.last_callback_result


# Global callback service instance
guvi_callback = GuviCallbackService()
