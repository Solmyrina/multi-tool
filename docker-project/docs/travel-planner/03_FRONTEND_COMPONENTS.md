# Frontend Components - Travel Planner

**Purpose**: HTML templates and JavaScript components for travel planning UI  
**Framework**: Flask + Jinja2 + Bootstrap 5  
**JavaScript**: Vanilla JS + Gantt + Leaflet

---

## 📁 Template Structure

```
webapp/templates/
├── travel/
│   ├── trip_list.html          # List all trips
│   ├── trip_detail.html        # Single trip view with Gantt + Map
│   ├── trip_create.html        # Create new trip form
│   ├── trip_edit.html          # Edit trip form
│   ├── daily_view.html         # Day-by-day itinerary
│   ├── budget_tracker.html     # Expense management
│   ├── packing_list.html       # Packing checklist
│   └── components/
│       ├── gantt_chart.html    # Gantt chart component
│       ├── map_view.html       # Interactive map component
│       ├── activity_form.html  # Add/edit activity modal
│       ├── accommodation_form.html
│       └── weather_widget.html
```

---

## 🎨 Page Designs

### 1. Trip List Page (`trip_list.html`)

**URL**: `/travel` or `/travel/trips`  
**Purpose**: Dashboard showing all user's trips

#### Layout
```html
{% extends "base.html" %}

{% block title %}My Trips - Travel Planner{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1><i class="fas fa-suitcase-rolling"></i> My Trips</h1>
        <a href="{{ url_for('travel.create_trip') }}" class="btn btn-primary">
            <i class="fas fa-plus"></i> New Trip
        </a>
    </div>

    <!-- Filter Tabs -->
    <ul class="nav nav-tabs mb-3" id="tripTabs">
        <li class="nav-item">
            <a class="nav-link active" data-status="all">All Trips</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-status="planning">Planning</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-status="confirmed">Confirmed</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-status="completed">Completed</a>
        </li>
    </ul>

    <!-- Trip Cards Grid -->
    <div class="row" id="tripGrid">
        {% for trip in trips %}
        <div class="col-md-6 col-lg-4 mb-4 trip-card" data-status="{{ trip.status }}">
            <div class="card h-100 shadow-sm hover-shadow">
                <!-- Card Header with Status Badge -->
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">{{ trip.name }}</h5>
                    <span class="badge bg-{{ trip.status | status_color }}">
                        {{ trip.status | capitalize }}
                    </span>
                </div>
                
                <!-- Card Body -->
                <div class="card-body">
                    <p class="text-muted mb-2">
                        <i class="fas fa-map-marker-alt"></i>
                        {{ trip.destination_city }}, {{ trip.destination_country }}
                    </p>
                    <p class="mb-2">
                        <i class="fas fa-calendar"></i>
                        {{ trip.start_date | format_date }} - {{ trip.end_date | format_date }}
                        <small class="text-muted">({{ trip.total_days }} days)</small>
                    </p>
                    
                    <!-- Stats Row -->
                    <div class="row mt-3">
                        <div class="col-4 text-center">
                            <div class="stat-value">{{ trip.activity_count }}</div>
                            <div class="stat-label">Activities</div>
                        </div>
                        <div class="col-4 text-center">
                            <div class="stat-value">{{ trip.accommodation_count }}</div>
                            <div class="stat-label">Stays</div>
                        </div>
                        <div class="col-4 text-center">
                            <div class="stat-value">{{ trip.budget_spent_pct }}%</div>
                            <div class="stat-label">Budget</div>
                        </div>
                    </div>
                    
                    <!-- Budget Progress Bar -->
                    <div class="progress mt-3" style="height: 8px;">
                        <div class="progress-bar" 
                             role="progressbar" 
                             style="width: {{ trip.budget_spent_pct }}%"
                             aria-valuenow="{{ trip.budget_spent_pct }}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                        </div>
                    </div>
                    <small class="text-muted">
                        {{ trip.total_spent | currency }} / {{ trip.total_budget | currency }}
                    </small>
                </div>
                
                <!-- Card Footer -->
                <div class="card-footer bg-transparent">
                    <div class="btn-group w-100">
                        <a href="{{ url_for('travel.trip_detail', trip_id=trip.id) }}" 
                           class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye"></i> View
                        </a>
                        <a href="{{ url_for('travel.edit_trip', trip_id=trip.id) }}" 
                           class="btn btn-sm btn-outline-secondary">
                            <i class="fas fa-edit"></i> Edit
                        </a>
                        <button class="btn btn-sm btn-outline-danger" 
                                onclick="deleteTrip({{ trip.id }})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Empty State -->
    {% if trips|length == 0 %}
    <div class="text-center py-5">
        <i class="fas fa-suitcase-rolling fa-5x text-muted mb-3"></i>
        <h3>No trips yet</h3>
        <p class="text-muted">Start planning your next adventure!</p>
        <a href="{{ url_for('travel.create_trip') }}" class="btn btn-primary btn-lg">
            Create Your First Trip
        </a>
    </div>
    {% endif %}
</div>

<script src="{{ url_for('static', filename='js/travel/trip_list.js') }}"></script>
{% endblock %}
```

#### JavaScript (`static/js/travel/trip_list.js`)
```javascript
// Filter trips by status
document.querySelectorAll('#tripTabs .nav-link').forEach(tab => {
    tab.addEventListener('click', function(e) {
        e.preventDefault();
        const status = this.dataset.status;
        
        // Update active tab
        document.querySelectorAll('#tripTabs .nav-link').forEach(t => 
            t.classList.remove('active')
        );
        this.classList.add('active');
        
        // Filter cards
        document.querySelectorAll('.trip-card').forEach(card => {
            if (status === 'all' || card.dataset.status === status) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

// Delete trip
async function deleteTrip(tripId) {
    if (!confirm('Are you sure you want to delete this trip? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/travel/trips/${tripId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove card from DOM
            document.querySelector(`[data-trip-id="${tripId}"]`).remove();
            showToast('Trip deleted successfully', 'success');
        } else {
            showToast('Error deleting trip: ' + data.error, 'danger');
        }
    } catch (error) {
        showToast('Error deleting trip', 'danger');
        console.error(error);
    }
}
```

---

### 2. Trip Detail Page (`trip_detail.html`)

**URL**: `/travel/trips/<trip_id>`  
**Purpose**: Main trip view with Gantt chart, map, and weather

#### Layout Structure
```html
{% extends "base.html" %}

{% block title %}{{ trip.name }} - Travel Planner{% endblock %}

{% block extra_head %}
<!-- Frappe Gantt CSS -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.css">
<!-- Leaflet CSS -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.css">
<style>
    #ganttChart { height: 400px; overflow-x: auto; }
    #mapView { height: 500px; }
    .sticky-header { position: sticky; top: 0; z-index: 100; background: white; }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Trip Header -->
    <div class="sticky-header border-bottom pb-3 mb-3">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <h1>{{ trip.name }}</h1>
                <p class="text-muted mb-0">
                    <i class="fas fa-map-marker-alt"></i>
                    {{ trip.destination_city }}, {{ trip.destination_country }}
                    &nbsp;|&nbsp;
                    <i class="fas fa-calendar"></i>
                    {{ trip.start_date | format_date }} - {{ trip.end_date | format_date }}
                    ({{ trip.total_days }} days)
                </p>
            </div>
            <div class="btn-group">
                <button class="btn btn-outline-primary" onclick="showDailyView()">
                    <i class="fas fa-calendar-day"></i> Daily View
                </button>
                <button class="btn btn-outline-secondary" onclick="showBudget()">
                    <i class="fas fa-dollar-sign"></i> Budget
                </button>
                <button class="btn btn-outline-info" onclick="showPacking()">
                    <i class="fas fa-suitcase"></i> Packing
                </button>
                <a href="{{ url_for('travel.edit_trip', trip_id=trip.id) }}" 
                   class="btn btn-outline-secondary">
                    <i class="fas fa-cog"></i> Settings
                </a>
            </div>
        </div>
        
        <!-- Budget Summary Bar -->
        <div class="row mt-3">
            <div class="col-md-3">
                <small class="text-muted">Total Budget</small>
                <div class="h5">{{ trip.total_budget | currency(trip.budget_currency) }}</div>
            </div>
            <div class="col-md-3">
                <small class="text-muted">Spent</small>
                <div class="h5 text-danger">{{ trip.total_spent | currency(trip.budget_currency) }}</div>
            </div>
            <div class="col-md-3">
                <small class="text-muted">Remaining</small>
                <div class="h5 text-success">{{ trip.budget_remaining | currency(trip.budget_currency) }}</div>
            </div>
            <div class="col-md-3">
                <small class="text-muted">Activities</small>
                <div class="h5">{{ trip.activity_count }}</div>
            </div>
        </div>
    </div>

    <!-- Tab Navigation -->
    <ul class="nav nav-tabs mb-3" id="mainTabs">
        <li class="nav-item">
            <a class="nav-link active" data-bs-toggle="tab" href="#timelineTab">
                <i class="fas fa-chart-gantt"></i> Timeline
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-bs-toggle="tab" href="#mapTab">
                <i class="fas fa-map"></i> Map
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-bs-toggle="tab" href="#activitiesTab">
                <i class="fas fa-list"></i> Activities
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-bs-toggle="tab" href="#weatherTab">
                <i class="fas fa-cloud-sun"></i> Weather
            </a>
        </li>
    </ul>

    <!-- Tab Content -->
    <div class="tab-content">
        <!-- Timeline Tab -->
        <div class="tab-pane fade show active" id="timelineTab">
            {% include 'travel/components/gantt_chart.html' %}
        </div>

        <!-- Map Tab -->
        <div class="tab-pane fade" id="mapTab">
            {% include 'travel/components/map_view.html' %}
        </div>

        <!-- Activities Tab -->
        <div class="tab-pane fade" id="activitiesTab">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4>Activities & Accommodations</h4>
                <div class="btn-group">
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addActivityModal">
                        <i class="fas fa-plus"></i> Add Activity
                    </button>
                    <button class="btn btn-success" data-bs-toggle="modal" data-bs-target="#addAccommodationModal">
                        <i class="fas fa-hotel"></i> Add Accommodation
                    </button>
                </div>
            </div>
            
            <!-- Activity List (grouped by day) -->
            <div id="activityList">
                {% for day in trip.days %}
                <div class="card mb-3">
                    <div class="card-header bg-light">
                        <strong>{{ day.date | format_date }}</strong>
                        <span class="badge bg-primary float-end">
                            {{ day.activities|length }} activities
                        </span>
                    </div>
                    <div class="card-body">
                        {% for activity in day.activities %}
                        <div class="activity-item d-flex justify-content-between align-items-center mb-2 p-2 border-start border-4 border-{{ activity.category | category_color }}">
                            <div>
                                <strong>{{ activity.start_datetime | format_time }}</strong>
                                <span class="ms-2">{{ activity.name }}</span>
                                <small class="text-muted ms-2">
                                    <i class="fas fa-map-marker-alt"></i> {{ activity.location_name }}
                                </small>
                            </div>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-primary" onclick="editActivity({{ activity.id }})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="deleteActivity({{ activity.id }})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Weather Tab -->
        <div class="tab-pane fade" id="weatherTab">
            {% include 'travel/components/weather_widget.html' %}
        </div>
    </div>
</div>

<!-- Modals -->
{% include 'travel/components/activity_form.html' %}
{% include 'travel/components/accommodation_form.html' %}

<script src="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.js"></script>
<script src="{{ url_for('static', filename='js/travel/trip_detail.js') }}"></script>
{% endblock %}
```

---

### 3. Gantt Chart Component (`components/gantt_chart.html`)

```html
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Trip Timeline</h5>
        <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary" data-view="day">Day</button>
            <button class="btn btn-outline-secondary active" data-view="week">Week</button>
            <button class="btn btn-outline-secondary" data-view="month">Month</button>
        </div>
    </div>
    <div class="card-body">
        <div id="ganttChart"></div>
    </div>
</div>
```

#### Gantt Chart JavaScript
```javascript
// In static/js/travel/trip_detail.js

let gantt;

function initGanttChart(tripData) {
    // Transform data for Frappe Gantt
    const tasks = [];
    
    // Add accommodations
    tripData.accommodations.forEach(acc => {
        tasks.push({
            id: `acc-${acc.id}`,
            name: `🏨 ${acc.name}`,
            start: acc.check_in_date,
            end: acc.check_out_date,
            progress: 100,
            custom_class: 'accommodation',
            type: 'accommodation'
        });
    });
    
    // Add activities
    tripData.activities.forEach(act => {
        tasks.push({
            id: `act-${act.id}`,
            name: `${getCategoryIcon(act.category)} ${act.name}`,
            start: act.start_datetime,
            end: act.end_datetime || calculateEndTime(act.start_datetime, act.duration_minutes),
            progress: act.is_completed ? 100 : 0,
            custom_class: act.category,
            type: 'activity'
        });
    });
    
    // Initialize Gantt
    gantt = new Gantt("#ganttChart", tasks, {
        view_mode: 'Week',
        bar_height: 30,
        bar_corner_radius: 3,
        arrow_curve: 5,
        padding: 18,
        view_modes: ['Day', 'Week', 'Month'],
        date_format: 'YYYY-MM-DD',
        custom_popup_html: function(task) {
            return `
                <div class="gantt-popup">
                    <h5>${task.name}</h5>
                    <p>${task.start} - ${task.end}</p>
                    <button onclick="editTask('${task.id}')">Edit</button>
                </div>
            `;
        },
        on_click: function (task) {
            console.log('Clicked:', task);
        },
        on_date_change: function(task, start, end) {
            // Handle drag-and-drop
            updateTaskTime(task.id, start, end);
        }
    });
}

// Update task time via API
async function updateTaskTime(taskId, start, end) {
    const [type, id] = taskId.split('-');
    const endpoint = type === 'acc' ? 'accommodations' : 'activities';
    
    try {
        const response = await fetch(`/api/travel/${endpoint}/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_datetime: start,
                end_datetime: end
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('Updated successfully', 'success');
        }
    } catch (error) {
        console.error('Error updating task:', error);
        showToast('Error updating task', 'danger');
    }
}

// View mode buttons
document.querySelectorAll('[data-view]').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('[data-view]').forEach(b => 
            b.classList.remove('active')
        );
        this.classList.add('active');
        gantt.change_view_mode(this.dataset.view.charAt(0).toUpperCase() + this.dataset.view.slice(1));
    });
});
```

---

### 4. Map Component (`components/map_view.html`)

```html
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Trip Map</h5>
        <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" id="showRoutes" checked>
            <label class="form-check-label" for="showRoutes">Show Routes</label>
        </div>
    </div>
    <div class="card-body p-0">
        <div id="mapView"></div>
    </div>
</div>
```

#### Map JavaScript
```javascript
let map, markers = [], routes = [];

function initMap(tripData) {
    // Initialize Leaflet map
    map = L.map('mapView').setView([
        tripData.center_lat || 41.8902,
        tripData.center_lng || 12.4922
    ], 12);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add accommodation markers
    tripData.accommodations.forEach(acc => {
        const marker = L.marker([acc.latitude, acc.longitude], {
            icon: L.divIcon({
                html: '<i class="fas fa-hotel fa-2x text-success"></i>',
                className: 'map-icon',
                iconSize: [30, 30]
            })
        }).addTo(map);
        
        marker.bindPopup(`
            <strong>${acc.name}</strong><br>
            ${acc.city}<br>
            ${acc.check_in_date} - ${acc.check_out_date}
        `);
        
        markers.push(marker);
    });
    
    // Add activity markers
    tripData.activities.forEach(act => {
        const marker = L.marker([act.latitude, act.longitude], {
            icon: L.divIcon({
                html: `<i class="fas ${getCategoryIcon(act.category)} fa-2x text-primary"></i>`,
                className: 'map-icon',
                iconSize: [30, 30]
            })
        }).addTo(map);
        
        marker.bindPopup(`
            <strong>${act.name}</strong><br>
            ${act.location_name}<br>
            ${act.start_datetime}
        `);
        
        markers.push(marker);
    });
    
    // Fit bounds to show all markers
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
    
    // Add routes if enabled
    if (document.getElementById('showRoutes').checked) {
        drawRoutes(tripData.routes);
    }
}

function drawRoutes(routeData) {
    routeData.forEach(route => {
        const line = L.polyline([
            [route.from_lat, route.from_lng],
            [route.to_lat, route.to_lng]
        ], {
            color: getTransportColor(route.transport_mode),
            weight: 3,
            opacity: 0.7,
            dashArray: route.transport_mode === 'flight' ? '5, 10' : null
        }).addTo(map);
        
        // Add arrow decorator
        const decorator = L.polylineDecorator(line, {
            patterns: [{
                offset: '50%',
                repeat: 0,
                symbol: L.Symbol.arrowHead({
                    pixelSize: 10,
                    polygon: false,
                    pathOptions: { stroke: true }
                })
            }]
        }).addTo(map);
        
        routes.push(line, decorator);
    });
}

// Toggle routes
document.getElementById('showRoutes').addEventListener('change', function(e) {
    if (e.target.checked) {
        // Fetch and draw routes
        fetch(`/api/travel/trips/${tripId}/routes`)
            .then(r => r.json())
            .then(data => drawRoutes(data.routes));
    } else {
        // Remove routes
        routes.forEach(r => map.removeLayer(r));
        routes = [];
    }
});
```

---

### 5. Weather Widget (`components/weather_widget.html`)

```html
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">Weather Forecast</h5>
    </div>
    <div class="card-body">
        <div class="row" id="weatherForecast">
            <!-- Populated via JavaScript -->
        </div>
    </div>
</div>

<script>
async function loadWeather() {
    try {
        const response = await fetch(`/api/travel/trips/{{ trip.id }}/weather`);
        const data = await response.json();
        
        const forecastHTML = data.forecasts.map(day => `
            <div class="col-md-3 text-center mb-3">
                <div class="card">
                    <div class="card-body">
                        <h6>${new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</h6>
                        <i class="fas ${getWeatherIcon(day.condition)} fa-3x my-2"></i>
                        <p class="mb-0">
                            <span class="h4">${day.temperature_high}°</span>
                            <span class="text-muted"> / ${day.temperature_low}°</span>
                        </p>
                        <small class="text-muted">${day.condition}</small>
                        <p class="mb-0 mt-2">
                            <i class="fas fa-tint text-info"></i> ${day.precipitation_chance}%
                        </p>
                    </div>
                </div>
            </div>
        `).join('');
        
        document.getElementById('weatherForecast').innerHTML = forecastHTML;
    } catch (error) {
        console.error('Error loading weather:', error);
    }
}

// Load weather on tab show
document.querySelector('a[href="#weatherTab"]').addEventListener('shown.bs.tab', loadWeather);
</script>
```

---

## 📱 Responsive Design

### Mobile Breakpoints
```css
/* Mobile First */
@media (max-width: 768px) {
    #ganttChart {
        overflow-x: scroll;
        -webkit-overflow-scrolling: touch;
    }
    
    .sticky-header {
        position: relative;
    }
    
    .btn-group {
        flex-direction: column;
    }
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) {
    .trip-card {
        flex: 0 0 50%;
    }
}

/* Desktop */
@media (min-width: 1025px) {
    .trip-card {
        flex: 0 0 33.33%;
    }
}
```

---

## 🎨 Custom CSS (`static/css/travel.css`)

```css
/* Trip Cards */
.trip-card {
    transition: transform 0.2s;
}

.trip-card:hover {
    transform: translateY(-5px);
}

.hover-shadow {
    transition: box-shadow 0.2s;
}

.hover-shadow:hover {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}

/* Gantt Chart Styling */
.gantt .bar-wrapper .bar {
    border-radius: 3px;
}

.gantt .bar.accommodation {
    fill: #28a745;
}

.gantt .bar.sightseeing {
    fill: #007bff;
}

.gantt .bar.dining {
    fill: #fd7e14;
}

.gantt .bar.transport {
    fill: #6c757d;
}

/* Map Icons */
.map-icon {
    background: transparent;
    border: none;
    text-align: center;
}

/* Activity List */
.activity-item {
    transition: background-color 0.2s;
}

.activity-item:hover {
    background-color: #f8f9fa;
}

.border-sightseeing { border-color: #007bff !important; }
.border-dining { border-color: #fd7e14 !important; }
.border-transport { border-color: #6c757d !important; }
.border-shopping { border-color: #e83e8c !important; }

/* Loading States */
.loading-spinner {
    display: inline-block;
    width: 2rem;
    height: 2rem;
    border: 0.25rem solid #f3f3f3;
    border-top: 0.25rem solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

---

## 🔧 Utility Functions (`static/js/travel/utils.js`)

```javascript
// Category icons
function getCategoryIcon(category) {
    const icons = {
        'sightseeing': 'fa-landmark',
        'dining': 'fa-utensils',
        'transport': 'fa-car',
        'entertainment': 'fa-ticket',
        'shopping': 'fa-shopping-bag',
        'accommodation': 'fa-hotel'
    };
    return icons[category] || 'fa-circle';
}

// Weather icons
function getWeatherIcon(condition) {
    const icons = {
        'sunny': 'fa-sun',
        'cloudy': 'fa-cloud',
        'rainy': 'fa-cloud-rain',
        'snowy': 'fa-snowflake',
        'partly_cloudy': 'fa-cloud-sun'
    };
    return icons[condition] || 'fa-cloud';
}

// Transport colors
function getTransportColor(mode) {
    const colors = {
        'walking': '#28a745',
        'driving': '#007bff',
        'public_transit': '#ffc107',
        'flight': '#dc3545',
        'train': '#6610f2',
        'ferry': '#17a2b8'
    };
    return colors[mode] || '#6c757d';
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 5000);
}

// Format currency
function formatCurrency(amount, currency = 'EUR') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Calculate end time from duration
function calculateEndTime(startTime, durationMinutes) {
    const start = new Date(startTime);
    start.setMinutes(start.getMinutes() + durationMinutes);
    return start.toISOString();
}
```

---

*Next: [Gantt Chart Implementation](./04_GANTT_CHART_IMPLEMENTATION.md)*
