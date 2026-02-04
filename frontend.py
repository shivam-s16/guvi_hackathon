"""
🍯 Honeypot API Testing Frontend
Simple Streamlit interface to test the API manually.
Act as a scammer and see the AI agent's responses!
"""

import os
import streamlit as st
import requests
import json
import uuid
from datetime import datetime, timezone

# Configuration (from environment variables)
API_BASE_URL = os.getenv("API_BASE_URL", os.getenv("BASE_URL", "http://localhost:8000"))
API_KEY = os.getenv("API_KEY", "change-me-in-production")

# Page config
st.set_page_config(
    page_title="🍯 Honeypot Tester",
    page_icon="🍯",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        max-width: 80%;
    }
    .scammer-message {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        color: white;
        margin-left: auto;
        text-align: right;
    }
    .agent-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    .intel-box {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .status-success {
        color: #48bb78;
        font-weight: bold;
    }
    .status-warning {
        color: #ed8936;
        font-weight: bold;
    }
    .scam-detected {
        background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🍯 Honeypot API Tester</h1>
    <p>Act as a scammer and test the AI agent's responses</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = f"test-{uuid.uuid4().hex[:8]}"
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "messages_display" not in st.session_state:
    st.session_state.messages_display = []
if "latest_intelligence" not in st.session_state:
    st.session_state.latest_intelligence = {}
if "scam_detected" not in st.session_state:
    st.session_state.scam_detected = False
if "latest_result" not in st.session_state:
    st.session_state.latest_result = {}


def send_message(message_text: str, language: str = "English"):
    """Send message to the API and get response."""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    payload = {
        "sessionId": st.session_state.session_id,
        "message": {
            "sender": "scammer",
            "text": message_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": st.session_state.conversation_history,
        "metadata": {
            "channel": "Chat",
            "language": language,
            "locale": "IN"
        }
    }
    
    try:
        # Use the detailed endpoint for more info
        response = requests.post(
            f"{API_BASE_URL}/api/honeypot",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}", "details": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection Error: {str(e)}"}


def trigger_guvi_callback():
    """Manually trigger GUVI callback for the current session."""
    headers = {"x-api-key": API_KEY}
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/session/{st.session_state.session_id}/send-guvi-callback",
            headers=headers,
            timeout=10
        )
        return response.json()
    except:
        return {"error": "Failed to trigger callback"}


def get_session_info():
    """Get current session information."""
    headers = {"x-api-key": API_KEY}
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/session/{st.session_state.session_id}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def reset_conversation():
    """Reset the conversation."""
    st.session_state.session_id = f"test-{uuid.uuid4().hex[:8]}"
    st.session_state.conversation_history = []
    st.session_state.messages_display = []
    st.session_state.latest_intelligence = {}
    st.session_state.scam_detected = False
    st.session_state.latest_result = {}


# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Session info
    st.subheader("📝 Session")
    st.code(st.session_state.session_id)
    
    if st.button("🔄 New Session", use_container_width=True):
        reset_conversation()
        st.rerun()
    
    # Language selection
    st.subheader("🌐 Language")
    language = st.selectbox(
        "Response Language",
        ["English", "Hindi", "Tamil"],
        index=0
    )
    
    # Quick scam messages
    st.subheader("⚡ Quick Messages")
    
    scam_templates = {
        "Bank Block": "URGENT: Your bank account will be blocked today! Call immediately to verify.",
        "UPI Verify": "Your UPI ID needs verification. Share your OTP to avoid suspension.",
        "Prize Win": "Congratulations! You won Rs.50,000! Click http://win-prize.com to claim.",
        "Tax Notice": "Income Tax Department: Pay Rs.5000 immediately or face arrest. Call +919876543210.",
        "KYC Update": "Your KYC is expired. Update now at kyc-update.com or account will be frozen.",
        "OTP Request": "Share the OTP sent to your phone for account security verification.",
    }
    
    for label, msg in scam_templates.items():
        if st.button(f"📩 {label}", use_container_width=True, key=f"quick_{label}"):
            st.session_state.quick_message = msg
    
    # GUVI Callback
    st.subheader("📡 GUVI Callback")
    if st.button("🚀 Send to GUVI", use_container_width=True):
        result = trigger_guvi_callback()
        if "error" not in result:
            st.success("Callback sent!")
            with st.expander("Callback Response"):
                st.json(result)
        else:
            st.error(result.get("reason", result.get("error", "Failed")))
    
    # Stats
    st.subheader("📊 Stats")
    st.metric("Messages", len(st.session_state.messages_display))
    st.metric("Scam Detected", "✅ Yes" if st.session_state.scam_detected else "❌ No")
    
    # Behavior Metrics (from latest response)
    if "latest_result" in st.session_state and st.session_state.latest_result:
        behavior = st.session_state.latest_result.get("behaviorMetrics", {})
        confidence = st.session_state.latest_result.get("scamConfidence", 0.0)
        
        st.subheader("🧠 Behavior Analysis")
        st.metric("Scam Confidence", f"{confidence:.0%}")
        st.metric("Intent Score", f"{behavior.get('intentConfidence', 0.0):.2f}")
        
        esc_rate = behavior.get("escalationRate", 0)
        esc_color = "🔴" if esc_rate > 1 else "🟡" if esc_rate > 0 else "🟢"
        st.metric("Escalation", f"{esc_color} {esc_rate:+d}")
        
        agg_slope = behavior.get("aggressionSlope", 0.0)
        agg_color = "🔴" if agg_slope > 1.5 else "🟡" if agg_slope > 0.5 else "🟢"
        st.metric("Aggression", f"{agg_color} {agg_slope:.2f}")


# Main content - Two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Conversation")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.messages_display:
            if msg["role"] == "scammer":
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%); 
                            color: white; padding: 12px 18px; border-radius: 15px; 
                            margin: 8px 0; margin-left: 20%; text-align: right;">
                    <small>👤 You (Scammer)</small><br>
                    {msg["text"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                            color: white; padding: 12px 18px; border-radius: 15px; 
                            margin: 8px 0; margin-right: 20%;">
                    <small>🤖 AI Agent (Victim)</small><br>
                    {msg["text"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Message input
    st.markdown("---")
    
    # Check for quick message
    default_msg = st.session_state.get("quick_message", "")
    if default_msg:
        del st.session_state.quick_message
    
    with st.form("message_form", clear_on_submit=True):
        user_input = st.text_area(
            "📩 Type your scam message:",
            value=default_msg,
            placeholder="E.g., 'Your bank account will be blocked! Send OTP immediately...'",
            height=100
        )
        
        col_a, col_b = st.columns([3, 1])
        with col_a:
            submit = st.form_submit_button("📤 Send Message", use_container_width=True)
        with col_b:
            clear = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    if clear:
        reset_conversation()
        st.rerun()
    
    if submit and user_input.strip():
        # Add scammer message to display
        st.session_state.messages_display.append({
            "role": "scammer",
            "text": user_input
        })
        
        # Send to API
        with st.spinner("🤖 AI Agent is thinking..."):
            result = send_message(user_input, language)
        
        if "error" not in result:
            # Add agent response to display
            agent_response = result.get("agentResponse", "No response")
            st.session_state.messages_display.append({
                "role": "agent",
                "text": agent_response
            })
            
            # Update conversation history for next request
            st.session_state.conversation_history.append({
                "sender": "scammer",
                "text": user_input,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            st.session_state.conversation_history.append({
                "sender": "user",
                "text": agent_response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Update intelligence
            st.session_state.latest_intelligence = result.get("extractedIntelligence", {})
            st.session_state.scam_detected = result.get("scamDetected", False)
            st.session_state.latest_result = result
        else:
            st.error(f"Error: {result.get('error')}")
        
        st.rerun()


with col2:
    # Scam Detection Status
    if st.session_state.scam_detected:
        st.markdown("""
        <div class="scam-detected">
            🚨 SCAM DETECTED!
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("🔍 Analyzing messages...")
    
    # Intelligence Panel
    st.subheader("🕵️ Extracted Intelligence")
    
    intel = st.session_state.latest_intelligence
    
    # Bank Accounts
    with st.expander("🏦 Bank Accounts", expanded=True):
        accounts = intel.get("bankAccounts", [])
        if accounts:
            for acc in accounts:
                st.code(acc)
        else:
            st.caption("None detected")
    
    # UPI IDs
    with st.expander("💳 UPI IDs", expanded=True):
        upis = intel.get("upiIds", [])
        if upis:
            for upi in upis:
                st.code(upi)
        else:
            st.caption("None detected")
    
    # Phone Numbers
    with st.expander("📱 Phone Numbers", expanded=True):
        phones = intel.get("phoneNumbers", [])
        if phones:
            for phone in phones:
                st.code(phone)
        else:
            st.caption("None detected")
    
    # Phishing Links
    with st.expander("🔗 Phishing Links", expanded=True):
        links = intel.get("phishingLinks", [])
        if links:
            for link in links:
                st.code(link)
        else:
            st.caption("None detected")
    
    # Keywords
    with st.expander("🔑 Suspicious Keywords", expanded=True):
        keywords = intel.get("suspiciousKeywords", [])
        if keywords:
            st.write(", ".join(keywords[:10]))
        else:
            st.caption("None detected")
    
    # Agent Notes (if available)
    if "latest_result" in st.session_state:
        with st.expander("📝 Agent Notes"):
            notes = st.session_state.latest_result.get("agentNotes", "")
            st.write(notes)
    
    # Raw Response
    if "latest_result" in st.session_state:
        with st.expander("🔧 Raw API Response"):
            st.json(st.session_state.latest_result)


# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #718096; padding: 20px;">
    <p>🍯 <b>Honeypot API Tester</b> | Built for GUVI Hackathon 2026</p>
    <p>API running at: <code>{API_BASE_URL}</code> | 
    <a href="{API_BASE_URL}/docs" target="_blank">📚 API Docs</a></p>
</div>
""", unsafe_allow_html=True)
