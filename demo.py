"""
🍯 Honeypot API Demo Script
Demonstrates the full evaluation flow with multiple scam scenarios.

Scenarios covered:
1. Bank Account Blocking Scam
2. UPI/KYC Verification Scam
3. Prize/Lottery Scam
4. Phishing Link Scam
5. Multi-turn Conversation Demo
"""

import os
import requests
import json
import time
from datetime import datetime, timezone
import uuid

# ============================================
# CONFIGURATION (from environment variables)
# ============================================
BASE_URL = os.getenv("API_BASE_URL", os.getenv("BASE_URL", "http://localhost:8000"))
API_KEY = os.getenv("API_KEY", "change-me-in-production")

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

def pretty_print(title, data):
    """Pretty print JSON response."""
    print(f"\n{'='*60}")
    print(f"📌 {title}")
    print('='*60)
    print(json.dumps(data, indent=2))

def send_message(session_id, message_text, history=[], channel="SMS"):
    """Send a message to the honeypot API."""
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": message_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": history,
        "metadata": {
            "channel": channel,
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers=HEADERS,
        json=payload
    )
    
    return response.json()

def complete_session(session_id):
    """Complete a session and trigger GUVI callback."""
    response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/complete",
        headers=HEADERS
    )
    return response.json()

# ============================================
# DEMO 1: Bank Account Blocking Scam
# ============================================
def demo_bank_scam():
    print("\n" + "🏦"*30)
    print("DEMO 1: BANK ACCOUNT BLOCKING SCAM")
    print("🏦"*30)
    
    session_id = f"demo-bank-{uuid.uuid4().hex[:8]}"
    print(f"\n📝 Session ID: {session_id}")
    
    # Message 1: Initial threat
    print("\n--- Scammer Message 1 ---")
    scam_msg1 = "URGENT: Your SBI bank account will be BLOCKED today due to KYC expiry. Verify immediately to avoid suspension. Call 9876543210."
    print(f"Scammer: {scam_msg1}")
    
    response1 = send_message(session_id, scam_msg1)
    print(f"\n🤖 Agent Response: {response1.get('agentResponse', 'N/A')}")
    print(f"📊 Scam Detected: {response1['scamDetected']}")
    print(f"🔍 Keywords: {response1['extractedIntelligence']['suspiciousKeywords']}")
    print(f"📞 Phone Numbers: {response1['extractedIntelligence']['phoneNumbers']}")
    
    return session_id, response1

# ============================================
# DEMO 2: UPI Verification Scam
# ============================================
def demo_upi_scam():
    print("\n" + "💳"*30)
    print("DEMO 2: UPI VERIFICATION SCAM")
    print("💳"*30)
    
    session_id = f"demo-upi-{uuid.uuid4().hex[:8]}"
    print(f"\n📝 Session ID: {session_id}")
    
    # Message 1
    scam_msg = "Your PhonePe account is under investigation. Send Rs.1 to fraudster@ybl for verification or account will be frozen in 2 hours."
    print(f"\n--- Scammer Message ---")
    print(f"Scammer: {scam_msg}")
    
    response = send_message(session_id, scam_msg, channel="WhatsApp")
    print(f"\n🤖 Agent Response: {response.get('agentResponse', 'N/A')}")
    print(f"📊 Scam Detected: {response['scamDetected']}")
    print(f"💰 UPI IDs Extracted: {response['extractedIntelligence']['upiIds']}")
    
    return session_id, response

# ============================================
# DEMO 3: Prize/Lottery Scam
# ============================================
def demo_prize_scam():
    print("\n" + "🎰"*30)
    print("DEMO 3: PRIZE/LOTTERY SCAM")
    print("🎰"*30)
    
    session_id = f"demo-prize-{uuid.uuid4().hex[:8]}"
    print(f"\n📝 Session ID: {session_id}")
    
    scam_msg = "CONGRATULATIONS! You have WON Rs.50,00,000 in Jio Lucky Draw! Claim now at http://fake-prize.xyz/claim. Pay Rs.999 processing fee to unlock your prize!"
    print(f"\n--- Scammer Message ---")
    print(f"Scammer: {scam_msg}")
    
    response = send_message(session_id, scam_msg)
    print(f"\n🤖 Agent Response: {response.get('agentResponse', 'N/A')}")
    print(f"📊 Scam Detected: {response['scamDetected']}")
    print(f"🔗 Phishing Links: {response['extractedIntelligence']['phishingLinks']}")
    print(f"🔍 Keywords: {response['extractedIntelligence']['suspiciousKeywords']}")
    
    return session_id, response

# ============================================
# DEMO 4: Income Tax Threat Scam
# ============================================
def demo_tax_scam():
    print("\n" + "⚖️"*30)
    print("DEMO 4: INCOME TAX THREAT SCAM")
    print("⚖️"*30)
    
    session_id = f"demo-tax-{uuid.uuid4().hex[:8]}"
    print(f"\n📝 Session ID: {session_id}")
    
    scam_msg = "This is Income Tax Department. Case filed against your PAN. Arrest warrant issued. Pay Rs.25000 immediately to settle or face jail. Contact: scammer.officer@gmail.com"
    print(f"\n--- Scammer Message ---")
    print(f"Scammer: {scam_msg}")
    
    response = send_message(session_id, scam_msg)
    print(f"\n🤖 Agent Response: {response.get('agentResponse', 'N/A')}")
    print(f"📊 Scam Detected: {response['scamDetected']}")
    print(f"📧 Emails Extracted: {response['extractedIntelligence']['emailAddresses']}")
    
    return session_id, response

# ============================================
# DEMO 5: Multi-Turn Conversation (FULL FLOW)
# ============================================
def demo_multi_turn_conversation():
    print("\n" + "🔄"*30)
    print("DEMO 5: MULTI-TURN CONVERSATION (FULL EVALUATION FLOW)")
    print("🔄"*30)
    
    session_id = f"demo-multiturn-{uuid.uuid4().hex[:8]}"
    print(f"\n📝 Session ID: {session_id}")
    
    conversation_history = []
    
    # === TURN 1 ===
    print("\n" + "-"*50)
    print("TURN 1: Initial Contact")
    print("-"*50)
    
    msg1 = "Hello, this is SBI customer care. Your account 4532XXXX7891 has suspicious activity. It will be blocked in 1 hour unless verified."
    print(f"\n📩 Scammer: {msg1}")
    
    response1 = send_message(session_id, msg1, conversation_history)
    agent_reply1 = response1.get('agentResponse', '')
    
    print(f"🤖 Agent: {agent_reply1}")
    print(f"   └─ Scam Detected: {response1['scamDetected']}")
    
    # Add to history
    conversation_history.append({
        "sender": "scammer",
        "text": msg1,
        "timestamp": "2026-01-28T10:00:00Z"
    })
    conversation_history.append({
        "sender": "user",
        "text": agent_reply1,
        "timestamp": "2026-01-28T10:01:00Z"
    })
    
    time.sleep(1)
    
    # === TURN 2 ===
    print("\n" + "-"*50)
    print("TURN 2: Scammer Requests Information")
    print("-"*50)
    
    msg2 = "Sir, to verify your identity, please share your registered mobile OTP. I am sending it now. Also share your UPI PIN for security check."
    print(f"\n📩 Scammer: {msg2}")
    
    response2 = send_message(session_id, msg2, conversation_history)
    agent_reply2 = response2.get('agentResponse', '')
    
    print(f"🤖 Agent: {agent_reply2}")
    print(f"   └─ Messages Exchanged: {response2['engagementMetrics']['totalMessagesExchanged']}")
    
    conversation_history.append({
        "sender": "scammer",
        "text": msg2,
        "timestamp": "2026-01-28T10:02:00Z"
    })
    conversation_history.append({
        "sender": "user",
        "text": agent_reply2,
        "timestamp": "2026-01-28T10:03:00Z"
    })
    
    time.sleep(1)
    
    # === TURN 3 ===
    print("\n" + "-"*50)
    print("TURN 3: Scammer Pushes Harder")
    print("-"*50)
    
    msg3 = "Sir hurry up! Account will freeze in 10 minutes! Transfer Rs.500 to verify your account is active. Send to my UPI: sbi.verify@ybl or call my direct line +919988776655"
    print(f"\n📩 Scammer: {msg3}")
    
    response3 = send_message(session_id, msg3, conversation_history)
    agent_reply3 = response3.get('agentResponse', '')
    
    print(f"🤖 Agent: {agent_reply3}")
    print(f"   └─ UPI IDs Found: {response3['extractedIntelligence']['upiIds']}")
    print(f"   └─ Phone Numbers: {response3['extractedIntelligence']['phoneNumbers']}")
    
    conversation_history.append({
        "sender": "scammer",
        "text": msg3,
        "timestamp": "2026-01-28T10:04:00Z"
    })
    conversation_history.append({
        "sender": "user",
        "text": agent_reply3,
        "timestamp": "2026-01-28T10:05:00Z"
    })
    
    time.sleep(1)
    
    # === TURN 4 ===
    print("\n" + "-"*50)
    print("TURN 4: Scammer Provides Account Details")
    print("-"*50)
    
    msg4 = "OK sir if UPI not working, do NEFT to our verification account: Account No. 12345678901234, IFSC: SBIN0012345, Name: SBI Security Team. Send Rs.500 only."
    print(f"\n📩 Scammer: {msg4}")
    
    response4 = send_message(session_id, msg4, conversation_history)
    agent_reply4 = response4.get('agentResponse', '')
    
    print(f"🤖 Agent: {agent_reply4}")
    print(f"   └─ Bank Accounts Found: {response4['extractedIntelligence']['bankAccounts']}")
    
    time.sleep(1)
    
    # === COMPLETE SESSION ===
    print("\n" + "="*50)
    print("COMPLETING SESSION & SENDING TO GUVI")
    print("="*50)
    
    completion = complete_session(session_id)
    
    print("\n📊 FINAL INTELLIGENCE REPORT:")
    print(json.dumps(completion, indent=2))
    
    return session_id, completion

# ============================================
# DEMO 6: Statistics Check
# ============================================
def demo_stats():
    print("\n" + "📊"*30)
    print("HONEYPOT STATISTICS")
    print("📊"*30)
    
    response = requests.get(
        f"{BASE_URL}/api/stats",
        headers=HEADERS
    )
    
    stats = response.json()
    pretty_print("Current Statistics", stats)
    return stats


# ============================================
# DEMO 7: GUVI Callback Test
# ============================================
def demo_guvi_callback():
    print("\n" + "📡"*30)
    print("DEMO 7: GUVI CALLBACK TEST")
    print("📡"*30)
    
    print("\n--- Testing GUVI Callback Endpoint ---")
    print(f"Target: https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
    
    # Test the callback
    response = requests.post(
        f"{BASE_URL}/api/guvi-callback/test",
        headers=HEADERS
    )
    
    result = response.json()
    print(f"\n📤 Test Callback Result:")
    print(json.dumps(result, indent=2))
    
    # Check last callback result
    last_result = requests.get(
        f"{BASE_URL}/api/guvi-callback/last-result",
        headers=HEADERS
    )
    
    print(f"\n📋 Last Callback Status:")
    print(json.dumps(last_result.json(), indent=2))
    
    return result

# ============================================
# MAIN DEMO RUNNER
# ============================================
def run_all_demos():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     🍯 AGENTIC HONEY-POT API - DEMO SHOWCASE 🍯           ║
    ║                                                           ║
    ║   Demonstrating scam detection, AI engagement,            ║
    ║   and intelligence extraction capabilities                ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Check if server is running
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code != 200:
            print("❌ Server not running! Start with: python run.py")
            return
        print("✅ Server is running!\n")
        
        # Run demos
        demos = [
            ("Bank Account Scam", demo_bank_scam),
            ("UPI Verification Scam", demo_upi_scam),
            ("Prize/Lottery Scam", demo_prize_scam),
            ("Income Tax Threat Scam", demo_tax_scam),
            ("Multi-Turn Conversation", demo_multi_turn_conversation),
            ("Statistics", demo_stats),
            ("GUVI Callback Test", demo_guvi_callback),
        ]
        
        for i, (name, demo_func) in enumerate(demos, 1):
            print(f"\n\n{'#'*60}")
            print(f"# RUNNING DEMO {i}/{len(demos)}: {name}")
            print('#'*60)
            
            try:
                demo_func()
                print(f"\n✅ Demo '{name}' completed successfully!")
            except Exception as e:
                print(f"\n❌ Demo '{name}' failed: {e}")
            
            if i < len(demos):
                print("\n⏳ Waiting 2 seconds before next demo...")
                time.sleep(2)
        
        print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║              ✅ ALL DEMOS COMPLETED!                      ║
    ║                                                           ║
    ║   The honeypot successfully:                              ║
    ║   • Detected scam messages ✓                              ║ 
    ║   • Engaged scammers with AI agent ✓                      ║
    ║   • Extracted intelligence (UPI, phones, links) ✓         ║
    ║   • Handled multi-turn conversations ✓                    ║
    ║   • Sent results to GUVI callback ✓                       ║
    ╚═══════════════════════════════════════════════════════════╝
        """)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Start the server first: python run.py")

# ============================================
# QUICK TEST FUNCTION
# ============================================
def quick_test():
    """Quick single message test."""
    print("\n🚀 Quick Test - Single Scam Message")
    print("="*50)
    
    session_id = f"quick-test-{uuid.uuid4().hex[:8]}"
    
    test_msg = "ALERT: Your HDFC account 9876XXXX will be blocked! Share OTP 123456 immediately. Call +919123456789"
    print(f"\n📩 Test Message: {test_msg}")
    
    response = send_message(session_id, test_msg)
    
    print(f"\n📊 Results:")
    print(f"   • Scam Detected: {response['scamDetected']}")
    print(f"   • Agent Response: {response.get('agentResponse', 'N/A')}")
    print(f"   • Phone Numbers: {response['extractedIntelligence']['phoneNumbers']}")
    print(f"   • Keywords: {response['extractedIntelligence']['suspiciousKeywords']}")
    
    return response

# ============================================
# ENTRY POINT
# ============================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        run_all_demos()
