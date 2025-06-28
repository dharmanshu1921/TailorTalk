# 
import datefinder
from api_call import service
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
import pytz

def get_upcoming_events(service):
    try:
        now = datetime.utcnow().isoformat() + "Z"
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return None

        return events

    except HttpError as error:
        print("An error occurred: %s" % error)
        return None

def get_events(start_date, end_date):
    try:

        start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC) + timedelta(days=1)
        
        time_min = start_datetime.isoformat()
        time_max = end_datetime.isoformat()
        
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return events

    except HttpError as error:
        print(f"An error occurred while fetching events: {error}")
        return []
    except ValueError as error:
        print(f"Invalid date format: {error}")
        return []

def list_upcoming_events():
    events = get_upcoming_events(service)
    if events:
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"], event["id"])


def delete_event(event_name, start_date=None, end_date=None, confirm: bool = True):
    try:
        if start_date and end_date:
            events = get_events(start_date, end_date)
        else:
            events = get_upcoming_events(service)

        if not events:
            return "No events found in the specified range."

        matching_events = [event for event in events if event["summary"].lower().strip() == event_name.lower().strip()]
        
        if not matching_events:
            return f"No events found with name '{event_name}'."

        if not confirm:
            event_details = [
                f"{event['start'].get('dateTime', event['start'].get('date'))} - {event['summary']} (ID: {event['id']})"
                for event in matching_events
            ]
            return f"Found {len(matching_events)} matching events:\n{', '.join(event_details)}\nConfirmation required to delete."

        deleted = []
        for event in matching_events:
            try:
                if 'recurringEventId' in event:
                    print(f"Warning: '{event['summary']}' is a recurring event instance. Deleting this instance only.")
                
                service.events().delete(calendarId="primary", eventId=event["id"]).execute()
                deleted.append(event["summary"])
                print(f"Successfully deleted event: {event['summary']} (ID: {event['id']})")
            except HttpError as e:
                print(f"Failed to delete event '{event['summary']}': {e}")
                return f"Failed to delete some events: {e}"

        return f"Deleted {len(deleted)} events: {', '.join(deleted)}"

    except Exception as e:
        print(f"Unexpected error in delete_event: {e}")
        return f"An unexpected error occurred: {e}"



def create_event(date, time, name, duration=1, description=None, location=None):
    
    start_time_str = date + " " +time
    matches = list(datefinder.find_dates(start_time_str))
    if len(matches):
        start_time = matches[0]
        end_time = start_time + timedelta(hours=duration)

        event = {
            'summary': name,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        try:
            event_result = service.events().insert(calendarId="primary", body=event).execute()
            print("Event created successfully!")
            return f"Event '{name}' created successfully for {date} at {time}"
        except HttpError as e:
            print(f"An error occurred while creating the event: {e}")
            return f"Error creating event: {e}"
    else:
        print("Error: Invalid format. Event not created.")
        return "Error: Invalid date/time format. Event not created."

def update_event(event_name, **kwargs):
    events = get_upcoming_events(service)
    if events:
        matching_events = [event for event in events if event["summary"].lower() == event_name.lower()]
        if matching_events:
            print("Matching events to be updated:")
            for event in matching_events:
                print(event["start"].get("dateTime", event["start"].get("date")), event["summary"], event["id"])
            print(event["start"].get("dateTime"))
            print(event["end"].get("dateTime"))
            confirmation = input("Do you want to update these events? (yes/no): ")
            if confirmation.lower() == "yes":
                for event in matching_events:
                    event_id = event["id"]
                    try:
                        updated_event = service.events().get(calendarId="primary", eventId=event_id).execute()
                        print(event["start"].get("duration"))
                        date = kwargs.get("date")
                        start_hours, start_minutes = map(int, [event["start"]["dateTime"][11:13], event["start"]["dateTime"][14:16]])
                        end_hours, end_minutes = map(int, [event["end"]["dateTime"][11:13], event["end"]["dateTime"][14:16]])

                        duration = kwargs.get("duration")
                        if duration:
                            time_difference = timedelta(hours=duration)
                        else :
                            time_difference = timedelta(hours=end_hours - start_hours, minutes=end_minutes - start_minutes)
                            
                        if date:
                            start_time_str = date + " " + updated_event["start"].get("dateTime")[11:16]   
                            matches = list(datefinder.find_dates(start_time_str))
                            if len(matches):
                                start_time = matches[0]
                                end_time = start_time + time_difference
                                updated_event['start']['dateTime'] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
                                updated_event['end']['dateTime'] = end_time.strftime("%Y-%m-%dT%H:%M:%S")

                        time = kwargs.get("time")
                        if time:
                            start_time_str = updated_event["start"].get("dateTime")[:10] + " " + time  
                            matches = list(datefinder.find_dates(start_time_str))

                            if len(matches):
                                start_time = matches[0]
                                updated_event['start']['dateTime'] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
                                if len(matches):
                                    start_time = matches[0]
                                    end_time = start_time +time_difference
                                    updated_event['start']['dateTime'] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
                                    updated_event['end']['dateTime'] = end_time.strftime("%Y-%m-%dT%H:%M:%S")
                        
                        name = kwargs.get("name")
                        if name:
                            updated_event['summary'] = name

                        description = kwargs.get("description")
                        if description:
                            updated_event['description'] = description

                        location = kwargs.get("location")
                        if location:
                            updated_event['location'] = location

                        updated_event = service.events().update(calendarId="primary", eventId=event_id, body=updated_event).execute()
                        print("Event Updated Successfully:", updated_event["summary"])
                        return f"Event '{updated_event['summary']}' updated successfully"

                    except HttpError as e:
                        print(f"An error occurred while updating the event: {e}")
                        return f"Error updating event: {e}"
            else:
                print("Event update cancelled.")
                return "Event update cancelled"
        else:
            print("No matching events found.")
            return "No matching events found"
    else:
        print("No upcoming events found.")
        return "No upcoming events found"

def parse_datetime_from_event(datetime_str):
    if not datetime_str:
        return None
    
    try:
        if datetime_str.endswith('Z'):

            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        elif '+' in datetime_str or datetime_str.count('-') > 2:

            return datetime.fromisoformat(datetime_str)
        else:

            dt = datetime.fromisoformat(datetime_str)
            return dt.replace(tzinfo=pytz.UTC)
    except Exception as e:
        print(f"Error parsing datetime '{datetime_str}': {e}")
        return None

def check_availability(date, start_time=None, end_time=None):
    try:
        events = get_events(date, date) 
        
        if not start_time:
            start_time = "09:00"
        if not end_time:
            end_time = "17:00"
        
        ist = pytz.timezone('Asia/Kolkata')
        utc = pytz.UTC
        
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        start_datetime = datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(f"{date} {end_time}", '%Y-%m-%d %H:%M')
        
        start_datetime = ist.localize(start_datetime).astimezone(utc)
        end_datetime = ist.localize(end_datetime).astimezone(utc)
        
        conflicts = []
        for event in events:
            event_start_str = event.get('start', {}).get('dateTime', '')
            event_end_str = event.get('end', {}).get('dateTime', '')
            
            if not event_start_str or not event_end_str:
                continue
                
            event_start = parse_datetime_from_event(event_start_str)
            event_end = parse_datetime_from_event(event_end_str)
            
            if not event_start or not event_end:
                continue
            
            if event_start.tzinfo is None:
                event_start = utc.localize(event_start)
            if event_end.tzinfo is None:
                event_end = utc.localize(event_end)
            
            if event_start < end_datetime and event_end > start_datetime:
                display_start = event_start.astimezone(ist)
                display_end = event_end.astimezone(ist)
                
                conflicts.append({
                    'name': event.get('summary', 'Untitled Event'),
                    'start': display_start.strftime('%H:%M'),
                    'end': display_end.strftime('%H:%M')
                })
        
        return {
            'available': len(conflicts) == 0,
            'conflicts': conflicts,
            'checked_period': f"{start_time} - {end_time}"
        }
    
    except Exception as e:
        print(f"Error in check_availability: {e}")
        return {
            'available': False,
            'error': str(e),
            'conflicts': []
        }

def suggest_time_slots(date, duration=1, preferred_time=None):
    try:
        events = get_events(date, date)
        
        busy_blocks = []
        ist = pytz.timezone('Asia/Kolkata')
        utc = pytz.UTC
        
        for event in events:
            event_start_str = event.get('start', {}).get('dateTime', '')
            event_end_str = event.get('end', {}).get('dateTime', '')
            
            if not event_start_str or not event_end_str:
                continue
                
            event_start = parse_datetime_from_event(event_start_str)
            event_end = parse_datetime_from_event(event_end_str)
            
            if not event_start or not event_end:
                continue
            
            if event_start.tzinfo is None:
                event_start = utc.localize(event_start)
            if event_end.tzinfo is None:
                event_end = utc.localize(event_end)
                
            event_start_ist = event_start.astimezone(ist)
            event_end_ist = event_end.astimezone(ist)
            
            event_date = event_start_ist.date()
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            if event_date == target_date:
                start_minutes = event_start_ist.hour * 60 + event_start_ist.minute
                end_minutes = event_end_ist.hour * 60 + event_end_ist.minute
                busy_blocks.append((start_minutes, end_minutes))
        
        start_minutes = 9 * 60  # 9:00 AM
        end_minutes = 23 * 60   # 11:00 PM
        duration_minutes = duration * 60
        
        available_slots = []
        current_time = start_minutes
        
        while current_time + duration_minutes <= end_minutes:
            slot_end = current_time + duration_minutes

            conflicts = False
            for busy_start, busy_end in busy_blocks:
                if current_time < busy_end and slot_end > busy_start:
                    conflicts = True
                    current_time = busy_end  
                    break
            
            if not conflicts:
                hour = current_time // 60
                minute = current_time % 60
                available_slots.append(f"{hour:02d}:{minute:02d}")
                current_time += 30 
        
        if preferred_time:
            pref_time = parse_time_preference(preferred_time)
            if pref_time:
                pref_hour = int(pref_time.split(':')[0])
                available_slots.sort(key=lambda x: abs(int(x.split(':')[0]) - pref_hour))
        
        return available_slots[:5]  
    
    except Exception as e:
        print(f"Error in suggest_time_slots: {e}")
        return []


def parse_time_preference(time_str):

    if not time_str:
        return None
    
    import re
    time_str = time_str.lower().strip()
    
    if 'morning' in time_str:
        return "09:00"
    elif 'afternoon' in time_str:
        return "14:00"
    elif 'evening' in time_str:
        return "18:00"
    elif re.match(r'\d{1,2}:\d{2}', time_str):
        return time_str
    elif re.match(r'\d{1,2}(am|pm)', time_str):
        # Convert 12-hour to 24-hour format
        hour = int(re.findall(r'\d+', time_str)[0])
        if 'pm' in time_str and hour != 12:
            hour += 12
        elif 'am' in time_str and hour == 12:
            hour = 0
        return f"{hour:02d}:00"
    
    return None