# Deployment Plan - Travel Planner

**Purpose**: Step-by-step guide to implement the travel planner feature  
**Timeline**: 4-6 weeks for MVP  
**Risk Level**: Low (builds on existing infrastructure)

---

## 🎯 Implementation Phases

### Phase 1: Database Setup (Week 1)

#### Step 1.1: Create Migration File
```bash
cd /home/one_control/docker-project/database
nano add_travel_planner_tables.sql
```

#### Step 1.2: Write SQL Migration
Copy all table definitions from [01_DATABASE_SCHEMA.md](./01_DATABASE_SCHEMA.md)

```sql
-- Travel Planner Schema Migration
-- Created: October 25, 2025

BEGIN;

-- Create trips table
CREATE TABLE trips (...);

-- Create accommodations table
CREATE TABLE accommodations (...);

-- Create activities table  
CREATE TABLE activities (...);

-- Create routes table
CREATE TABLE routes (...);

-- Create expenses table
CREATE TABLE expenses (...);

-- Create trip_documents table
CREATE TABLE trip_documents (...);

-- Create packing_lists table
CREATE TABLE packing_lists (...);

-- Create indexes
CREATE INDEX ...;

-- Create triggers
CREATE OR REPLACE FUNCTION update_updated_at_column() ...;

COMMIT;
```

#### Step 1.3: Run Migration
```bash
# Option 1: Via psql
docker exec -i docker-project-database psql -U root -d webapp_db < database/add_travel_planner_tables.sql

# Option 2: Via init.sql (add to end of file)
echo "\i /docker-entrypoint-initdb.d/add_travel_planner_tables.sql" >> database/init.sql

# Option 3: Via Flask migration script
python webapp/migrate_travel_planner.py
```

#### Step 1.4: Verify Tables
```bash
docker exec -it docker-project-database psql -U root -d webapp_db -c "\dt"
```

Expected output:
```
 trips
 accommodations
 activities
 routes
 expenses
 trip_documents
 packing_lists
```

---

### Phase 2: Backend API (Week 2)

#### Step 2.1: Create API Blueprint
```python
# api/travel_api.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import psycopg

travel_bp = Blueprint('travel', __name__, url_prefix='/api/travel')

# Database connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'database'),
    'dbname': os.getenv('DB_NAME', 'webapp_db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT', 5432))
}

def get_db_connection():
    return psycopg.connect(**DB_CONFIG)

# Trip endpoints
@travel_bp.route('/trips', methods=['GET'])
@login_required
def list_trips():
    """Get all trips for current user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        t.*,
                        COUNT(DISTINCT a.id) as activity_count,
                        COUNT(DISTINCT ac.id) as accommodation_count,
                        COALESCE(SUM(e.amount_in_base_currency), 0) as total_spent
                    FROM trips t
                    LEFT JOIN activities a ON t.id = a.trip_id
                    LEFT JOIN accommodations ac ON t.id = ac.trip_id
                    LEFT JOIN expenses e ON t.id = e.trip_id
                    WHERE t.user_id = %s
                    GROUP BY t.id
                    ORDER BY t.start_date DESC
                """, (current_user.id,))
                
                trips = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'trips': [dict(trip) for trip in trips]
                })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travel_bp.route('/trips/<int:trip_id>', methods=['GET'])
@login_required
def get_trip(trip_id):
    """Get single trip details"""
    # Implementation from 02_API_ENDPOINTS.md
    pass

@travel_bp.route('/trips', methods=['POST'])
@login_required
def create_trip():
    """Create new trip"""
    # Implementation from 02_API_ENDPOINTS.md
    pass

# ... more endpoints
```

#### Step 2.2: Register Blueprint in api.py
```python
# api/api.py

from travel_api import travel_bp

app.register_blueprint(travel_bp)
```

#### Step 2.3: Test Endpoints
```bash
# Create test trip
curl -X POST https://localhost/api/travel/trips \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Trip",
    "start_date": "2025-12-01",
    "end_date": "2025-12-10",
    "destination_city": "Paris",
    "destination_country": "France",
    "total_budget": 1500
  }'

# List trips
curl https://localhost/api/travel/trips

# Get trip
curl https://localhost/api/travel/trips/1
```

---

### Phase 3: Frontend Templates (Week 3)

#### Step 3.1: Create Template Directory
```bash
mkdir -p webapp/templates/travel
mkdir -p webapp/templates/travel/components
mkdir -p webapp/static/js/travel
mkdir -p webapp/static/css/travel
```

#### Step 3.2: Create Templates
Copy templates from [03_FRONTEND_COMPONENTS.md](./03_FRONTEND_COMPONENTS.md):

```bash
# Main templates
webapp/templates/travel/trip_list.html
webapp/templates/travel/trip_detail.html
webapp/templates/travel/trip_create.html
webapp/templates/travel/trip_edit.html

# Components
webapp/templates/travel/components/gantt_chart.html
webapp/templates/travel/components/map_view.html
webapp/templates/travel/components/activity_form.html
webapp/templates/travel/components/accommodation_form.html
webapp/templates/travel/components/weather_widget.html
```

#### Step 3.3: Create Flask Routes
```python
# webapp/app.py

from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
import requests

@app.route('/travel')
@login_required
def travel_home():
    """Trip list page"""
    # Fetch trips from API
    response = requests.get('http://api:8000/api/travel/trips')
    trips = response.json().get('trips', [])
    
    return render_template('travel/trip_list.html', trips=trips)

@app.route('/travel/trips/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    """Trip detail page"""
    # Fetch trip from API
    response = requests.get(f'http://api:8000/api/travel/trips/{trip_id}')
    trip = response.json().get('trip')
    
    if not trip:
        flash('Trip not found', 'error')
        return redirect(url_for('travel_home'))
    
    return render_template('travel/trip_detail.html', trip=trip)

@app.route('/travel/create', methods=['GET', 'POST'])
@login_required
def create_trip():
    """Create new trip"""
    if request.method == 'POST':
        # Submit to API
        data = request.form.to_dict()
        response = requests.post('http://api:8000/api/travel/trips', json=data)
        
        if response.json().get('success'):
            flash('Trip created successfully!', 'success')
            return redirect(url_for('travel_home'))
    
    return render_template('travel/trip_create.html')
```

#### Step 3.4: Add Navigation Link
```html
<!-- webapp/templates/base.html -->

<li class="nav-item">
    <a class="nav-link" href="{{ url_for('travel_home') }}">
        <i class="fas fa-suitcase-rolling"></i> Travel
    </a>
</li>
```

---

### Phase 4: Gantt Chart Integration (Week 4)

#### Step 4.1: Install Frappe Gantt
Add to `webapp/templates/travel/trip_detail.html`:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.css">
<script src="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js"></script>
```

#### Step 4.2: Implement Gantt Logic
Create `webapp/static/js/travel/gantt.js` with code from [04_GANTT_CHART_IMPLEMENTATION.md](./04_GANTT_CHART_IMPLEMENTATION.md)

#### Step 4.3: Test Drag & Drop
- Create trip with multiple activities
- Verify Gantt chart renders
- Test drag-and-drop time updates
- Verify API updates are saved

---

### Phase 5: Map Integration (Week 5)

#### Step 5.1: Install Leaflet.js
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

#### Step 5.2: Implement Map
Create `webapp/static/js/travel/map.js` with code from [05_MAP_INTEGRATION.md](./05_MAP_INTEGRATION.md)

#### Step 5.3: Add Geocoding
```python
# api/travel_api.py

@travel_bp.route('/geocode', methods=['POST'])
@login_required
def geocode_address():
    """Convert address to lat/lng using Nominatim"""
    address = request.json.get('address')
    
    try:
        import requests
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': address,
                'format': 'json',
                'limit': 1
            },
            headers={'User-Agent': 'TravelPlannerApp/1.0'}
        )
        
        data = response.json()
        if data:
            return jsonify({
                'success': True,
                'latitude': float(data[0]['lat']),
                'longitude': float(data[0]['lon'])
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### Phase 6: Weather Integration (Week 5)

#### Step 6.1: Connect to Existing Weather API
```python
# api/travel_api.py

@travel_bp.route('/trips/<int:trip_id>/weather', methods=['GET'])
@login_required
def get_trip_weather(trip_id):
    """Get weather forecast for trip locations"""
    try:
        # Get trip details
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get unique locations from activities and accommodations
                cur.execute("""
                    SELECT DISTINCT city, country, latitude, longitude
                    FROM (
                        SELECT city, country, latitude, longitude FROM activities WHERE trip_id = %s
                        UNION
                        SELECT city, country, latitude, longitude FROM accommodations WHERE trip_id = %s
                    ) locations
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """, (trip_id, trip_id))
                
                locations = cur.fetchall()
        
        # Fetch weather for each location (use existing weather API)
        forecasts = []
        for loc in locations:
            # Call your existing weather endpoint
            weather_response = requests.get(
                f'http://api:8000/weather/forecast',
                params={'lat': loc['latitude'], 'lon': loc['longitude']}
            )
            forecasts.append(weather_response.json())
        
        return jsonify({
            'success': True,
            'forecasts': forecasts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### Phase 7: Testing & Polish (Week 6)

#### Step 7.1: Unit Tests
```python
# tests/test_travel_api.py

import pytest
from api.travel_api import travel_bp

def test_create_trip(client, auth):
    """Test trip creation"""
    auth.login()
    
    response = client.post('/api/travel/trips', json={
        'name': 'Test Trip',
        'start_date': '2025-12-01',
        'end_date': '2025-12-10',
        'destination_city': 'Paris',
        'total_budget': 1500
    })
    
    assert response.status_code == 201
    assert response.json['success'] is True
    assert 'trip' in response.json

def test_list_trips(client, auth):
    """Test trip listing"""
    auth.login()
    
    response = client.get('/api/travel/trips')
    
    assert response.status_code == 200
    assert 'trips' in response.json
```

#### Step 7.2: Integration Tests
- Create trip → verify in database
- Add activities → verify Gantt chart updates
- Drag activity → verify API saves new time
- Add accommodation → verify map marker appears

#### Step 7.3: Performance Testing
```sql
-- Test query performance
EXPLAIN ANALYZE
SELECT * FROM trips t
LEFT JOIN activities a ON t.id = a.trip_id
WHERE t.user_id = 1;

-- Should use indexes, < 50ms execution time
```

#### Step 7.4: Browser Testing
- Chrome, Firefox, Safari
- Mobile (iOS Safari, Chrome Mobile)
- Responsive breakpoints (320px, 768px, 1024px, 1440px)

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Database migration tested on staging
- [ ] Frontend responsive on all devices
- [ ] API endpoints documented
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Toast notifications working

### Deployment Steps

1. **Backup Database**
   ```bash
   docker exec docker-project-database pg_dump -U root webapp_db > backup_pre_travel_$(date +%Y%m%d).sql
   ```

2. **Run Migration**
   ```bash
   docker exec -i docker-project-database psql -U root webapp_db < database/add_travel_planner_tables.sql
   ```

3. **Restart Services**
   ```bash
   docker compose restart webapp api
   ```

4. **Verify Deployment**
   - Visit https://localhost/travel
   - Create test trip
   - Add activities
   - Check Gantt chart
   - Check map
   - Check weather

5. **Monitor Logs**
   ```bash
   docker compose logs -f webapp api
   ```

### Post-Deployment
- [ ] Smoke test all features
- [ ] Check error logs
- [ ] Monitor performance metrics
- [ ] Gather user feedback

---

## 🔄 Rollback Plan

If issues occur:

1. **Stop Services**
   ```bash
   docker compose stop webapp api
   ```

2. **Restore Database**
   ```bash
   docker exec -i docker-project-database psql -U root webapp_db < backup_pre_travel_YYYYMMDD.sql
   ```

3. **Remove Route**
   ```python
   # Comment out in webapp/app.py
   # @app.route('/travel')
   ```

4. **Restart Services**
   ```bash
   docker compose up -d webapp api
   ```

---

## 📊 Success Metrics

### Week 1-2 (Backend)
- ✅ All database tables created
- ✅ All API endpoints functional
- ✅ Unit tests passing (>80% coverage)

### Week 3-4 (Frontend)
- ✅ All templates rendering
- ✅ Forms submitting correctly
- ✅ Gantt chart displaying activities

### Week 5 (Integration)
- ✅ Map showing markers
- ✅ Weather data loading
- ✅ Drag-and-drop working

### Week 6 (Polish)
- ✅ Mobile responsive
- ✅ No console errors
- ✅ Page load < 2 seconds
- ✅ 100% feature complete

---

## 🐛 Known Issues & Limitations

### MVP Limitations
- No collaborative features (Phase 2)
- No offline mode (Phase 3)
- No mobile app (Phase 3)
- No route optimization (Phase 2)
- No AI suggestions (Phase 3)

### Technical Debt
- No caching for map tiles (future optimization)
- No lazy loading for large trips (future optimization)
- No real-time collaboration (Phase 2 feature)

---

## 📝 Documentation Updates

After deployment, update:
- [ ] Main README.md (add travel planner section)
- [ ] API documentation
- [ ] User guide
- [ ] Admin guide
- [ ] System architecture diagram

---

## 🎯 Next Steps (Phase 2)

After MVP is stable:
1. Route optimization algorithm
2. Collaborative trip sharing
3. Document upload functionality
4. Packing list auto-generation
5. Budget analytics dashboard

---

*Implementation Ready! Follow this plan step-by-step for successful deployment.*
