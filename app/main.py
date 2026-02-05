"""
Agentic Honey-Pot API for Scam Detection & Intelligence Extraction.

Main FastAPI application that provides:
- Scam detection and intent analysis
- Autonomous AI agent engagement
- Intelligence extraction
- Multi-turn conversation handling
- GUVI evaluation callback integration
"""

from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, Depends, BackgroundTasks
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.models import (
    HoneypotRequest, HoneypotResponse, ErrorResponse, SimpleResponse,
    EngagementMetrics, ExtractedIntelligence, ExtractedIntelligenceInternal, 
    ConversationMessage, BehaviorMetricsResponse
)
from app.services.detector import ScamDetector
from app.services.behavior_engine import get_behavior_engine
from app.intelligence_extractor import IntelligenceExtractor
from app.agent import AIAgent
from app.session_manager import session_manager
from app.guvi_callback import guvi_callback

# Force reload triggers


# Security
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def verify_api_key(
    api_key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings)
) -> str:
    """Verify the API key from request header."""
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include 'x-api-key' header."
        )
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key


# Initialize core components
scam_detector = ScamDetector()
intelligence_extractor = IntelligenceExtractor()

# Agent instances per session (created on demand)
agents: dict = {}


def get_or_create_agent(session_id: str) -> AIAgent:
    """Get existing agent for session or create new one."""
    if session_id not in agents:
        agents[session_id] = AIAgent()
    return agents[session_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🍯 Honeypot API starting...")
    print(f"📡 Listening for scam messages...")
    yield
    # Shutdown
    print("🛑 Honeypot API shutting down...")
    # Cleanup sessions
    await session_manager.cleanup_expired_sessions()


# Create FastAPI app
app = FastAPI(
    title="Agentic Honey-Pot API",
    description="AI-powered honeypot system for scam detection and intelligence extraction",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Exception Handlers =============

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status="error",
            error="Internal server error",
            details=str(exc)
        ).model_dump()
    )


# ============= API Endpoints =============

@app.get("/")
async def root():
    """Root endpoint to verify API status."""
    return {
        "status": "online",
        "service": "Honeypot Agent API",
        "version": "1.0.0",
        "scam_detector": "Advanced Hybrid Engine (v2)"
    }


@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint. Supports both GET and HEAD for uptime monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "scam_detector": "operational",
            "intelligence_extractor": "operational",
            "ai_agent": "operational",
            "session_manager": "operational"
        }
    }


@app.post(
    "/api/honeypot",
    response_model=HoneypotResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def process_message(
    request: HoneypotRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> HoneypotResponse:
    """
    Main honeypot endpoint.
    """
    session_id = request.sessionId
    message = request.message
    history = request.conversationHistory
    metadata = request.metadata
    
    try:
        # Get or create session
        session = await session_manager.get_or_create_session(session_id)
        
        # Store incoming message
        await session_manager.update_session(
            session_id,
            new_message={
                "sender": message.sender.value,
                "text": message.text,
                "timestamp": message.timestamp.isoformat()
            }
        )
        
        # Convert history to formatted strings for new detector
        history_strings = [msg.text for msg in history]
        
        # Convert history to expected format for intelligence extractor
        history_messages = [
            ConversationMessage(
                sender=msg.sender,
                text=msg.text,
                timestamp=msg.timestamp
            ) for msg in history
        ]
        
        # Step 1: Detect scam intent (New Advanced Engine)
        is_scam_current, risk_score, debug_info = scam_detector.detect(
            message.text, 
            history_strings
        )
        
        # ===== PROGRESSIVE DETECTION: Check if session was PREVIOUSLY marked as scam =====
        # If session already detected as scam, stay in scam mode (don't downgrade)
        session_was_scam = session.scam_detected if session.scam_detected else False
        
        # Cumulative score: Consider current message + history signals
        # Even if current message alone isn't scam, if history + current crosses threshold, it's scam
        cumulative_score = risk_score
        if history_strings:
            # Add small boost for each previous suspicious message
            for hist_msg in history_strings[-5:]:  # Check last 5 messages
                _, hist_score, _ = scam_detector.detect(hist_msg, [])
                cumulative_score += hist_score * 0.3  # 30% weight for historical
        
        # DECISION: Mark as scam if:
        # 1. Current message is scam, OR
        # 2. Session was already marked as scam, OR  
        # 3. Cumulative score crosses threshold (allows mid-conversation reclassification)
        is_scam = is_scam_current or session_was_scam or (cumulative_score >= 6.0)
        
        # Normalize for session storage
        confidence = min(cumulative_score / 10.0, 1.0)  # Convert 0-10 to 0-1, cap at 1.0
        keywords = [s for s in debug_info.get("signals", []) if ":" in s]
        analysis = debug_info.get("analysis", "No analysis")
        
        # Get scam type for better context
        scam_type = scam_detector.get_scam_type(message.text, keywords) if is_scam else "None"
        
        # Update session with detection results (can UPGRADE to scam, never downgrade)
        await session_manager.update_session(
            session_id,
            scam_detected=is_scam,  # Will be True if was True OR now True
            scam_confidence=confidence,
            agent_note=f"{analysis}. Cumulative: {cumulative_score:.1f}. Signals: {len(keywords)}"
        )
        
        # Step 2: Extract intelligence ALWAYS (even for non-scam, we collect data)
        intelligence = intelligence_extractor.extract_from_conversation(
            message, 
            history_messages
        )
        
        await session_manager.update_session(
            session_id,
            intelligence=intelligence
        )
        
        # Step 3: Generate agent response
        agent_response = None
        agent_notes = analysis
        
        if is_scam:
            # Get or create agent for this session
            agent = get_or_create_agent(session_id)
            
            # Set persona if first message
            if not session.persona:
                await session_manager.update_session(
                    session_id,
                    persona=agent.get_persona()
                )
            
            # Generate response (engage scam messages)
            response_text, notes = await agent.generate_response(
                message,
                history_messages,
                scam_type,
                is_scam=True
            )
            
            agent_response = response_text
            agent_notes = notes
            
            # SAFEGUARD: Ensure agent_response is never None
            if not agent_response or agent_response.strip() == "" or agent_response == "None":
                fallback_responses = [
                    "Hello? Yes, I am listening... please continue",
                    "Hello, what is this about?",
                    "Yes, can you tell me more?",
                    "I am here, please explain what you need",
                ]
                import random
                agent_response = random.choice(fallback_responses)
            
            # Store agent's response in session
            await session_manager.update_session(
                session_id,
                new_message={
                    "sender": "user",  # Agent plays as user
                    "text": agent_response,
                    "timestamp": datetime.utcnow().isoformat()
                },
                agent_note=notes
            )
        else:
            # Not a scam YET - Engage neutrally (in case it escalates later)
            agent_response = "Hello, I'm listening. What is this about?"
            agent_notes = "Message appears safe. Engaging neutrally in case of escalation."
        
        # Step 4: Calculate engagement metrics
        engagement_duration = await session_manager.get_engagement_duration(session_id)
        message_count = await session_manager.get_message_count(session_id)
        
        # Step 5: Check if session should be completed
        should_complete = await session_manager.should_complete_session(session_id)
        
        if should_complete and is_scam:
            # Complete session and send to GUVI
            await session_manager.complete_session(session_id)
            updated_session = await session_manager.get_session(session_id)
            
            # Send callback in background
            background_tasks.add_task(
                guvi_callback.send_final_result,
                updated_session,
                engagement_duration
            )
        
        # Get updated session data
        final_session = await session_manager.get_session(session_id)
        
        # Process scammer message through behavior engine for analysis
        behavior_engine = get_behavior_engine(session_id)
        await behavior_engine.process_reply(
            reply=agent_response or "",
            scammer_msg=message.text,
            scam_score=cumulative_score,
            signal_count=len(keywords),
            apply_delay=False  # Don't block API response
        )
        behavior_metrics = behavior_engine.get_metrics()
        
        # Build response (Strict match to specs - EXACT format)
        # Convert internal intelligence to API format (only bankAccounts, upiIds, phishingLinks)
        api_intelligence = final_session.extracted_intelligence.to_api_format()
        
        response = HoneypotResponse(
            status="success",
            scamDetected=is_scam,
            engagementMetrics=EngagementMetrics(
                engagementDurationSeconds=engagement_duration,
                totalMessagesExchanged=message_count
            ),
            extractedIntelligence=api_intelligence,
            agentNotes=agent_notes
        )
        
        return response
        
    except Exception as e:
        # Log error and return error response
        print(f"Error processing message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@app.post(
    "/api/message",
    response_model=SimpleResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def process_message_simple(
    request: HoneypotRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> SimpleResponse:
    """
    Simple message endpoint - returns only status and reply.
    
    **This is the primary endpoint for GUVI evaluation.**
    
    Returns the expected format:
    ```json
    {
        "status": "success",
        "reply": "Why is my account being suspended?"
    }
    ```
    
    The agent will respond in the same language as the incoming message.
    
    **Authentication**: Requires `x-api-key` header.
    """
    session_id = request.sessionId
    message = request.message
    history = request.conversationHistory
    metadata = request.metadata
    
    # Get language from metadata (for multi-language support)
    language = "English"
    if metadata and metadata.language:
        language = metadata.language
    
    try:
        # Get or create session
        session = await session_manager.get_or_create_session(session_id)
        
        # Store incoming message
        await session_manager.update_session(
            session_id,
            new_message={
                "sender": message.sender.value,
                "text": message.text,
                "timestamp": message.timestamp.isoformat()
            }
        )
        
        # Convert history to expected format
        history_messages = [
            ConversationMessage(
                sender=msg.sender,
                text=msg.text,
                timestamp=msg.timestamp
            ) for msg in history
        ]
        
        # Detect scam intent
        # Convert history to formatted strings for new detector
        history_strings = [msg.text for msg in history_messages]
        
        # Detect scam intent (New Advanced Engine)
        is_scam_current, risk_score, debug_info = scam_detector.detect(
            message.text, 
            history_strings
        )
        
        # ===== PROGRESSIVE DETECTION =====
        # Check if session was PREVIOUSLY marked as scam
        session_was_scam = session.scam_detected if session.scam_detected else False
        
        # Cumulative score: current + history
        cumulative_score = risk_score
        if history_strings:
            for hist_msg in history_strings[-5:]:
                _, hist_score, _ = scam_detector.detect(hist_msg, [])
                cumulative_score += hist_score * 0.3
        
        # DECISION: Mark as scam if any condition met
        is_scam = is_scam_current or session_was_scam or (cumulative_score >= 6.0)
        
        # Normalize for session storage
        confidence = min(cumulative_score / 10.0, 1.0)
        keywords = [s for s in debug_info.get("signals", []) if ":" in s]
        analysis = debug_info.get("analysis", "No analysis")
        
        # Get scam type
        scam_type = scam_detector.get_scam_type(message.text, keywords) if is_scam else "None"
        
        # Update session (can UPGRADE to scam, never downgrade)
        await session_manager.update_session(
            session_id,
            scam_detected=is_scam,
            scam_confidence=confidence,
            agent_note=f"Detection: {analysis}. Cumulative: {cumulative_score:.1f}. Type: {scam_type}"
        )
        
        # Extract intelligence ALWAYS
        intelligence = intelligence_extractor.extract_from_conversation(
            message, 
            history_messages
        )
        
        await session_manager.update_session(
            session_id,
            intelligence=intelligence
        )
        
        # Generate agent reply (ALWAYS engage - honeypot should respond to all messages)
        reply = ""
        
        # Get or create agent
        agent = get_or_create_agent(session_id)
        
        # Set language context for agent
        if language != "English":
            agent.set_language(language)
        
        # Set persona if first message
        if not session.persona:
            await session_manager.update_session(
                session_id,
                persona=agent.get_persona()
            )
        
        # Generate agent reply
        if is_scam:
            # Generate response (engage scam messages)
            response_text, notes = await agent.generate_response(
                message,
                history_messages,
                scam_type,
                language=language,
                is_scam=True
            )
            
            reply = response_text
            
            # SAFEGUARD: Ensure reply is never None or empty
            if not reply or reply.strip() == "" or reply == "None":
                import random
                if language.lower() == "hindi":
                    fallback_responses = [
                        "Hello? Yes, I am listening... please continue",
                        "Hello, what is this about?",
                    ]
                elif language.lower() == "tamil":
                    fallback_responses = [
                        "Hello? Yes, I am listening... please continue",
                    ]
                else:
                    fallback_responses = [
                        "Hello? Yes, I am listening... please continue",
                        "Hello, what is this about?",
                        "Yes, can you tell me more?",
                        "I am here, please explain what you need",
                    ]
                reply = random.choice(fallback_responses)
            
            # Store agent's response
            await session_manager.update_session(
                session_id,
                new_message={
                    "sender": "user",
                    "text": reply,
                    "timestamp": datetime.utcnow().isoformat()
                },
                agent_note=notes
            )
        else:
            # Not a scam YET - Engage neutrally (watch for escalation)
            reply = "Hello, I'm listening. What is this regarding?"
        
        # Check if session should be completed and send GUVI callback
        should_complete = await session_manager.should_complete_session(session_id)
        
        if should_complete and is_scam:
            await session_manager.complete_session(session_id)
            updated_session = await session_manager.get_session(session_id)
            engagement_duration = await session_manager.get_engagement_duration(session_id)
            
            # Send GUVI callback in background
            background_tasks.add_task(
                guvi_callback.send_final_result,
                updated_session,
                engagement_duration
            )
        
        return SimpleResponse(
            status="success",
            reply=reply
        )
        
    except Exception as e:
        print(f"Error processing message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@app.get("/api/session/{session_id}")
async def get_session_info(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get session information and extracted intelligence.
    
    **Authentication**: Requires `x-api-key` header.
    """
    session = await session_manager.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    return await session_manager.get_session_summary(session_id)


@app.post("/api/session/{session_id}/complete")
async def complete_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually complete a session and trigger GUVI callback.
    
    **Authentication**: Requires `x-api-key` header.
    """
    session = await session_manager.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    if session.is_completed:
        return {
            "status": "already_completed",
            "session_id": session_id
        }
    
    # Complete session
    await session_manager.complete_session(session_id)
    updated_session = await session_manager.get_session(session_id)
    
    # Get engagement duration
    engagement_duration = await session_manager.get_engagement_duration(session_id)
    
    # Send to GUVI in background
    if updated_session.scam_detected:
        background_tasks.add_task(
            guvi_callback.send_final_result,
            updated_session,
            engagement_duration
        )
    
    return {
        "status": "completed",
        "session_id": session_id,
        "summary": await session_manager.get_session_summary(session_id)
    }


@app.delete("/api/session/{session_id}")
async def delete_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a session.
    
    **Authentication**: Requires `x-api-key` header.
    """
    session = await session_manager.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    # Remove from agents dict
    if session_id in agents:
        del agents[session_id]
    
    # Remove session
    async with session_manager._lock:
        if session_id in session_manager.sessions:
            del session_manager.sessions[session_id]
    
    return {
        "status": "deleted",
        "session_id": session_id
    }


@app.get("/api/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """
    Get honeypot statistics.
    
    **Authentication**: Requires `x-api-key` header.
    """
    active_sessions = await session_manager.get_all_active_sessions()
    
    total_scams = sum(
        1 for sid in session_manager.sessions
        if session_manager.sessions[sid].scam_detected
    )
    
    total_intelligence = {
        "bankAccounts": 0,
        "upiIds": 0,
        "phoneNumbers": 0,
        "phishingLinks": 0
    }
    
    for sid, session in session_manager.sessions.items():
        intel = session.extracted_intelligence
        total_intelligence["bankAccounts"] += len(intel.bankAccounts)
        total_intelligence["upiIds"] += len(intel.upiIds)
        total_intelligence["phoneNumbers"] += len(intel.phoneNumbers)
        total_intelligence["phishingLinks"] += len(intel.phishingLinks)
    
    return {
        "activeSessions": len(active_sessions),
        "totalSessions": len(session_manager.sessions),
        "scamsDetected": total_scams,
        "totalIntelligence": total_intelligence
    }


@app.post("/api/session/{session_id}/send-guvi-callback")
async def send_guvi_callback(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger GUVI callback for a session.
    
    This sends the final result to: https://hackathon.guvi.in/api/updateHoneyPotFinalResult
    
    **Authentication**: Requires `x-api-key` header.
    
    **Use this when**: 
    - Scam is detected (scamDetected = true)
    - Sufficient engagement has occurred
    - Intelligence extraction is complete
    """
    session = await session_manager.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    if not session.scam_detected:
        return {
            "status": "skipped",
            "reason": "Scam not detected for this session - GUVI callback not sent",
            "session_id": session_id
        }
    
    # Get engagement duration
    engagement_duration = await session_manager.get_engagement_duration(session_id)
    
    # Send callback immediately (not in background)
    result = await guvi_callback.send_final_result(session, engagement_duration)
    
    return {
        "status": "callback_sent",
        "session_id": session_id,
        "guvi_response": result,
        "payload_summary": {
            "scamDetected": session.scam_detected,
            "totalMessagesExchanged": len(session.messages),
            "intelligenceCount": {
                "bankAccounts": len(session.extracted_intelligence.bankAccounts),
                "upiIds": len(session.extracted_intelligence.upiIds),
                "phoneNumbers": len(session.extracted_intelligence.phoneNumbers),
                "phishingLinks": len(session.extracted_intelligence.phishingLinks)
            }
        }
    }


@app.get("/api/guvi-callback/last-result")
async def get_last_guvi_callback_result(api_key: str = Depends(verify_api_key)):
    """
    Get the result of the last GUVI callback attempt.
    
    Useful for debugging and verifying callback was sent.
    
    **Authentication**: Requires `x-api-key` header.
    """
    result = guvi_callback.get_last_callback_result()
    
    if result is None:
        return {
            "status": "no_callbacks_sent",
            "message": "No GUVI callbacks have been sent yet"
        }
    
    return {
        "status": "found",
        "last_callback": result
    }


@app.post("/api/guvi-callback/test")
async def test_guvi_callback(api_key: str = Depends(verify_api_key)):
    """
    Send a test callback to GUVI endpoint.
    
    This can be used to verify connectivity to the GUVI evaluation endpoint.
    
    **Authentication**: Requires `x-api-key` header.
    """
    import uuid
    
    test_session_id = f"test-{uuid.uuid4().hex[:8]}"
    
    result = await guvi_callback.send_result_direct(
        session_id=test_session_id,
        scam_detected=True,
        total_messages=5,
        intelligence={
            "bankAccounts": ["1234567890"],
            "upiIds": ["test@upi"],
            "phishingLinks": ["http://test-phishing.example"],
            "phoneNumbers": ["+911234567890"],
            "suspiciousKeywords": ["urgent", "blocked", "verify"]
        },
        agent_notes="Test callback from honeypot API"
    )
    
    return {
        "status": "test_sent",
        "test_session_id": test_session_id,
        "guvi_response": result
    }


# ============= Run Configuration =============

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
