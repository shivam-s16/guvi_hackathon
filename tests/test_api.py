"""
Test script for the Honeypot API.
Simulates scammer interactions and validates responses.
"""

import os
import requests
import json
import time
from datetime import datetime, timezone
import uuid

# Configuration (from environment variables)
BASE_URL = os.getenv("API_BASE_URL", os.getenv("BASE_URL", "http://localhost:8000"))
API_KEY = os.getenv("API_KEY", "change-me-in-production")

# Headers
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}


def test_health_check():
    """Test the health check endpoint."""
    print("\n📍 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Health check passed!")
    return True


def test_root():
    """Test the root endpoint."""
    print("\n📍 Testing Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Root endpoint passed!")
    return True


def test_scam_detection():
    """Test scam detection with first message."""
    print("\n📍 Testing Scam Detection (First Message)...")
    
    session_id = str(uuid.uuid4())
    
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately or face legal action!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers=HEADERS,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["scamDetected"] == True
    assert data["agentResponse"] is not None
    
    print("✅ Scam detection passed!")
    return session_id


def test_multi_turn_conversation(session_id: str):
    """Test multi-turn conversation handling."""
    print(f"\n📍 Testing Multi-Turn Conversation (Session: {session_id[:8]}...)...")
    
    # First scammer message (already sent in previous test)
    history = [
        {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately or face legal action!",
            "timestamp": "2026-01-21T10:15:30Z"
        },
        {
            "sender": "user",
            "text": "What? My account will be blocked? But why sir?",
            "timestamp": "2026-01-21T10:16:00Z"
        }
    ]
    
    # Second scammer message
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Your KYC is not updated. Share your UPI ID scammer@ybl to verify. Call 9876543210 for help.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": history,
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers=HEADERS,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert data["scamDetected"] == True
    
    # Check intelligence extraction
    intel = data["extractedIntelligence"]
    print(f"\n📊 Extracted Intelligence:")
    print(f"   - UPI IDs: {intel['upiIds']}")
    print(f"   - Phone Numbers: {intel['phoneNumbers']}")
    print(f"   - Keywords: {intel['suspiciousKeywords']}")
    
    print("✅ Multi-turn conversation passed!")
    return True


def test_get_session(session_id: str):
    """Test session info retrieval."""
    print(f"\n📍 Testing Get Session (Session: {session_id[:8]}...)...")
    
    response = requests.get(
        f"{BASE_URL}/api/session/{session_id}",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✅ Get session passed!")
    return True


def test_complete_session(session_id: str):
    """Test session completion."""
    print(f"\n📍 Testing Complete Session (Session: {session_id[:8]}...)...")
    
    response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/complete",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✅ Complete session passed!")
    return True


def test_stats():
    """Test statistics endpoint."""
    print("\n📍 Testing Statistics...")
    
    response = requests.get(
        f"{BASE_URL}/api/stats",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✅ Statistics passed!")
    return True


def test_api_key_required():
    """Test that API key is required."""
    print("\n📍 Testing API Key Requirement...")
    
    response = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers={"Content-Type": "application/json"},  # No API key
        json={"sessionId": "test", "message": {"sender": "scammer", "text": "test", "timestamp": "2026-01-01T00:00:00Z"}}
    )
    
    print(f"Status: {response.status_code}")
    assert response.status_code == 401
    print("✅ API key requirement passed!")
    return True


def test_phishing_link_detection():
    """Test phishing link detection."""
    print("\n📍 Testing Phishing Link Detection...")
    
    session_id = str(uuid.uuid4())
    
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Congratulations! You won Rs.50000! Claim now at http://fake-prize.xyz/claim or bit.ly/fakeprize",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "WhatsApp",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/honeypot",
        headers=HEADERS,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    intel = data["extractedIntelligence"]
    print(f"\n📊 Phishing Links Detected: {intel['phishingLinks']}")
    
    assert response.status_code == 200
    assert data["scamDetected"] == True
    
    print("✅ Phishing link detection passed!")
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("🍯 HONEYPOT API TEST SUITE")
    print("=" * 60)
    
    try:
        # Basic tests
        test_health_check()
        test_root()
        test_api_key_required()
        
        # Scam detection tests
        session_id = test_scam_detection()
        test_multi_turn_conversation(session_id)
        test_get_session(session_id)
        test_complete_session(session_id)
        
        # Additional tests
        test_phishing_link_detection()
        test_stats()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("   Make sure the server is running: python run.py")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    run_all_tests()
