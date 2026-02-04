# -*- coding: utf-8 -*-
"""
PRE-DEPLOYMENT VERIFICATION SCRIPT
===================================
Checks all critical requirements before hosting:
1. Server runs
2. API responds
3. Response time < 3 seconds
4. Callback works
5. No crashes after multiple requests
"""

import os
import requests
import json
import time
import uuid
import sys
from datetime import datetime, timezone

# Configuration (from environment variables)
BASE_URL = os.getenv("API_BASE_URL", os.getenv("BASE_URL", "http://localhost:8000"))
API_KEY = os.getenv("API_KEY", "change-me-in-production")
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# Test results
results = {
    "server_runs": {"passed": False, "details": ""},
    "api_responds": {"passed": False, "details": ""},
    "response_time_ok": {"passed": False, "details": ""},
    "callback_works": {"passed": False, "details": ""},
    "stability_ok": {"passed": False, "details": ""}
}

def test_server_runs():
    """Test 1: Check if server is running"""
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            results["server_runs"]["passed"] = True
            results["server_runs"]["details"] = f"Server running, response time: {elapsed:.3f}s"
            return True
        else:
            results["server_runs"]["details"] = f"Server returned status {response.status_code}"
            return False
    except requests.exceptions.ConnectionError:
        results["server_runs"]["details"] = "Cannot connect to server"
        return False
    except Exception as e:
        results["server_runs"]["details"] = str(e)
        return False

def test_api_responds():
    """Test 2: Check if API endpoints respond correctly"""
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/", None),
        ("GET", "/api/stats", None),
    ]
    
    endpoint_results = []
    all_passed = True
    for method, endpoint, data in endpoints:
        try:
            start = time.time()
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", headers=HEADERS, json=data, timeout=5)
            elapsed = time.time() - start
            
            passed = response.status_code in [200, 201]
            endpoint_results.append(f"{method} {endpoint}: {response.status_code} ({elapsed:.3f}s)")
            if not passed:
                all_passed = False
        except Exception as e:
            endpoint_results.append(f"{method} {endpoint}: FAILED ({e})")
            all_passed = False
    
    results["api_responds"]["passed"] = all_passed
    results["api_responds"]["details"] = "; ".join(endpoint_results)
    return all_passed

def test_response_time():
    """Test 3: Check if response time is < 3 seconds"""
    session_id = f"time-test-{uuid.uuid4().hex[:8]}"
    
    test_message = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Hello, I need your help with a banking issue.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    times = []
    for i in range(3):
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/honeypot",
                headers=HEADERS,
                json=test_message,
                timeout=10
            )
            elapsed = time.time() - start
            times.append(elapsed)
        except Exception as e:
            times.append(999)
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    results["response_time_ok"]["passed"] = max_time < 3
    results["response_time_ok"]["details"] = f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s"
    return max_time < 3

def test_callback_works():
    """Test 4: Check if GUVI callback works"""
    session_id = f"callback-test-{uuid.uuid4().hex[:8]}"
    
    scam_msg = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "URGENT: Your account 1234567890 is blocked! Pay Rs.500 to verify@upi or call +919876543210. Visit http://fake.com now!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    try:
        response1 = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json=scam_msg, timeout=10)
        
        if response1.status_code != 200:
            results["callback_works"]["details"] = f"Session creation failed: {response1.status_code}"
            return False
        
        result1 = response1.json()
        
        response2 = requests.post(
            f"{BASE_URL}/api/session/{session_id}/send-guvi-callback",
            headers=HEADERS,
            timeout=15
        )
        
        result2 = response2.json()
        
        if response2.status_code == 200:
            guvi_resp = result2.get("guvi_response", {})
            payload = guvi_resp.get("payload_sent", {})
            required_fields = ["sessionId", "scamDetected", "totalMessagesExchanged", "extractedIntelligence", "agentNotes"]
            missing = [f for f in required_fields if f not in payload]
            
            results["callback_works"]["passed"] = True
            results["callback_works"]["details"] = f"Callback sent, GUVI status: {guvi_resp.get('status_code', 'N/A')}, Missing fields: {missing if missing else 'None'}"
            return True
        else:
            results["callback_works"]["details"] = f"Callback endpoint failed: {response2.status_code}"
            return False
            
    except Exception as e:
        results["callback_works"]["details"] = str(e)
        return False

def test_stability():
    """Test 5: Check stability with multiple requests"""
    num_requests = 10
    success_count = 0
    times = []
    
    for i in range(num_requests):
        session_id = f"stability-{i+1}-{uuid.uuid4().hex[:4]}"
        msg = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": f"Test message {i+1} for stability check",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        
        try:
            start = time.time()
            response = requests.post(f"{BASE_URL}/api/honeypot", headers=HEADERS, json=msg, timeout=15)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                success_count += 1
                times.append(elapsed)
        except:
            pass
    
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        server_ok = health.status_code == 200
    except:
        server_ok = False
    
    avg_time = sum(times) / len(times) if times else 0
    max_time = max(times) if times else 0
    
    results["stability_ok"]["passed"] = success_count == num_requests and server_ok
    results["stability_ok"]["details"] = f"Success: {success_count}/{num_requests}, Avg: {avg_time:.3f}s, Max: {max_time:.3f}s, Server: {'OK' if server_ok else 'DOWN'}"
    return results["stability_ok"]["passed"]

def main():
    print("Running pre-deployment checks...")
    
    if not test_server_runs():
        print("Server not running! Start with: python run.py")
        print(json.dumps(results, indent=2))
        return 1
    
    test_api_responds()
    test_response_time()
    test_callback_works()
    test_stability()
    
    # Save results to JSON file
    with open("deployment_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    all_passed = all(r["passed"] for r in results.values())
    
    print()
    print("=" * 60)
    print("PRE-DEPLOYMENT CHECK RESULTS")
    print("=" * 60)
    
    for name, data in results.items():
        status = "PASS" if data["passed"] else "FAIL"
        print(f"[{status}] {name}: {data['details']}")
    
    print()
    if all_passed:
        print("ALL CHECKS PASSED! Ready for deployment.")
        return 0
    else:
        print("SOME CHECKS FAILED! Fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
