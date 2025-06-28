from dotenv import load_dotenv
from typing import Optional
import os
import json
print("GROQ Key:", os.getenv("GROQ_API_KEY")[:10] + "...")
print("Google Client ID:", json.loads(os.getenv("GOOGLE_CLIENT_SECRETS"))["installed"]["client_id"][:10] + "...")
from function import create_event, update_event, delete_event, get_events
from typing import Optional, TypedDict, Annotated, Sequence
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
import pytz
import calendar
from datetime import datetime, timedelta
import re
from dateutil import parser as date_parser
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode

load_dotenv()

llm = ChatGroq(
    model="qwen-qwq-32b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

class CheckAvailabilityParameters(BaseModel):
    date: str = Field(description="date to check availability (YYYY-MM-DD)")
    start_time: Optional[str] = Field(description="start time to check from (HH:MM)")
    end_time: Optional[str] = Field(description="end time to check until (HH:MM)")

class SuggestTimeSlotsParameters(BaseModel):
    date: str = Field(description="preferred date for the appointment (YYYY-MM-DD)")
    duration: int = Field(1, description="duration of the appointment in hours")
    preferred_time: Optional[str] = Field(description="preferred time if any (morning, afternoon, evening, or HH:MM)")

class ConfirmBookingParameters(BaseModel):
    date: str = Field(description="date of the appointment (YYYY-MM-DD)")
    time: str = Field(description="time of the appointment (HH:MM)")
    name: str = Field("Appointment", description="name/title of the appointment (defaults to 'Appointment')")
    duration: int = Field(1, description="duration in hours")
    description: Optional[str] = Field(None, description="description of the appointment")
    location: Optional[str] = Field(None, description="location of the appointment")

class DeleteEventParameters(BaseModel):
    event_name: str = Field(description="name of the event to be deleted")

class UpdateEventParameters(BaseModel):
    event_name: str = Field(description="name of the event to be updated")
    date: Optional[str] = Field(description="updated start date of the event (YYYY-MM-DD)")
    time: Optional[str] = Field(description="updated start time of the event (HH:MM)")
    duration: Optional[int] = Field(description="updated duration in hours")
    name: Optional[str] = Field(description="updated title of the event")
    description: Optional[str] = Field(description="updated description of the event")
    location: Optional[str] = Field(description="updated location of the event")

class CreateEventParameters(BaseModel):
    date: str = Field(description="start date of the event (YYYY-MM-DD)")
    time: str = Field(description="start time of the event (HH:MM)")
    name: str = Field("Appointment", description="name or title of the event (default: 'Appointment' if not specified)")
    duration: int = Field(1, description="duration of the event in hours (default: 1)")
    description: Optional[str] = Field(None, description="description of the event")
    location: Optional[str] = Field(None, description="location of the event")

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def parse_relative_date(date_str, current_time):
    date_str = date_str.lower().strip()
    
    if date_str in ['today']:
        return current_time.strftime('%Y-%m-%d')
    elif date_str in ['tomorrow']:
        return (current_time + timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'next' in date_str:
        days_ahead = 7
        if 'monday' in date_str:
            days_ahead = (0 - current_time.weekday()) % 7 + 7
        elif 'tuesday' in date_str:
            days_ahead = (1 - current_time.weekday()) % 7 + 7
        elif 'wednesday' in date_str:
            days_ahead = (2 - current_time.weekday()) % 7 + 7
        elif 'thursday' in date_str:
            days_ahead = (3 - current_time.weekday()) % 7 + 7
        elif 'friday' in date_str:
            days_ahead = (4 - current_time.weekday()) % 7 + 7
        elif 'saturday' in date_str:
            days_ahead = (5 - current_time.weekday()) % 7 + 7
        elif 'sunday' in date_str:
            days_ahead = (6 - current_time.weekday()) % 7 + 7
        return (current_time + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    try:
        parsed_date = date_parser.parse(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except:
        return None

def parse_time_preference(time_str):
    if not time_str:
        return None
    
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
        hour = int(re.findall(r'\d+', time_str)[0])
        if 'pm' in time_str and hour != 12:
            hour += 12
        elif 'am' in time_str and hour == 12:
            hour = 0
        return f"{hour:02d}:00"
    
    return None

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

def confirm_booking_details(date, time, name, duration, description=None, location=None):
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%A, %B %d, %Y')
    
    start_time = datetime.strptime(time, '%H:%M')
    end_time = start_time + timedelta(hours=duration)
    
    confirmation = f"""
📅 **Appointment Confirmation**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **Title:** {name}
📅 **Date:** {formatted_date}
🕐 **Time:** {time} - {end_time.strftime('%H:%M')}
⏱️ **Duration:** {duration} hour(s)
"""
    
    if description:
        confirmation += f"📝 **Description:** {description}\n"
    if location:
        confirmation += f"📍 **Location:** {location}\n"
    
    confirmation += "\n✅ **Status:** Ready to book"
    return confirmation

def create_tools():
    return [
        StructuredTool.from_function(
            name="check_availability",
            func=check_availability,
            description="Check calendar availability for a specific date and time range",
            args_schema=CheckAvailabilityParameters,
        ),
        StructuredTool.from_function(
            name="suggest_time_slots",
            func=suggest_time_slots,
            description="Suggest available time slots for booking an appointment",
            args_schema=SuggestTimeSlotsParameters,
        ),
        StructuredTool.from_function(
            name="confirm_booking_details",
            func=confirm_booking_details,
            description="Show formatted confirmation details before booking",
            args_schema=ConfirmBookingParameters,
        ),
        StructuredTool.from_function(
            name="create_event",
            func=create_event,
            description="Create an event in Google Calendar after confirmation",
            args_schema=CreateEventParameters,
        ),
        StructuredTool.from_function(
            name="update_event",
            func=update_event,
            description="Update an event in Google Calendar",
            args_schema=UpdateEventParameters,
        ),
        StructuredTool.from_function(
            name="delete_event",
            func=delete_event,
            description="Delete an event from Google Calendar",
            args_schema=DeleteEventParameters,
        ),
    ]

def get_system_prompt(current_time):
    timezone = pytz.timezone("UTC")
    tomorrow_date = current_time + timedelta(days=1)
    current_year = current_time.year
    
    return f"""You are a helpful and conversational AI scheduling assistant for booking appointments on Google Calendar.

- Do NOT say the event is booked unless the create_event tool is actually called.
- ALWAYS call the create_event tool to finalize booking.
- Confirm with the user, then execute tool.

**Your Conversation Flow:**
1. **Understand Intent**: Listen to what the user wants to schedule
2. **Check Availability**: Always check calendar availability before suggesting times
3. **Suggest Options**: If the preferred time is busy, suggest alternative time slots
4. **Confirm Details**: Suggest a name (optional) and confirm the booking
...
- Use defaults if user skips details (e.g., "Appointment" as title)
- Don't interrupt flow with too many strict follow-ups
- Be conversational and flexible with partial input

5. **Book Appointment**: Only create the calendar event after user confirms

**Guidelines:**
- Be conversational and friendly, not robotic
- Always check availability first using check_availability tool
- If conflicts exist, use suggest_time_slots to offer alternatives
- Use confirm_booking_details before creating any event
- Handle relative dates like "today", "tomorrow", "next Monday"
- Understand time preferences like "morning", "afternoon", "evening"
- Ask follow-up questions if information is missing
- Remember context throughout the conversation

**Available Tools:**
- check_availability: Check if a time slot is free
- suggest_time_slots: Find alternative available times
- confirm_booking_details: Show booking confirmation
- create_event: Book the appointment (only after confirmation)
- update_event: Modify existing appointments
- delete_event: Cancel appointments

Current UTC time: {current_time}
ISO format: {current_time.astimezone(timezone).isoformat()}
Tomorrow (ISO): {tomorrow_date.isoformat()}
Day of the week: {calendar.day_name[current_time.astimezone(timezone).weekday()]}
Current year: {current_year}

Always be helpful and make the booking process smooth and natural!"""

def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    
    # Check if last message has tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return END

def call_model(state: AgentState):
   
    messages = state['messages']
    

    current_time = datetime.now(pytz.timezone("UTC"))
    system_prompt = get_system_prompt(current_time)
    
   
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=system_prompt)] + list(messages)
    

    tools = create_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def create_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(create_tools()))
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

def process_message(conversation: list) -> tuple[list, str]:
    try:
        initial_state = {"messages": conversation}
        # Remove unnecessary compilation step
        app = create_agent_graph()
        final_state = app.invoke(initial_state)
        
        # Extract last assistant response
        last_assistant_message = ""
        for msg in reversed(final_state["messages"]):
            if msg.type == "ai" and msg.content:
                last_assistant_message = msg.content
                break
        
        return final_state["messages"], last_assistant_message
        
    except Exception as e:
        print(f"Error processing message: {e}")
        return conversation, "Sorry, I couldn't process your request. Please try again."

def main(conversation):
    if not conversation:
        print("⚠️ No user input received.")
        return

    initial_state = {
        "messages": conversation
    }

    print("Processing your request...")
    try:
        for chunk in create_agent_graph().stream(initial_state):
            if "agent" in chunk:
                message = chunk["agent"]["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    print(f"\n🤖 Assistant: {message.content}")
                    conversation.append(message)
            elif "tools" in chunk:
                for message in chunk["tools"]["messages"]:
                    print(f"🛠️ Tool executed: {message.name}")
                    if isinstance(message, ToolMessage):
                        if "check_availability" in str(message):
                            print("📅 Checking calendar availability...")
                        elif "suggest_time_slots" in str(message):
                            print("🔍 Finding available time slots...")
                        elif "confirm_booking" in str(message):
                            print("✅ Preparing booking confirmation...")
                        elif "create_event" in str(message):
                            print("📝 Booking appointment...")

                        if message.content and len(message.content) > 10:
                            print(f"📊 Result: {message.content}")
                        conversation.append(message)
    except Exception as e:
        print(f"❌ Error executing agent: {e}")


if __name__ == "__main__":
    print("💬 Welcome to TailorTalk - AI Appointment Assistant!")
    print("Type 'exit' anytime to quit.\n")

    from langchain_core.messages import HumanMessage

    conversation = []

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            print("👋 Goodbye!")
            break

        conversation.append(HumanMessage(content=user_input))
        main(conversation)