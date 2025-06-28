from function import create_event, get_events, delete_event
from datetime import datetime, timedelta
import pytz

# Test data
tomorrow = (datetime.now(pytz.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
test_event = {
    "date": tomorrow,
    "time": "10:00",
    "name": "TEST EVENT - DELETE ME",
    "duration": 0.5
}

def test_event_lifecycle():
    # Create test event
    create_result = create_event(**test_event)
    print(f"Create Result: {create_result}")
    
    # Retrieve events
    events = get_events(tomorrow, tomorrow)
    test_events = [e for e in events if test_event['name'] in e['summary']]
    print(f"Found {len(test_events)} test events")
    
    # Delete test events
    for event in test_events:
        del_result = delete_event(event['summary'], tomorrow, tomorrow)
        print(f"Delete Result: {del_result}")

if __name__ == "__main__":
    test_event_lifecycle()
    