from api_call import service

if service:
    print("✅ Google Calendar service initialized successfully")
    try:
        calendars = service.calendarList().list().execute()
        print(f"✅ Found {len(calendars.get('items', []))} calendars")
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
else:
    print("❌ Calendar service not initialized")