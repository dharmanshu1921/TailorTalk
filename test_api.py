import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    # Test root endpoint
    health_res = requests.get(BASE_URL)
    print(f"Health Check: {health_res.status_code} - {health_res.json()}")
    
    # Test valid chat request
    print("\nTesting valid scheduling request:")
    chat_payload = {
        "session_id": "test-user-123",
        "message": "Schedule a meeting tomorrow at 2pm for 1 hour"
    }
    chat_res = requests.post(f"{BASE_URL}/chat", json=chat_payload)
    print(f"Status: {chat_res.status_code}")
    print(f"Response: {json.dumps(chat_res.json(), indent=2)}")
    
    # Test calendar query
    print("\nTesting calendar query:")
    query_payload = {
        "session_id": "test-user-123",
        "message": "What's on my calendar tomorrow?"
    }
    query_res = requests.post(f"{BASE_URL}/chat", json=query_payload)
    print(f"Status: {query_res.status_code}")
    print(f"Response: {json.dumps(query_res.json(), indent=2)}")
    
    # Test empty input
    print("\nTesting empty input:")
    empty_payload = {
        "session_id": "test-user-123",
        "message": ""
    }
    empty_res = requests.post(f"{BASE_URL}/chat", json=empty_payload)
    print(f"Status: {empty_res.status_code}")
    print(f"Response: {json.dumps(empty_res.json(), indent=2)}")

if __name__ == "__main__":
    test_api()