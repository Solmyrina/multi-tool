# API Endpoints - Travel Planner

**Purpose**: RESTful API endpoints for travel planning functionality  
**Base URL**: `/api/travel/`  
**Authentication**: Required (Flask-Login session)

---

## 🔌 Endpoint Structure

All endpoints follow REST conventions:
- `GET` - Retrieve data
- `POST` - Create new resource
- `PUT/PATCH` - Update existing resource
- `DELETE` - Remove resource

---

## 📋 Trip Management

### 1. List all trips
```
GET /api/travel/trips
```

**Query Parameters**:
- `status` (optional): Filter by status (planning, confirmed, in_progress, completed, cancelled)
- `year` (optional): Filter by year
- `page` (optional): Pagination (default 1)
- `limit` (optional): Items per page (default 20)

**Response** (200 OK):
```json
{
  "success": true,
  "trips": [
    {
      "id": 1,
      "name": "Summer in Italy",
      "destination_country": "Italy",
      "destination_city": "Rome",
      "start_date": "2025-07-01",
      "end_date": "2025-07-14",
      "total_budget": 2500.00,
      "budget_currency": "EUR",
      "status": "planning",
      "activity_count": 15,
      "accommodation_count": 3,
      "total_spent": 450.00,
      "created_at": "2025-06-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5
  }
}
```

---

### 2. Get single trip details
```
GET /api/travel/trips/<trip_id>
```

**Response** (200 OK):
```json
{
  "success": true,
  "trip": {
    "id": 1,
    "name": "Summer in Italy",
    "description": "Two weeks exploring Rome, Florence, and Venice",
    "destination_country": "Italy",
    "destination_city": "Rome",
    "start_date": "2025-07-01",
    "end_date": "2025-07-14",
    "total_budget": 2500.00,
    "budget_currency": "EUR",
    "status": "planning",
    "timezone": "Europe/Rome",
    "is_public": false,
    "created_at": "2025-06-01T10:00:00Z",
    "updated_at": "2025-06-10T15:30:00Z",
    "stats": {
      "total_days": 14,
      "activity_count": 15,
      "accommodation_count": 3,
      "total_spent": 450.00,
      "budget_remaining": 2050.00
    }
  }
}
```

**Errors**:
- `404`: Trip not found
- `403`: Not authorized to view this trip

---

### 3. Create new trip
```
POST /api/travel/trips
```

**Request Body**:
```json
{
  "name": "Summer in Italy",
  "description": "Two weeks exploring Rome, Florence, and Venice",
  "destination_country": "Italy",
  "destination_city": "Rome",
  "start_date": "2025-07-01",
  "end_date": "2025-07-14",
  "total_budget": 2500.00,
  "budget_currency": "EUR",
  "timezone": "Europe/Rome"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Trip created successfully",
  "trip": {
    "id": 1,
    "name": "Summer in Italy",
    ...
  }
}
```

**Validation Errors** (400):
- `name` required, max 255 chars
- `start_date` required, valid date format
- `end_date` required, must be >= start_date
- `total_budget` must be >= 0

---

### 4. Update trip
```
PUT /api/travel/trips/<trip_id>
PATCH /api/travel/trips/<trip_id>
```

**Request Body** (partial updates allowed):
```json
{
  "name": "Updated Trip Name",
  "total_budget": 3000.00,
  "status": "confirmed"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Trip updated successfully",
  "trip": { ... }
}
```

---

### 5. Delete trip
```
DELETE /api/travel/trips/<trip_id>
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Trip deleted successfully"
}
```

**Note**: Cascades to all related accommodations, activities, routes, etc.

---

## 🏨 Accommodation Management

### 6. List accommodations for trip
```
GET /api/travel/trips/<trip_id>/accommodations
```

**Response** (200 OK):
```json
{
  "success": true,
  "accommodations": [
    {
      "id": 1,
      "name": "Hotel Colosseo",
      "type": "hotel",
      "address": "Via del Colosseo, 123",
      "city": "Rome",
      "country": "Italy",
      "latitude": 41.8902,
      "longitude": 12.4922,
      "check_in_date": "2025-07-01",
      "check_in_time": "15:00:00",
      "check_out_date": "2025-07-05",
      "check_out_time": "11:00:00",
      "cost_per_night": 120.00,
      "total_cost": 480.00,
      "currency": "EUR",
      "booking_reference": "ABC123",
      "rating": 4.5,
      "nights": 4
    }
  ]
}
```

---

### 7. Create accommodation
```
POST /api/travel/trips/<trip_id>/accommodations
```

**Request Body**:
```json
{
  "name": "Hotel Colosseo",
  "type": "hotel",
  "address": "Via del Colosseo, 123",
  "city": "Rome",
  "country": "Italy",
  "latitude": 41.8902,
  "longitude": 12.4922,
  "check_in_date": "2025-07-01",
  "check_in_time": "15:00:00",
  "check_out_date": "2025-07-05",
  "check_out_time": "11:00:00",
  "cost_per_night": 120.00,
  "currency": "EUR",
  "booking_reference": "ABC123",
  "notes": "Free breakfast included"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Accommodation added successfully",
  "accommodation": { ... }
}
```

---

### 8. Update accommodation
```
PUT /api/travel/accommodations/<accommodation_id>
```

### 9. Delete accommodation
```
DELETE /api/travel/accommodations/<accommodation_id>
```

---

## 🎯 Activity Management

### 10. List activities for trip
```
GET /api/travel/trips/<trip_id>/activities
```

**Query Parameters**:
- `date` (optional): Filter by specific date (YYYY-MM-DD)
- `category` (optional): Filter by category
- `priority` (optional): Filter by priority

**Response** (200 OK):
```json
{
  "success": true,
  "activities": [
    {
      "id": 1,
      "name": "Visit Colosseum",
      "description": "Explore the ancient amphitheater",
      "category": "sightseeing",
      "activity_type": "attraction",
      "location_name": "Colosseum",
      "address": "Piazza del Colosseo, 1",
      "city": "Rome",
      "country": "Italy",
      "latitude": 41.8902,
      "longitude": 12.4922,
      "start_datetime": "2025-07-02T09:00:00Z",
      "end_datetime": "2025-07-02T12:00:00Z",
      "duration_minutes": 180,
      "priority": "must_see",
      "cost": 16.00,
      "currency": "EUR",
      "booking_required": true,
      "is_booked": true,
      "booking_reference": "COL-12345",
      "opening_hours": "Daily 09:00-19:00",
      "notes": "Book tickets online in advance"
    }
  ]
}
```

---

### 11. Create activity
```
POST /api/travel/trips/<trip_id>/activities
```

**Request Body**:
```json
{
  "name": "Visit Colosseum",
  "description": "Explore the ancient amphitheater",
  "category": "sightseeing",
  "activity_type": "attraction",
  "location_name": "Colosseum",
  "address": "Piazza del Colosseo, 1",
  "city": "Rome",
  "latitude": 41.8902,
  "longitude": 12.4922,
  "start_datetime": "2025-07-02T09:00:00",
  "duration_minutes": 180,
  "priority": "must_see",
  "cost": 16.00,
  "booking_required": true
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Activity added successfully",
  "activity": { ... }
}
```

---

### 12. Update activity
```
PUT /api/travel/activities/<activity_id>
```

**Special feature**: Drag-and-drop support
```json
{
  "start_datetime": "2025-07-02T14:00:00"
}
```

This updates the activity time when dragged on Gantt chart.

---

### 13. Delete activity
```
DELETE /api/travel/activities/<activity_id>
```

---

### 14. Bulk update activity order
```
POST /api/travel/trips/<trip_id>/activities/reorder
```

**Request Body**:
```json
{
  "activities": [
    {
      "id": 1,
      "start_datetime": "2025-07-02T09:00:00"
    },
    {
      "id": 2,
      "start_datetime": "2025-07-02T14:00:00"
    }
  ]
}
```

Useful for optimized route calculations.

---

## 🗺️ Route Management

### 15. Get routes for trip
```
GET /api/travel/trips/<trip_id>/routes
```

**Response** (200 OK):
```json
{
  "success": true,
  "routes": [
    {
      "id": 1,
      "from_activity": {
        "id": 1,
        "name": "Hotel Colosseo",
        "latitude": 41.8902,
        "longitude": 12.4922
      },
      "to_activity": {
        "id": 2,
        "name": "Colosseum",
        "latitude": 41.8902,
        "longitude": 12.4924
      },
      "transport_mode": "walking",
      "distance_km": 0.5,
      "duration_minutes": 10,
      "departure_time": "2025-07-02T08:50:00Z",
      "arrival_time": "2025-07-02T09:00:00Z"
    }
  ]
}
```

---

### 16. Calculate route
```
POST /api/travel/routes/calculate
```

**Request Body**:
```json
{
  "from_latitude": 41.8902,
  "from_longitude": 12.4922,
  "to_latitude": 41.8902,
  "to_longitude": 12.4924,
  "transport_mode": "walking"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "route": {
    "distance_km": 0.5,
    "duration_minutes": 10,
    "polyline": "encoded_polyline_string",
    "steps": [...]
  }
}
```

Uses OpenStreetMap routing API.

---

### 17. Create route
```
POST /api/travel/trips/<trip_id>/routes
```

---

## 💰 Expense Management

### 18. List expenses
```
GET /api/travel/trips/<trip_id>/expenses
```

**Query Parameters**:
- `category` (optional): Filter by category
- `date_from` (optional): Filter from date
- `date_to` (optional): Filter to date

**Response** (200 OK):
```json
{
  "success": true,
  "expenses": [
    {
      "id": 1,
      "category": "food",
      "subcategory": "dinner",
      "amount": 45.00,
      "currency": "EUR",
      "description": "Trattoria da Luigi",
      "expense_date": "2025-07-02",
      "payment_method": "card",
      "is_paid": true
    }
  ],
  "summary": {
    "total": 450.00,
    "by_category": {
      "food": 150.00,
      "transport": 100.00,
      "activities": 200.00
    }
  }
}
```

---

### 19. Create expense
```
POST /api/travel/trips/<trip_id>/expenses
```

### 20. Update expense
```
PUT /api/travel/expenses/<expense_id>
```

### 21. Delete expense
```
DELETE /api/travel/expenses/<expense_id>
```

---

## 📄 Document Management

### 22. List documents
```
GET /api/travel/trips/<trip_id>/documents
```

### 23. Upload document
```
POST /api/travel/trips/<trip_id>/documents
Content-Type: multipart/form-data
```

**Form Data**:
- `file`: File to upload
- `document_type`: Type (flight, hotel, passport, etc.)
- `title`: Document title
- `description`: Optional description

---

## ✅ Packing List

### 24. Get packing list
```
GET /api/travel/trips/<trip_id>/packing
```

**Response** (200 OK):
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "category": "clothing",
      "item_name": "T-shirts",
      "quantity": 5,
      "is_packed": true,
      "is_essential": true
    }
  ],
  "stats": {
    "total_items": 25,
    "packed_items": 10,
    "completion_percentage": 40
  }
}
```

---

### 25. Add packing item
```
POST /api/travel/trips/<trip_id>/packing
```

### 26. Toggle packed status
```
PATCH /api/travel/packing/<item_id>/toggle
```

---

## 🌤️ Weather Integration

### 27. Get weather forecast
```
GET /api/travel/trips/<trip_id>/weather
```

**Query Parameters**:
- `date` (optional): Specific date
- `location` (optional): Specific location (accommodation/activity ID)

**Response** (200 OK):
```json
{
  "success": true,
  "forecasts": [
    {
      "date": "2025-07-02",
      "location": "Rome",
      "temperature_high": 32,
      "temperature_low": 22,
      "condition": "sunny",
      "precipitation_chance": 10,
      "activities_affected": [1, 2]
    }
  ]
}
```

Uses existing weather API endpoint from your system.

---

## 📊 Analytics & Summary

### 28. Get trip summary
```
GET /api/travel/trips/<trip_id>/summary
```

**Response** (200 OK):
```json
{
  "success": true,
  "summary": {
    "total_days": 14,
    "total_activities": 15,
    "total_accommodations": 3,
    "total_distance_km": 125.5,
    "budget": {
      "total": 2500.00,
      "spent": 450.00,
      "remaining": 2050.00,
      "by_category": {...}
    },
    "timeline": {
      "days": [
        {
          "date": "2025-07-02",
          "activities": 3,
          "total_cost": 50.00,
          "weather": "sunny"
        }
      ]
    }
  }
}
```

---

### 29. Get daily itinerary
```
GET /api/travel/trips/<trip_id>/daily/<date>
```

**Response** (200 OK):
```json
{
  "success": true,
  "date": "2025-07-02",
  "accommodation": {...},
  "activities": [
    {
      "time": "09:00",
      "activity": {...},
      "route_to_next": {...}
    }
  ],
  "weather": {...},
  "total_cost": 50.00
}
```

---

## 🔒 Authentication & Permissions

All endpoints require authenticated user (Flask-Login session).

**Ownership check**:
- User must own the trip to modify it
- Future: `trip_participants` table for shared access

**Error Responses**:
- `401 Unauthorized`: Not logged in
- `403 Forbidden`: Not authorized for this trip
- `404 Not Found`: Resource doesn't exist
- `400 Bad Request`: Validation errors
- `500 Internal Server Error`: Server error

---

## 📝 Implementation Notes

### Error Response Format
```json
{
  "success": false,
  "error": "Error message here",
  "details": {...} // Optional validation details
}
```

### Pagination Format
All list endpoints support:
- `?page=1`
- `?limit=20`

### Date/Time Formats
- Dates: ISO 8601 (`YYYY-MM-DD`)
- Datetimes: ISO 8601 with timezone (`2025-07-02T09:00:00Z`)
- Times: 24-hour format (`15:00:00`)

---

*Next: [Frontend Components](./03_FRONTEND_COMPONENTS.md)*
