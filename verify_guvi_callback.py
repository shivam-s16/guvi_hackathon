"""
🧪 GUVI Callback Verification Script
Verifies that the callback payload matches the EXACT required format.

Expected Payload Format:
{
    "sessionId": "abc123-session-id",
    "scamDetected": true,
    "totalMessagesExchanged": 18,
    "extractedIntelligence": {
        "bankAccounts": ["XXXX-XXXX-XXXX"],
        "upiIds": ["scammer@upi"],
        "phishingLinks": ["http://malicious-link.example"],
        "phoneNumbers": ["+91XXXXXXXXXX"],
        "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
    },
    "agentNotes": "Scammer used urgency tactics and payment redirection"
}
"""

import os
import requests
import json
import uuid
from datetime import datetime, timezone

# Configuration (from environment variables)
BASE_URL = os.getenv("API_BASE_URL", os.getenv("BASE_URL", "http://localhost:8000"))
API_KEY = os.getenv("API_KEY", "change-me-in-production")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}


def verify_payload_structure(payload: dict) -> dict:
    """Verify the payload matches GUVI's required structure."""
    issues = []
    
    # Check required fields
    required_fields = ["sessionId", "scamDetected", "totalMessagesExchanged", "extractedIntelligence", "agentNotes"]
    for field in required_fields:
        if field not in payload:
            issues.append(f"❌ Missing required field: {field}")
        else:
            print(f"✅ Field '{field}' present")
    
    # Check extractedIntelligence structure
    if "extractedIntelligence" in payload:
        intel_fields = ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords"]
        for field in intel_fields:
            if field not in payload["extractedIntelligence"]:
                issues.append(f"❌ Missing intelligence field: {field}")
            else:
                value = payload["extractedIntelligence"][field]
                if not isinstance(value, list):
                    issues.append(f"❌ Field {field} should be a list, got {type(value).__name__}")
                else:
                    print(f"   ✅ extractedIntelligence.{field}: {value}")
    
    # Check data types
    if "sessionId" in payload and not isinstance(payload["sessionId"], str):
        issues.append(f"❌ sessionId should be string, got {type(payload['sessionId']).__name__}")
    
    if "scamDetected" in payload and not isinstance(payload["scamDetected"], bool):
        issues.append(f"❌ scamDetected should be boolean, got {type(payload['scamDetected']).__name__}")
    
    if "totalMessagesExchanged" in payload and not isinstance(payload["totalMessagesExchanged"], int):
        issues.append(f"❌ totalMessagesExchanged should be integer, got {type(payload['totalMessagesExchanged']).__name__}")
    
    if "agentNotes" in payload and not isinstance(payload["agentNotes"], str):
        issues.append(f"❌ agentNotes should be string, got {type(payload['agentNotes']).__name__}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def test_direct_guvi_callback():
    """Test sending directly to GUVI endpoint with example payload."""
    print("\n" + "="*60)
    print("📡 TEST 1: Direct GUVI Callback (Example Payload)")
    print("="*60)
    
    # Build EXACT example payload from GUVI documentation
    payload = {
        "sessionId": f"test-verification-{uuid.uuid4().hex[:8]}",
        "scamDetected": True,
        "totalMessagesExchanged": 18,
        "extractedIntelligence": {
            "bankAccounts": ["XXXX-XXXX-XXXX"],
            "upiIds": ["scammer@upi"],
            "phishingLinks": ["http://malicious-link.example"],
            "phoneNumbers": ["+91XXXXXXXXXX"],
            "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
        },
        "agentNotes": "Scammer used urgency tactics and payment redirection"
    }
    
    print("\n📋 Payload to send:")
    print(json.dumps(payload, indent=2))
    
    # Verify structure
    print("\n🔍 Validating payload structure...")
    validation = verify_payload_structure(payload)
    
    if validation["valid"]:
        print("\n✅ Payload structure is VALID!")
    else:
        print("\n❌ Payload has issues:")
        for issue in validation["issues"]:
            print(f"   {issue}")
        return
    
    # Send to GUVI
    print(f"\n📤 Sending to: {GUVI_CALLBACK_URL}")
    
    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ GUVI callback successful!")
            return True
        else:
            print(f"\n⚠️ GUVI returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error sending to GUVI: {e}")
        return False


def test_via_api():
    """Test the callback via our API endpoint."""
    print("\n" + "="*60)
    print("📡 TEST 2: Via Honeypot API (/api/guvi-callback/test)")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/guvi-callback/test",
            headers=HEADERS
        )
        
        result = response.json()
        print("\n📋 API Response:")
        print(json.dumps(result, indent=2))
        
        # Check if payload was sent correctly
        if "guvi_response" in result and "payload_sent" in result["guvi_response"]:
            print("\n🔍 Validating sent payload...")
            validation = verify_payload_structure(result["guvi_response"]["payload_sent"])
            
            if validation["valid"]:
                print("\n✅ Payload structure is VALID!")
            else:
                print("\n❌ Payload has issues:")
                for issue in validation["issues"]:
                    print(f"   {issue}")
        
        return result.get("guvi_response", {}).get("success", False)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        return False


def test_full_flow():
    """Test complete flow: message -> detection -> callback."""
    print("\n" + "="*60)
    print("📡 TEST 3: Full Flow (Scam -> Detection -> GUVI Callback)")
    print("="*60)
    
    session_id = f"full-test-{uuid.uuid4().hex[:8]}"
    print(f"\n📝 Session ID: {session_id}")
    
    # Step 1: Send scam message
    print("\n--- Step 1: Send Scam Message ---")
    
    scam_msg = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "URGENT: Your SBI bank account 1234567890 will be blocked! Send Rs.500 to verify@upi or call +919876543210. Click http://fake-sbi.com now!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response1 = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers=HEADERS,
        json=scam_msg
    )
    
    result1 = response1.json()
    print(f"✅ Scam Detected: {result1.get('scamDetected')}")
    print(f"📊 Intelligence Extracted:")
    intel = result1.get("extractedIntelligence", {})
    print(f"   - Bank Accounts: {intel.get('bankAccounts', [])}")
    print(f"   - UPI IDs: {intel.get('upiIds', [])}")
    print(f"   - Phone Numbers: {intel.get('phoneNumbers', [])}")
    print(f"   - Phishing Links: {intel.get('phishingLinks', [])}")
    print(f"   - Keywords: {intel.get('suspiciousKeywords', [])}")
    
    # Step 2: Complete session and trigger callback
    print("\n--- Step 2: Complete Session & Trigger GUVI Callback ---")
    
    complete_response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/send-guvi-callback",
        headers=HEADERS
    )
    
    complete_result = complete_response.json()
    print(f"\n📤 Callback Result:")
    print(json.dumps(complete_result, indent=2))
    
    # Verify the payload that was sent
    if "guvi_response" in complete_result and "payload_sent" in complete_result["guvi_response"]:
        sent_payload = complete_result["guvi_response"]["payload_sent"]
        print("\n🔍 Validating sent payload against GUVI format...")
        validation = verify_payload_structure(sent_payload)
        
        if validation["valid"]:
            print("\n✅ Payload structure is VALID!")
        else:
            print("\n❌ Issues found:")
            for issue in validation["issues"]:
                print(f"   {issue}")
    
    return complete_result

def test_last_callback():
    """Check the last callback that was sent."""
    print("\n" + "="*60)
    print("📋 Last Callback Result")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/api/guvi-callback/last-result",
        headers=HEADERS
    )
    
    result = response.json()
    print(json.dumps(result, indent=2))
    
    return result


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║       🧪 GUVI CALLBACK VERIFICATION SCRIPT                 ║
    ║                                                            ║
    ║   Verifies payload matches GUVI's required format          ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check server is running
    try:
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code != 200:
            print("❌ Server not running! Start with: python run.py")
            return
        print("✅ Server is running!\n")
    except:
        print("❌ Cannot connect to server!")
        return
    
    # Run tests
    test_direct_guvi_callback()
    test_via_api()
    test_full_flow()
    test_last_callback()
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                    ✅ VERIFICATION COMPLETE                ║
    ║                                                            ║
    ║   If all tests passed, your GUVI callback is correctly     ║
    ║   formatted and the integration is working!                ║
    ╚════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
