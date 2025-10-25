# Calendar Export - Google Calendar Integration

**Purpose**: Export trip itinerary to Google Calendar via .ics file download  
**Implementation**: Simple download button, no OAuth required  
**Complexity**: Low (1-2 days)

---

## 🎯 Feature Overview

Add a button to export the entire trip itinerary to Google Calendar (or any calendar app that supports .ics files like Apple Calendar, Outlook, etc.).

**How it works**:
1. User clicks "Add to Google Calendar" button
2. System generates `.ics` file with all trip events
3. User downloads the file
4. User imports it to Google Calendar manually

**No integration needed** - just a downloadable calendar file!

---

## 📄 iCalendar (.ics) Format

### What is .ics?
Standard calendar format (RFC 5545) supported by:
- Google Calendar
- Apple Calendar
- Microsoft Outlook
- Any calendar application

### Basic Structure
```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Travel Planner//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Summer in Italy
X-WR-TIMEZONE:Europe/Rome

BEGIN:VEVENT
UID:trip-1-activity-1@travelplanner.local
DTSTAMP:20251025T120000Z
DTSTART:20250702T090000Z
DTEND:20250702T120000Z
SUMMARY:Visit Colosseum
DESCRIPTION:Explore the ancient amphitheater\nPriority: Must See
LOCATION:Piazza del Colosseo, 1, Rome, Italy
GEO:41.8902;12.4922
STATUS:CONFIRMED
CATEGORIES:Sightseeing
END:VEVENT

BEGIN:VEVENT
UID:trip-1-accommodation-1@travelplanner.local
DTSTAMP:20251025T120000Z
DTSTART:20250701T150000Z
DTEND:20250705T110000Z
SUMMARY:🏨 Hotel Colosseo
DESCRIPTION:Check-in: 15:00\nCheck-out: 11:00\nBooking: ABC123
LOCATION:Via del Colosseo, 123, Rome, Italy
GEO:41.8902;12.4922
STATUS:CONFIRMED
CATEGORIES:Accommodation
END:VEVENT

END:VCALENDAR
```

---

## 🔌 Backend Implementation

### API Endpoint

```python
# api/travel_api.py

from datetime import datetime
from flask import Response

@travel_bp.route('/trips/<int:trip_id>/export/calendar', methods=['GET'])
@login_required
def export_to_calendar(trip_id):
    """Generate .ics file for trip"""
    try:
        # Verify user owns trip
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get trip details
                cur.execute("""
                    SELECT * FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, current_user.id))
                
                trip = cur.fetchone()
                if not trip:
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get all activities
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE trip_id = %s 
                    ORDER BY start_datetime
                """, (trip_id,))
                activities = cur.fetchall()
                
                # Get all accommodations
                cur.execute("""
                    SELECT * FROM accommodations 
                    WHERE trip_id = %s 
                    ORDER BY check_in_date
                """, (trip_id,))
                accommodations = cur.fetchall()
        
        # Generate .ics file content
        ics_content = generate_ics_file(trip, activities, accommodations)
        
        # Return as downloadable file
        response = Response(ics_content, mimetype='text/calendar')
        response.headers['Content-Disposition'] = f'attachment; filename="{trip["name"]}.ics"'
        response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_ics_file(trip, activities, accommodations):
    """Generate iCalendar format content"""
    
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Travel Planner//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'X-WR-CALNAME:{escape_ics_text(trip["name"])}',
        f'X-WR-TIMEZONE:{trip["timezone"] or "UTC"}',
        ''
    ]
    
    # Add accommodation events
    for acc in accommodations:
        lines.extend(create_accommodation_event(trip, acc))
    
    # Add activity events
    for act in activities:
        lines.extend(create_activity_event(trip, act))
    
    lines.extend([
        'END:VCALENDAR',
        ''
    ])
    
    return '\r\n'.join(lines)


def create_accommodation_event(trip, accommodation):
    """Create VEVENT for accommodation"""
    
    # Format dates (no timezone conversion, use as-is)
    check_in = f"{accommodation['check_in_date'].replace('-', '')}"
    check_in_time = f"{accommodation['check_in_time'].replace(':', '')}"
    check_out = f"{accommodation['check_out_date'].replace('-', '')}"
    check_out_time = f"{accommodation['check_out_time'].replace(':', '')}"
    
    # Build description
    description_parts = [
        f"Check-in: {accommodation['check_in_time']}",
        f"Check-out: {accommodation['check_out_time']}"
    ]
    
    if accommodation.get('booking_reference'):
        description_parts.append(f"Booking: {accommodation['booking_reference']}")
    
    if accommodation.get('cost_per_night'):
        description_parts.append(
            f"Cost: {accommodation['cost_per_night']} {accommodation['currency']}/night"
        )
    
    if accommodation.get('notes'):
        description_parts.append(f"\\n{accommodation['notes']}")
    
    description = '\\n'.join(description_parts)
    
    # Build location
    location_parts = []
    if accommodation.get('address'):
        location_parts.append(accommodation['address'])
    if accommodation.get('city'):
        location_parts.append(accommodation['city'])
    if accommodation.get('country'):
        location_parts.append(accommodation['country'])
    location = ', '.join(location_parts)
    
    # Build event
    event = [
        'BEGIN:VEVENT',
        f'UID:trip-{trip["id"]}-acc-{accommodation["id"]}@travelplanner.local',
        f'DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}',
        f'DTSTART:{check_in}T{check_in_time}00',
        f'DTEND:{check_out}T{check_out_time}00',
        f'SUMMARY:🏨 {escape_ics_text(accommodation["name"])}',
        f'DESCRIPTION:{escape_ics_text(description)}',
    ]
    
    if location:
        event.append(f'LOCATION:{escape_ics_text(location)}')
    
    if accommodation.get('latitude') and accommodation.get('longitude'):
        event.append(f'GEO:{accommodation["latitude"]};{accommodation["longitude"]}')
    
    event.extend([
        'STATUS:CONFIRMED',
        'CATEGORIES:Accommodation',
        'END:VEVENT',
        ''
    ])
    
    return event


def create_activity_event(trip, activity):
    """Create VEVENT for activity"""
    
    # Format datetime (convert to UTC for VEVENT)
    start_dt = activity['start_datetime']
    
    # Calculate end time
    if activity.get('end_datetime'):
        end_dt = activity['end_datetime']
    elif activity.get('duration_minutes'):
        from datetime import timedelta
        end_dt = start_dt + timedelta(minutes=activity['duration_minutes'])
    else:
        # Default 1 hour
        from datetime import timedelta
        end_dt = start_dt + timedelta(hours=1)
    
    # Format for iCalendar (YYYYMMDDTHHMMSSZ)
    start_str = start_dt.strftime('%Y%m%dT%H%M%SZ')
    end_str = end_dt.strftime('%Y%m%dT%H%M%SZ')
    
    # Build description
    description_parts = []
    
    if activity.get('description'):
        description_parts.append(activity['description'])
    
    if activity.get('priority'):
        description_parts.append(f"Priority: {activity['priority'].replace('_', ' ').title()}")
    
    if activity.get('cost'):
        description_parts.append(f"Cost: {activity['cost']} {activity['currency']}")
    
    if activity.get('booking_reference'):
        description_parts.append(f"Booking: {activity['booking_reference']}")
    
    if activity.get('opening_hours'):
        description_parts.append(f"Hours: {activity['opening_hours']}")
    
    if activity.get('notes'):
        description_parts.append(f"\\n{activity['notes']}")
    
    description = '\\n'.join(description_parts)
    
    # Build location
    location_parts = []
    if activity.get('location_name'):
        location_parts.append(activity['location_name'])
    if activity.get('address'):
        location_parts.append(activity['address'])
    if activity.get('city'):
        location_parts.append(activity['city'])
    location = ', '.join(location_parts)
    
    # Get category icon
    category_icons = {
        'sightseeing': '🏛️',
        'dining': '🍽️',
        'transport': '🚗',
        'entertainment': '🎭',
        'shopping': '🛍️',
        'other': '📍'
    }
    icon = category_icons.get(activity.get('category'), '📍')
    
    # Build event
    event = [
        'BEGIN:VEVENT',
        f'UID:trip-{trip["id"]}-act-{activity["id"]}@travelplanner.local',
        f'DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}',
        f'DTSTART:{start_str}',
        f'DTEND:{end_str}',
        f'SUMMARY:{icon} {escape_ics_text(activity["name"])}',
        f'DESCRIPTION:{escape_ics_text(description)}',
    ]
    
    if location:
        event.append(f'LOCATION:{escape_ics_text(location)}')
    
    if activity.get('latitude') and activity.get('longitude'):
        event.append(f'GEO:{activity["latitude"]};{activity["longitude"]}')
    
    # Add alarm/reminder for high priority items
    if activity.get('priority') in ['must_see', 'high']:
        event.extend([
            'BEGIN:VALARM',
            'ACTION:DISPLAY',
            'DESCRIPTION:Reminder',
            'TRIGGER:-PT1H',  # 1 hour before
            'END:VALARM'
        ])
    
    event.extend([
        'STATUS:CONFIRMED',
        f'CATEGORIES:{activity.get("category", "other").title()}',
        'END:VEVENT',
        ''
    ])
    
    return event


def escape_ics_text(text):
    """Escape special characters for iCalendar format"""
    if not text:
        return ''
    
    # Convert to string if needed
    text = str(text)
    
    # Escape special characters
    text = text.replace('\\', '\\\\')  # Backslash
    text = text.replace(',', '\\,')     # Comma
    text = text.replace(';', '\\;')     # Semicolon
    text = text.replace('\n', '\\n')    # Newline
    
    return text
```

---

## 🎨 Frontend Implementation

### Button in Trip Detail Page

```html
<!-- webapp/templates/travel/trip_detail.html -->

<div class="sticky-header border-bottom pb-3 mb-3">
    <div class="d-flex justify-content-between align-items-center">
        <div>
            <h1>{{ trip.name }}</h1>
            <!-- ... existing code ... -->
        </div>
        <div class="btn-group">
            <!-- NEW: Calendar Export Button -->
            <a href="{{ url_for('travel.export_calendar', trip_id=trip.id) }}" 
               class="btn btn-success"
               download="{{ trip.name }}.ics"
               title="Add all activities to your calendar">
                <i class="fab fa-google"></i>
                <i class="fas fa-calendar-plus"></i>
                Add to Calendar
            </a>
            
            <!-- Existing buttons -->
            <button class="btn btn-outline-primary" onclick="showDailyView()">
                <i class="fas fa-calendar-day"></i> Daily View
            </button>
            <!-- ... rest of buttons ... -->
        </div>
    </div>
</div>
```

### Alternative: Dropdown with Options

```html
<!-- Multiple export options -->
<div class="btn-group">
    <button type="button" class="btn btn-success dropdown-toggle" 
            data-bs-toggle="dropdown" aria-expanded="false">
        <i class="fas fa-calendar-plus"></i> Export Calendar
    </button>
    <ul class="dropdown-menu">
        <li>
            <a class="dropdown-item" 
               href="/api/travel/trips/{{ trip.id }}/export/calendar">
                <i class="fab fa-google"></i> Google Calendar (.ics)
            </a>
        </li>
        <li>
            <a class="dropdown-item" 
               href="/api/travel/trips/{{ trip.id }}/export/calendar">
                <i class="fab fa-apple"></i> Apple Calendar (.ics)
            </a>
        </li>
        <li>
            <a class="dropdown-item" 
               href="/api/travel/trips/{{ trip.id }}/export/calendar">
                <i class="fab fa-microsoft"></i> Outlook (.ics)
            </a>
        </li>
        <li><hr class="dropdown-divider"></li>
        <li>
            <a class="dropdown-item" 
               href="/api/travel/trips/{{ trip.id }}/export/json">
                <i class="fas fa-file-code"></i> JSON Export
            </a>
        </li>
        <li>
            <a class="dropdown-item" 
               href="/api/travel/trips/{{ trip.id }}/export/pdf">
                <i class="fas fa-file-pdf"></i> PDF Itinerary
            </a>
        </li>
    </ul>
</div>
```

### JavaScript Enhancement (Optional)

```javascript
// static/js/travel/trip_detail.js

// Track calendar export
document.querySelector('[href*="/export/calendar"]').addEventListener('click', function(e) {
    // Analytics tracking
    console.log('Calendar export clicked');
    
    // Show success message after download
    setTimeout(() => {
        showInstructions();
    }, 1000);
});

function showInstructions() {
    const modal = new bootstrap.Modal(document.getElementById('calendarInstructionsModal'));
    modal.show();
}
```

### Instructions Modal

```html
<!-- webapp/templates/travel/trip_detail.html -->

<!-- Modal with import instructions -->
<div class="modal fade" id="calendarInstructionsModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fas fa-calendar-check"></i>
                    Import to Google Calendar
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <h6>How to import:</h6>
                <ol>
                    <li>The <code>.ics</code> file has been downloaded</li>
                    <li>Go to <a href="https://calendar.google.com" target="_blank">Google Calendar</a></li>
                    <li>Click the <strong>⚙️ Settings</strong> gear icon</li>
                    <li>Select <strong>Import & Export</strong></li>
                    <li>Click <strong>Select file from your computer</strong></li>
                    <li>Choose the downloaded <code>{{ trip.name }}.ics</code> file</li>
                    <li>Select which calendar to import to</li>
                    <li>Click <strong>Import</strong></li>
                </ol>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Tip:</strong> All {{ trip.activity_count }} activities and 
                    {{ trip.accommodation_count }} accommodations will be added to your calendar!
                </div>
                
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Note:</strong> Changes made to the trip later won't sync automatically. 
                    Re-export and import if you update your itinerary.
                </div>
            </div>
            <div class="modal-footer">
                <a href="https://support.google.com/calendar/answer/37118" 
                   target="_blank" 
                   class="btn btn-link">
                    Learn More
                </a>
                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                    Got it!
                </button>
            </div>
        </div>
    </div>
</div>
```

---

## 🧪 Testing

### Test Cases

1. **Empty Trip**
   - Trip with no activities or accommodations
   - Should generate valid .ics with calendar metadata only

2. **Full Trip**
   - Trip with 10+ activities and 3 accommodations
   - All events should appear in correct order

3. **Special Characters**
   - Activity names with: commas, semicolons, quotes, newlines
   - Should be properly escaped

4. **Timezones**
   - Trip in different timezone (e.g., Tokyo)
   - Times should be correct when imported

5. **Multi-day Events**
   - Accommodation spanning 5 days
   - Should show as all-day or timed event

### Manual Testing

```bash
# Download .ics file
curl -o test_trip.ics https://localhost/api/travel/trips/1/export/calendar

# Validate .ics format
# On macOS/Linux:
icalendar-validator test_trip.ics

# Or check manually:
cat test_trip.ics
```

Expected output:
```
BEGIN:VCALENDAR
VERSION:2.0
...
BEGIN:VEVENT
...
END:VEVENT
...
END:VCALENDAR
```

### Import Test

1. Download .ics file
2. Open Google Calendar
3. Settings → Import & Export
4. Upload file
5. Verify all events imported correctly

---

## 🎨 Styling Enhancements

### Button Styles

```css
/* static/css/travel.css */

.btn-calendar-export {
    background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
    color: white;
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.btn-calendar-export:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.btn-calendar-export i {
    margin-right: 5px;
}
```

---

## 📊 Analytics (Optional)

Track calendar exports:

```python
# api/travel_api.py

@travel_bp.route('/trips/<int:trip_id>/export/calendar', methods=['GET'])
@login_required
def export_to_calendar(trip_id):
    try:
        # ... existing code ...
        
        # Log export event
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_activity_logs (user_id, action, details)
                    VALUES (%s, 'calendar_export', %s)
                """, (current_user.id, f'trip_id={trip_id}'))
        
        # ... rest of code ...
```

---

## 🚀 Deployment

### Step 1: Add Route
```python
# webapp/app.py

@app.route('/travel/trips/<int:trip_id>/calendar/export')
@login_required
def export_calendar(trip_id):
    """Proxy to API for calendar export"""
    import requests
    
    response = requests.get(
        f'http://api:8000/api/travel/trips/{trip_id}/export/calendar',
        cookies=request.cookies
    )
    
    # Return the .ics file
    return Response(
        response.content,
        mimetype='text/calendar',
        headers={
            'Content-Disposition': f'attachment; filename="trip_{trip_id}.ics"'
        }
    )
```

### Step 2: Test
```bash
# Create test trip
# Add activities
# Click "Add to Calendar"
# Verify .ics downloads
# Import to Google Calendar
# Verify events appear
```

### Step 3: Deploy
```bash
# Restart services
docker compose restart webapp api

# Test endpoint
curl -o test.ics https://localhost/travel/trips/1/calendar/export
```

---

## ✅ Success Criteria

- [ ] Button appears on trip detail page
- [ ] Clicking button downloads .ics file
- [ ] File opens in Google Calendar
- [ ] All activities imported correctly
- [ ] All accommodations imported correctly
- [ ] Timezones handled correctly
- [ ] Special characters escaped properly
- [ ] Instructions modal helpful

---

## 🔮 Future Enhancements

### Phase 2
- **Subscribe to Calendar**: Generate unique URL for calendar feed (auto-updates)
- **Email Calendar**: Send .ics file via email
- **Calendar Sync**: Two-way sync with Google Calendar API (requires OAuth)

### Phase 3
- **Smart Reminders**: Add customizable reminders (1 hour, 1 day before)
- **Color Coding**: Different colors for activity categories
- **Recurring Events**: For repeating activities

---

## 📝 Implementation Checklist

- [ ] Add `generate_ics_file()` function to `api/travel_api.py`
- [ ] Add `/export/calendar` endpoint
- [ ] Add "Add to Calendar" button to trip detail page
- [ ] Add instructions modal
- [ ] Test with sample trip
- [ ] Test import to Google Calendar
- [ ] Test special characters
- [ ] Test timezones
- [ ] Add analytics tracking
- [ ] Update documentation

---

**Estimated Time**: 1-2 days  
**Complexity**: Low  
**Dependencies**: None (uses standard library)  
**Result**: Simple, user-friendly calendar export!

---

*No OAuth, no API keys, no complexity - just a simple download button!* 📅✨
