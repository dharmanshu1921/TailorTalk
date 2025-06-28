# streamlit_app.py
import streamlit as st
import requests
import json
from datetime import datetime
import urllib.parse

# Update to your Render-deployed FastAPI URL after deployment
FASTAPI_URL = "http://localhost:8000"

st.title("AI Scheduling Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# Check for OAuth callback credentials in URL
query_params = st.query_params
if "credentials" in query_params:
    st.session_state.credentials = urllib.parse.unquote(query_params["credentials"])
    st.query_params.clear()  # Clear query params after use

# Login Button
if not st.session_state.credentials:
    st.header("Login Required")
    if st.button("Login with Google"):
        try:
            response = requests.get(f"{FASTAPI_URL}/login/")
            response.raise_for_status()
            auth_url = response.json().get("auth_url")
            st.write(f"Please visit this URL to authenticate: {auth_url}")
            # Optionally, use JavaScript to redirect automatically
            st.markdown(f'<meta http-equiv="refresh" content="0;URL={auth_url}">', unsafe_allow_html=True)
        except requests.RequestException as e:
            st.error(f"Error initiating login: {str(e)}")
else:
    # Sidebar for direct actions
    st.sidebar.header("Quick Actions")
    action = st.sidebar.radio("Choose an action:", [
        "Converse with Assistant",
        "Check Availability",
        "Suggest Time Slots",
        "Create Event",
        "Update Event",
        "Delete Event",
        "List Upcoming Events"
    ])

    # Conversational Interface
    if action == "Converse with Assistant":
        st.header("Chat with the Scheduling Assistant")
        
        # Suggested questions as buttons
        st.subheader("Suggested Questions")
        suggestions = [
            "Hey, I want to schedule a call for tomorrow afternoon.",
            "Do you have any free time this Friday?",
            "Book a meeting between 3-5 PM next week."
        ]
        cols = st.columns(3)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(suggestion, key=f"suggestion_{i}"):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    try:
                        response = requests.post(
                            f"{FASTAPI_URL}/converse/",
                            json={"user_input": suggestion, "credentials": st.session_state.credentials}
                        )
                        response.raise_for_status()
                        assistant_response = response.json().get("response", "No response")
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    except requests.RequestException as e:
                        st.error(f"Error: {str(e)}")

        # Custom input
        user_input = st.text_input("Your message:", placeholder="e.g., Book a meeting tomorrow at 10 AM")
        if st.button("Send"):
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/converse/",
                        json={"user_input": user_input, "credentials": st.session_state.credentials}
                    )
                    response.raise_for_status()
                    assistant_response = response.json().get("response", "No response")
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                except requests.RequestException as e:
                    st.error(f"Error: {str(e)}")

        # Display conversation history
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.write(f"**You**: {message['content']}")
            else:
                st.write(f"**Assistant**: {message['content']}")

    # Check Availability Form
    elif action == "Check Availability":
        st.header("Check Calendar Availability")
        with st.form("check_availability"):
            date = st.text_input("Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
            start_time = st.text_input("Start Time (HH:MM)", value="09:00")
            end_time = st.text_input("End Time (HH:MM)", value="17:00")
            submitted = st.form_submit_button("Check")
            if submitted:
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/check-availability/",
                        json={
                            "date": date,
                            "start_time": start_time,
                            "end_time": end_time,
                            "credentials": st.session_state.credentials
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    if result["available"]:
                        st.success(f"Time slot is available: {result['checked_period']}")
                    else:
                        st.warning(f"Conflicts found: {result['conflicts']}")
                except requests.RequestException as e:
                    st.error(f"Error: {str(e)}")

    # Suggest Time Slots Form
    elif action == "Suggest Time Slots":
        st.header("Suggest Available Time Slots")
        with st.form("suggest_time_slots"):
            date = st.text_input("Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
            duration = st.number_input("Duration (hours)", min_value=1, max_value=8, value=1)
            preferred_time = st.text_input("Preferred Time (e.g., morning, 14:00)", value="")
            submitted = st.form_submit_button("Suggest")
            if submitted:
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/suggest-time-slots/",
                        json={
                            "date": date,
                            "duration": duration,
                            "preferred_time": preferred_time or None,
                            "credentials": st.session_state.credentials
                        }
                    )
                    response.raise_for_status()
                    slots = response.json().get("available_slots", [])
                    if slots:
                        st.success(f"Available slots: {', '.join(slots)}")
                    else:
                        st.warning("No available slots found.")
                except requests.RequestException as e:
                    st.error(f"Error: {str(e)}")

    # Create Event Form
    elif action == "Create Event":
        st.header("Create a New Event")
        with st.form("create_event"):
            date = st.text_input("Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
            time = st.text_input("Time (HH:MM)", value="10:00")
            name = st.text_input("Event Name", value="Appointment")
            duration = st.number_input("Duration (hours)", min_value=1, max_value=8, value=1)
            description = st.text_area("Description (optional)", value="")
            location = st.text_input("Location (optional)", value="")
            submitted = st.form_submit_button("Create")
            if submitted:
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/create-event/",
                        json={
                            "date": date,
                            "time": time,
                            "name": name,
                            "duration": duration,
                            "description": description or None,
                            "location": location or None,
                            "credentials": st.session_state.credentials
                        }
                    )
                    response.raise_for_status()
                    st.success(response.json().get("message"))
                except requests.RequestException as e:
                    st.error(f"Error: {str(e)}")

    # Update Event Form
    elif action == "Update Event":
        st.header("Update an Existing Event")
        with st.form("update_event"):
            event_name = st.text_input("Event Name to Update")
            date = st.text_input("New Date (YYYY-MM-DD, optional)", value="")
            time = st.text_input("New Time (HH:MM, optional)", value="")
            duration = st.number_input("New Duration (hours, optional)", min_value=1, max_value=8, value=1)
            new_name = st.text_input("New Event Name (optional)", value="")
            description = st.text_area("New Description (optional)", value="")
            location = st.text_input("New Location (optional)", value="")
            submitted = st.form_submit_button("Update")
            if submitted:
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/update-event/",
                        json={
                            "event_name": event_name,
                            "date": date or None,
                            "time": time or None,
                            "duration": duration,
                            "name": new_name or None,
                            "description": description or None,
                            "location": location or None,
                            "credentials": st.session_state.credentials
                        }
                    )
                    response.raise_for_status()
                    st.success(response.json().get("message"))
                except requests.RequestException as e:
                    st.error(f"Error: {str(e)}")

    # Delete Event Form
    elif action == "Delete Event":
        st.header("Delete an Event")
        with st.form("delete_event"):
            event_name = st.text_input("Event Name to Delete")
            submitted = st.form_submit_button("Delete")
            if submitted:
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/delete-event/",
                        json={"event_name": event_name, "credentials": st.session_state.credentials}
                    )
                    response.raise_for_status()
                    st.success(response.json().get("message"))
                except requests.RequestException as e:
                    st.error(f"Error: {str(e)}")

    # List Upcoming Events
    elif action == "List Upcoming Events":
        st.header("Upcoming Events")
        if st.button("Fetch Events"):
            try:
                response = requests.get(
                    f"{FASTAPI_URL}/upcoming-events/",
                    json={"credentials": st.session_state.credentials}
                )
                response.raise_for_status()
                events = response.json().get("events", [])
                if events:
                    for event in events:
                        st.write(f"- {event['name']} at {event['start']} (ID: {event['id']})")
                else:
                    st.warning("No upcoming events found.")
            except requests.RequestException as e:
                st.error(f"Error: {str(e)}")