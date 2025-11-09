"""
Test script for Meeting Transcript Microservice
Run this after starting the service to verify all endpoints work
"""

import requests
import json

BASE_URL = "http://localhost:8888"

# Sample transcript
SAMPLE_TRANSCRIPT = """
John: Good morning everyone, thanks for joining our Q4 planning meeting.
Sarah: Happy to be here. I wanted to discuss our marketing budget for next quarter.
John: Great, let's start there. What are you thinking?
Sarah: I propose we increase the digital marketing budget by 20% and focus on social media campaigns.
Mike: That sounds reasonable. I can prepare a detailed breakdown by Friday.
John: Perfect. Mike, please share that with the team by end of week.
Sarah: Also, we need to finalize the product launch date. I'm thinking January 15th.
John: January 15th works. Let's make that official. Sarah, can you coordinate with the product team?
Sarah: Will do. I'll set up a meeting with them this week.
John: Excellent. Any other items?
Mike: Just a reminder that our analytics tool subscription needs renewal by December 1st.
John: Good catch. Sarah, can you handle that renewal?
Sarah: Sure, I'll take care of it today.
John: Great. I think that covers everything. Thanks everyone!
"""

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_summary():
    """Test summary generation"""
    print("\n=== Testing Summary Generation ===")
    payload = {
        "transcript": SAMPLE_TRANSCRIPT,
        "meeting_title": "Q4 Planning Meeting",
        "meeting_date": "2024-11-08"
    }
    response = requests.post(f"{BASE_URL}/api/v1/summary", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nSummary:\n{data['summary']}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_minutes():
    """Test minutes generation"""
    print("\n=== Testing Minutes Generation ===")
    payload = {
        "transcript": SAMPLE_TRANSCRIPT,
        "meeting_title": "Q4 Planning Meeting",
        "meeting_date": "2024-11-08",
        "participants": ["John", "Sarah", "Mike"]
    }
    response = requests.post(f"{BASE_URL}/api/v1/minutes", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nMinutes:\n{data['minutes']}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_action_items():
    """Test action items extraction"""
    print("\n=== Testing Action Items Extraction ===")
    payload = {
        "transcript": SAMPLE_TRANSCRIPT,
        "meeting_title": "Q4 Planning Meeting",
        "meeting_date": "2024-11-08"
    }
    response = requests.post(f"{BASE_URL}/api/v1/action-items", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nAction Items:")
        for i, item in enumerate(data['action_items'], 1):
            print(f"{i}. {item}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("=" * 60)
    print("Meeting Transcript Service - Test Suite")
    print("=" * 60)
    
    results = {
        "Health Check": test_health_check(),
        "Summary": test_summary(),
        "Minutes": test_minutes(),
        "Action Items": test_action_items()
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("All tests passed! ✓" if all_passed else "Some tests failed ✗"))

if __name__ == "__main__":
    main()