"""
Travel Planner API Blueprint
Provides REST endpoints for trip planning, accommodations, activities, routes, expenses, etc.
Created: 2025-10-25
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
import os
from decimal import Decimal

# Create blueprint
travel_bp = Blueprint('travel', __name__, url_prefix='/api/travel')


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_db_connection():
    """Get database connection"""
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'database'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'webapp_db'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'rootpassword')
    )


# =============================================================================
# AUTHENTICATION DECORATOR
# =============================================================================

def get_user_from_request():
    """Extract user ID from request headers/cookies"""
    # Try to get from Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # TODO: Decode JWT token and get user_id
        # For now, return None (will implement with proper auth)
        return None
    
    # Try to get from cookie (session-based)
    user_id = request.cookies.get('user_id')
    if user_id:
        return user_id
    
    return None


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_user_from_request()
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Store user_id in request context
        request.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def serialize_row(row):
    """Convert database row to JSON-serializable dict"""
    if row is None:
        return None
    
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif hasattr(value, 'isoformat'):  # date, time objects
            result[key] = value.isoformat()
    
    return result


def serialize_rows(rows):
    """Convert list of database rows to JSON-serializable list"""
    return [serialize_row(row) for row in rows]


# =============================================================================
# TRIP ENDPOINTS
# =============================================================================

@travel_bp.route('/trips', methods=['GET'])
@login_required
def get_trips():
    """Get all trips for the current user"""
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                query = """
                    SELECT t.*,
                           COUNT(DISTINCT a.id) as activity_count,
                           COUNT(DISTINCT ac.id) as accommodation_count,
                           COALESCE(SUM(e.amount), 0) as total_spent
                    FROM trips t
                    LEFT JOIN activities a ON t.id = a.trip_id
                    LEFT JOIN accommodations ac ON t.id = ac.trip_id
                    LEFT JOIN expenses e ON t.id = e.trip_id
                    WHERE t.user_id = %s
                """
                params = [request.user_id]
                
                if status:
                    query += " AND t.status = %s"
                    params.append(status)
                
                query += """
                    GROUP BY t.id
                    ORDER BY t.start_date DESC
                    LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])
                
                cur.execute(query, params)
                trips = cur.fetchall()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM trips WHERE user_id = %s"
                count_params = [request.user_id]
                if status:
                    count_query += " AND status = %s"
                    count_params.append(status)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
        
        return jsonify({
            'success': True,
            'trips': serialize_rows(trips),
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>', methods=['GET'])
@login_required
def get_trip(trip_id):
    """Get single trip details"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT t.*,
                           COUNT(DISTINCT a.id) as activity_count,
                           COUNT(DISTINCT ac.id) as accommodation_count,
                           COUNT(DISTINCT r.id) as route_count,
                           COALESCE(SUM(e.amount), 0) as total_spent
                    FROM trips t
                    LEFT JOIN activities a ON t.id = a.trip_id
                    LEFT JOIN accommodations ac ON t.id = ac.trip_id
                    LEFT JOIN routes r ON t.id = r.trip_id
                    LEFT JOIN expenses e ON t.id = e.trip_id
                    WHERE t.id = %s AND t.user_id = %s
                    GROUP BY t.id
                """, (trip_id, request.user_id))
                
                trip = cur.fetchone()
                
                if not trip:
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
        
        return jsonify({
            'success': True,
            'trip': serialize_row(trip)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips', methods=['POST'])
@login_required
def create_trip():
    """Create a new trip"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'start_date', 'end_date']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    INSERT INTO trips (
                        user_id, name, description, start_date, end_date, status,
                        budget_total, budget_currency, destination_country, 
                        destination_city, timezone
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    request.user_id,
                    data['name'],
                    data.get('description'),
                    data['start_date'],
                    data['end_date'],
                    data.get('status', 'planning'),
                    data.get('budget_total'),
                    data.get('budget_currency', 'EUR'),
                    data.get('destination_country'),
                    data.get('destination_city'),
                    data.get('timezone', 'UTC')
                ))
                
                trip = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'trip': serialize_row(trip)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>', methods=['PUT'])
@login_required
def update_trip(trip_id):
    """Update a trip"""
    try:
        data = request.get_json()
        
        # Build dynamic update query
        allowed_fields = [
            'name', 'description', 'start_date', 'end_date', 'status',
            'budget_total', 'budget_currency', 'destination_country',
            'destination_city', 'timezone'
        ]
        
        update_fields = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        values.extend([trip_id, request.user_id])
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                query = f"""
                    UPDATE trips 
                    SET {', '.join(update_fields)}
                    WHERE id = %s AND user_id = %s
                    RETURNING *
                """
                
                cur.execute(query, values)
                trip = cur.fetchone()
                
                if not trip:
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'trip': serialize_row(trip)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_trip(trip_id):
    """Delete a trip (cascades to all related data)"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    DELETE FROM trips 
                    WHERE id = %s AND user_id = %s
                    RETURNING id
                """, (trip_id, request.user_id))
                
                deleted = cur.fetchone()
                
                if not deleted:
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ACCOMMODATION ENDPOINTS
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/accommodations', methods=['GET'])
@login_required
def get_accommodations(trip_id):
    """Get all accommodations for a trip"""
    try:
        # Verify trip ownership
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get accommodations
                cur.execute("""
                    SELECT * FROM accommodations 
                    WHERE trip_id = %s 
                    ORDER BY check_in_date
                """, (trip_id,))
                
                accommodations = cur.fetchall()
        
        return jsonify({
            'success': True,
            'accommodations': serialize_rows(accommodations)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/accommodations', methods=['POST'])
@login_required
def create_accommodation(trip_id):
    """Create a new accommodation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'check_in_date', 'check_out_date']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Create accommodation
                cur.execute("""
                    INSERT INTO accommodations (
                        trip_id, name, type, address, city, country,
                        latitude, longitude, check_in_date, check_in_time,
                        check_out_date, check_out_time, booking_reference,
                        booking_url, cost_per_night, total_cost, currency, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    trip_id,
                    data['name'],
                    data.get('type', 'hotel'),
                    data.get('address'),
                    data.get('city'),
                    data.get('country'),
                    data.get('latitude'),
                    data.get('longitude'),
                    data['check_in_date'],
                    data.get('check_in_time', '15:00:00'),
                    data['check_out_date'],
                    data.get('check_out_time', '11:00:00'),
                    data.get('booking_reference'),
                    data.get('booking_url'),
                    data.get('cost_per_night'),
                    data.get('total_cost'),
                    data.get('currency', 'EUR'),
                    data.get('notes')
                ))
                
                accommodation = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'accommodation': serialize_row(accommodation)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/accommodations/<int:accommodation_id>', methods=['GET'])
@login_required
def get_accommodation(trip_id, accommodation_id):
    """Get a single accommodation"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get accommodation with ownership check
                cur.execute("""
                    SELECT a.* 
                    FROM accommodations a
                    JOIN trips t ON a.trip_id = t.id
                    WHERE a.id = %s AND a.trip_id = %s AND t.user_id = %s
                """, (accommodation_id, trip_id, request.user_id))
                
                accommodation = cur.fetchone()
                
                if not accommodation:
                    return jsonify({'success': False, 'error': 'Accommodation not found'}), 404
                
                return jsonify({
                    'success': True,
                    'accommodation': serialize_row(accommodation)
                })
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/accommodations/<int:accommodation_id>', methods=['PUT'])
@login_required
def update_accommodation(trip_id, accommodation_id):
    """Update an accommodation"""
    try:
        data = request.get_json()
        
        # Build dynamic update query
        allowed_fields = [
            'name', 'type', 'address', 'city', 'country', 'latitude', 'longitude',
            'check_in_date', 'check_in_time', 'check_out_date', 'check_out_time',
            'booking_reference', 'booking_url', 'cost_per_night', 'total_cost',
            'currency', 'notes'
        ]
        
        update_fields = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        values.append(accommodation_id)
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify ownership through trip
                query = f"""
                    UPDATE accommodations 
                    SET {', '.join(update_fields)}
                    WHERE id = %s 
                    AND trip_id IN (SELECT id FROM trips WHERE user_id = %s)
                    RETURNING *
                """
                values.append(request.user_id)
                
                cur.execute(query, values)
                accommodation = cur.fetchone()
                
                if not accommodation:
                    return jsonify({'success': False, 'error': 'Accommodation not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'accommodation': serialize_row(accommodation)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/accommodations/<int:accommodation_id>', methods=['DELETE'])
@login_required
def delete_accommodation(trip_id, accommodation_id):
    """Delete an accommodation"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    DELETE FROM accommodations 
                    WHERE id = %s 
                    AND trip_id = %s
                    AND trip_id IN (SELECT id FROM trips WHERE user_id = %s)
                    RETURNING id
                """, (accommodation_id, trip_id, request.user_id))
                
                deleted = cur.fetchone()
                
                if not deleted:
                    return jsonify({'success': False, 'error': 'Accommodation not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Accommodation deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ACTIVITY ENDPOINTS
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/activities', methods=['GET'])
@login_required
def get_activities(trip_id):
    """Get all activities for a trip"""
    try:
        category = request.args.get('category')
        priority = request.args.get('priority')
        status = request.args.get('status')
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Build query with filters
                query = "SELECT * FROM activities WHERE trip_id = %s"
                params = [trip_id]
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                if priority:
                    query += " AND priority = %s"
                    params.append(priority)
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY start_datetime, display_order"
                
                cur.execute(query, params)
                activities = cur.fetchall()
        
        return jsonify({
            'success': True,
            'activities': serialize_rows(activities)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/activities', methods=['POST'])
@login_required
def create_activity(trip_id):
    """Create a new activity"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'start_datetime']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Create activity
                cur.execute("""
                    INSERT INTO activities (
                        trip_id, name, description, category, start_datetime,
                        end_datetime, duration_minutes, location_name, address,
                        city, country, latitude, longitude, priority, status,
                        cost, currency, booking_reference, booking_url,
                        opening_hours, contact_info, notes, display_order
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                """, (
                    trip_id,
                    data['name'],
                    data.get('description'),
                    data.get('category', 'other'),
                    data['start_datetime'],
                    data.get('end_datetime'),
                    data.get('duration_minutes'),
                    data.get('location_name'),
                    data.get('address'),
                    data.get('city'),
                    data.get('country'),
                    data.get('latitude'),
                    data.get('longitude'),
                    data.get('priority', 'medium'),
                    data.get('status', 'planned'),
                    data.get('cost'),
                    data.get('currency', 'EUR'),
                    data.get('booking_reference'),
                    data.get('booking_url'),
                    data.get('opening_hours'),
                    data.get('contact_info'),
                    data.get('notes'),
                    data.get('display_order', 0)
                ))
                
                activity = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'activity': serialize_row(activity)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/activities/<int:activity_id>', methods=['GET'])
@login_required
def get_activity(trip_id, activity_id):
    """Get a single activity"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get activity with ownership check
                cur.execute("""
                    SELECT a.* 
                    FROM activities a
                    JOIN trips t ON a.trip_id = t.id
                    WHERE a.id = %s AND a.trip_id = %s AND t.user_id = %s
                """, (activity_id, trip_id, request.user_id))
                
                activity = cur.fetchone()
                
                if not activity:
                    return jsonify({'success': False, 'error': 'Activity not found'}), 404
                
                return jsonify({
                    'success': True,
                    'activity': serialize_row(activity)
                })
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/activities/<int:activity_id>', methods=['PUT'])
@login_required
def update_activity(trip_id, activity_id):
    """Update an activity"""
    try:
        data = request.get_json()
        
        # Build dynamic update query
        allowed_fields = [
            'name', 'description', 'category', 'start_datetime', 'end_datetime',
            'duration_minutes', 'location_name', 'address', 'city', 'country',
            'latitude', 'longitude', 'priority', 'status', 'cost', 'currency',
            'booking_reference', 'booking_url', 'opening_hours', 'contact_info',
            'notes', 'display_order'
        ]
        
        update_fields = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        values.append(activity_id)
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                query = f"""
                    UPDATE activities 
                    SET {', '.join(update_fields)}
                    WHERE id = %s 
                    AND trip_id IN (SELECT id FROM trips WHERE user_id = %s)
                    RETURNING *
                """
                values.append(request.user_id)
                
                cur.execute(query, values)
                activity = cur.fetchone()
                
                if not activity:
                    return jsonify({'success': False, 'error': 'Activity not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'activity': serialize_row(activity)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/activities/<int:activity_id>', methods=['DELETE'])
@login_required
def delete_activity(trip_id, activity_id):
    """Delete an activity"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    DELETE FROM activities 
                    WHERE id = %s 
                    AND trip_id = %s
                    AND trip_id IN (SELECT id FROM trips WHERE user_id = %s)
                    RETURNING id
                """, (activity_id, trip_id, request.user_id))
                
                deleted = cur.fetchone()
                
                if not deleted:
                    return jsonify({'success': False, 'error': 'Activity not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Activity deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/activities/reorder', methods=['POST'])
@login_required
def reorder_activities(trip_id):
    """Bulk reorder activities (for drag-drop in Gantt chart)"""
    try:
        data = request.get_json()
        activity_orders = data.get('activities', [])  # [{id: 1, display_order: 0}, ...]
        
        if not activity_orders:
            return jsonify({'success': False, 'error': 'No activities to reorder'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Update each activity
                for item in activity_orders:
                    cur.execute("""
                        UPDATE activities 
                        SET display_order = %s
                        WHERE id = %s AND trip_id = %s
                    """, (item['display_order'], item['id'], trip_id))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Reordered {len(activity_orders)} activities'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ROUTE ENDPOINTS
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/routes', methods=['GET'])
@login_required
def get_routes(trip_id):
    """Get all routes for a trip"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get routes
                cur.execute("""
                    SELECT * FROM routes 
                    WHERE trip_id = %s 
                    ORDER BY departure_datetime NULLS LAST
                """, (trip_id,))
                
                routes = cur.fetchall()
        
        return jsonify({
            'success': True,
            'routes': serialize_rows(routes)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/routes/calculate', methods=['POST'])
@login_required
def calculate_route():
    """Calculate route distance and duration (using external API or estimation)"""
    try:
        data = request.get_json()
        
        from_lat = data.get('from_latitude')
        from_lng = data.get('from_longitude')
        to_lat = data.get('to_latitude')
        to_lng = data.get('to_longitude')
        mode = data.get('transport_mode', 'car')
        
        if not all([from_lat, from_lng, to_lat, to_lng]):
            return jsonify({'success': False, 'error': 'Missing coordinates'}), 400
        
        # Simple haversine distance calculation
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        
        lat1, lon1 = radians(float(from_lat)), radians(float(from_lng))
        lat2, lon2 = radians(float(to_lat)), radians(float(to_lng))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance_km = R * c
        
        # Estimate duration based on mode
        speed_map = {
            'walking': 5,
            'cycling': 20,
            'car': 80,
            'bus': 60,
            'train': 100,
            'flight': 800
        }
        
        speed = speed_map.get(mode, 60)
        duration_minutes = int((distance_km / speed) * 60)
        
        return jsonify({
            'success': True,
            'distance_km': round(distance_km, 2),
            'duration_minutes': duration_minutes,
            'estimated_speed_kmh': speed
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/routes', methods=['POST'])
@login_required
def create_route(trip_id):
    """Create a new route"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['from_location', 'to_location']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Create route
                cur.execute("""
                    INSERT INTO routes (
                        trip_id, from_location, to_location, from_latitude, from_longitude,
                        to_latitude, to_longitude, transport_mode, departure_datetime,
                        arrival_datetime, duration_minutes, distance_km, cost, currency,
                        booking_reference, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    trip_id,
                    data['from_location'],
                    data['to_location'],
                    data.get('from_latitude'),
                    data.get('from_longitude'),
                    data.get('to_latitude'),
                    data.get('to_longitude'),
                    data.get('transport_mode', 'car'),
                    data.get('departure_datetime'),
                    data.get('arrival_datetime'),
                    data.get('duration_minutes'),
                    data.get('distance_km'),
                    data.get('cost'),
                    data.get('currency', 'EUR'),
                    data.get('booking_reference'),
                    data.get('notes')
                ))
                
                route = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'route': serialize_row(route)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# EXPENSE ENDPOINTS
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/expenses', methods=['GET'])
@login_required
def get_expenses(trip_id):
    """Get all expenses for a trip"""
    try:
        category = request.args.get('category')
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Build query
                query = "SELECT * FROM expenses WHERE trip_id = %s"
                params = [trip_id]
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                query += " ORDER BY expense_date DESC"
                
                cur.execute(query, params)
                expenses = cur.fetchall()
                
                # Calculate summary
                cur.execute("""
                    SELECT 
                        category,
                        COUNT(*) as count,
                        SUM(amount) as total
                    FROM expenses
                    WHERE trip_id = %s
                    GROUP BY category
                """, (trip_id,))
                
                summary = cur.fetchall()
        
        return jsonify({
            'success': True,
            'expenses': serialize_rows(expenses),
            'summary': serialize_rows(summary)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/expenses', methods=['POST'])
@login_required
def create_expense(trip_id):
    """Create a new expense"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['description', 'amount', 'expense_date']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Create expense
                cur.execute("""
                    INSERT INTO expenses (
                        trip_id, activity_id, accommodation_id, route_id,
                        category, description, amount, currency, expense_date,
                        payment_method, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    trip_id,
                    data.get('activity_id'),
                    data.get('accommodation_id'),
                    data.get('route_id'),
                    data.get('category', 'other'),
                    data['description'],
                    data['amount'],
                    data.get('currency', 'EUR'),
                    data['expense_date'],
                    data.get('payment_method'),
                    data.get('notes')
                ))
                
                expense = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'expense': serialize_row(expense)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    """Update an expense"""
    try:
        data = request.get_json()
        
        allowed_fields = [
            'activity_id', 'accommodation_id', 'route_id', 'category',
            'description', 'amount', 'currency', 'expense_date',
            'payment_method', 'notes'
        ]
        
        update_fields = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        values.append(expense_id)
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                query = f"""
                    UPDATE expenses 
                    SET {', '.join(update_fields)}
                    WHERE id = %s 
                    AND trip_id IN (SELECT id FROM trips WHERE user_id = %s)
                    RETURNING *
                """
                values.append(request.user_id)
                
                cur.execute(query, values)
                expense = cur.fetchone()
                
                if not expense:
                    return jsonify({'success': False, 'error': 'Expense not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'expense': serialize_row(expense)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    DELETE FROM expenses 
                    WHERE id = %s 
                    AND trip_id IN (SELECT id FROM trips WHERE user_id = %s)
                    RETURNING id
                """, (expense_id, request.user_id))
                
                deleted = cur.fetchone()
                
                if not deleted:
                    return jsonify({'success': False, 'error': 'Expense not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Expense deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# DOCUMENT ENDPOINTS
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/documents', methods=['GET'])
@login_required
def get_documents(trip_id):
    """Get all documents for a trip"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get documents
                cur.execute("""
                    SELECT * FROM trip_documents 
                    WHERE trip_id = %s 
                    ORDER BY created_at DESC
                """, (trip_id,))
                
                documents = cur.fetchall()
        
        return jsonify({
            'success': True,
            'documents': serialize_rows(documents)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/documents', methods=['POST'])
@login_required
def create_document(trip_id):
    """Add a document reference (file upload handled separately)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'name' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: name'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Create document reference
                cur.execute("""
                    INSERT INTO trip_documents (
                        trip_id, name, document_type, file_path, file_url,
                        description, expiry_date, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    trip_id,
                    data['name'],
                    data.get('document_type', 'other'),
                    data.get('file_path'),
                    data.get('file_url'),
                    data.get('description'),
                    data.get('expiry_date'),
                    data.get('notes')
                ))
                
                document = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'document': serialize_row(document)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# PACKING LIST ENDPOINTS
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/packing', methods=['GET'])
@login_required
def get_packing_list(trip_id):
    """Get packing list for a trip"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get packing list with category grouping
                cur.execute("""
                    SELECT 
                        category,
                        COUNT(*) as total_items,
                        SUM(CASE WHEN is_packed THEN 1 ELSE 0 END) as packed_items
                    FROM packing_lists
                    WHERE trip_id = %s
                    GROUP BY category
                """, (trip_id,))
                
                summary = cur.fetchall()
                
                # Get all items
                cur.execute("""
                    SELECT * FROM packing_lists 
                    WHERE trip_id = %s 
                    ORDER BY category, is_packed, item_name
                """, (trip_id,))
                
                items = cur.fetchall()
        
        return jsonify({
            'success': True,
            'items': serialize_rows(items),
            'summary': serialize_rows(summary)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/packing', methods=['POST'])
@login_required
def add_packing_item(trip_id):
    """Add an item to packing list"""
    try:
        data = request.get_json()
        
        if 'item_name' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: item_name'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT id FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Add item
                cur.execute("""
                    INSERT INTO packing_lists (
                        trip_id, category, item_name, quantity, is_packed, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    trip_id,
                    data.get('category', 'general'),
                    data['item_name'],
                    data.get('quantity', 1),
                    data.get('is_packed', False),
                    data.get('notes')
                ))
                
                item = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'item': serialize_row(item)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/packing/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_packing_item(item_id):
    """Toggle packed status of an item"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    UPDATE packing_lists 
                    SET is_packed = NOT is_packed
                    WHERE id = %s 
                    AND trip_id IN (SELECT id FROM trips WHERE user_id = %s)
                    RETURNING *
                """, (item_id, request.user_id))
                
                item = cur.fetchone()
                
                if not item:
                    return jsonify({'success': False, 'error': 'Item not found'}), 404
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'item': serialize_row(item)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# WEATHER INTEGRATION ENDPOINT
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/weather', methods=['GET'])
@login_required
def get_trip_weather(trip_id):
    """Get weather forecast for trip destination"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get trip details
                cur.execute("""
                    SELECT * FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                trip = cur.fetchone()
                
                if not trip:
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get first accommodation to get coordinates
                cur.execute("""
                    SELECT latitude, longitude 
                    FROM accommodations 
                    WHERE trip_id = %s AND latitude IS NOT NULL AND longitude IS NOT NULL
                    ORDER BY check_in_date 
                    LIMIT 1
                """, (trip_id,))
                
                location = cur.fetchone()
                
                if not location:
                    # Try to get from activities
                    cur.execute("""
                        SELECT latitude, longitude 
                        FROM activities 
                        WHERE trip_id = %s AND latitude IS NOT NULL AND longitude IS NOT NULL
                        ORDER BY start_datetime 
                        LIMIT 1
                    """, (trip_id,))
                    
                    location = cur.fetchone()
        
        if not location:
            return jsonify({
                'success': False,
                'error': 'No location data available for weather forecast'
            }), 404
        
        # TODO: Call existing weather API endpoint
        # For now, return placeholder
        return jsonify({
            'success': True,
            'message': 'Weather integration - connect to existing weather API',
            'latitude': float(location['latitude']),
            'longitude': float(location['longitude']),
            'trip_dates': {
                'start': trip['start_date'].isoformat(),
                'end': trip['end_date'].isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@travel_bp.route('/trips/<int:trip_id>/summary', methods=['GET'])
@login_required
def get_trip_summary(trip_id):
    """Get comprehensive trip summary with statistics"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify ownership and get trip
                cur.execute("""
                    SELECT * FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                trip = cur.fetchone()
                
                if not trip:
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get counts
                cur.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM activities WHERE trip_id = %s) as activity_count,
                        (SELECT COUNT(*) FROM accommodations WHERE trip_id = %s) as accommodation_count,
                        (SELECT COUNT(*) FROM routes WHERE trip_id = %s) as route_count,
                        (SELECT COUNT(*) FROM expenses WHERE trip_id = %s) as expense_count,
                        (SELECT COUNT(*) FROM packing_lists WHERE trip_id = %s) as packing_items,
                        (SELECT COUNT(*) FROM packing_lists WHERE trip_id = %s AND is_packed = true) as packed_items
                """, (trip_id, trip_id, trip_id, trip_id, trip_id, trip_id))
                
                counts = cur.fetchone()
                
                # Get expense summary
                cur.execute("""
                    SELECT 
                        category,
                        SUM(amount) as total,
                        COUNT(*) as count
                    FROM expenses
                    WHERE trip_id = %s
                    GROUP BY category
                """, (trip_id,))
                
                expense_breakdown = cur.fetchall()
                
                # Get activity breakdown
                cur.execute("""
                    SELECT 
                        category,
                        COUNT(*) as count
                    FROM activities
                    WHERE trip_id = %s
                    GROUP BY category
                """, (trip_id,))
                
                activity_breakdown = cur.fetchall()
        
        return jsonify({
            'success': True,
            'trip': serialize_row(trip),
            'counts': serialize_row(counts),
            'expense_breakdown': serialize_rows(expense_breakdown),
            'activity_breakdown': serialize_rows(activity_breakdown)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@travel_bp.route('/trips/<int:trip_id>/daily-itinerary', methods=['GET'])
@login_required
def get_daily_itinerary(trip_id):
    """Get activities grouped by day"""
    try:
        date_param = request.args.get('date')  # Optional: get specific day
        
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify trip ownership
                cur.execute("""
                    SELECT * FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, request.user_id))
                
                trip = cur.fetchone()
                
                if not trip:
                    return jsonify({'success': False, 'error': 'Trip not found'}), 404
                
                # Get activities grouped by date
                if date_param:
                    cur.execute("""
                        SELECT * FROM activities 
                        WHERE trip_id = %s 
                        AND DATE(start_datetime) = %s
                        ORDER BY start_datetime
                    """, (trip_id, date_param))
                    
                    activities = cur.fetchall()
                    
                    return jsonify({
                        'success': True,
                        'date': date_param,
                        'activities': serialize_rows(activities)
                    })
                else:
                    # Group by all days
                    cur.execute("""
                        SELECT 
                            DATE(start_datetime) as day,
                            json_agg(
                                json_build_object(
                                    'id', id,
                                    'name', name,
                                    'start_datetime', start_datetime,
                                    'category', category,
                                    'priority', priority,
                                    'location_name', location_name
                                ) ORDER BY start_datetime
                            ) as activities
                        FROM activities
                        WHERE trip_id = %s
                        GROUP BY DATE(start_datetime)
                        ORDER BY DATE(start_datetime)
                    """, (trip_id,))
                    
                    daily_groups = cur.fetchall()
                    
                    return jsonify({
                        'success': True,
                        'trip': serialize_row(trip),
                        'daily_itinerary': serialize_rows(daily_groups)
                    })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# HEALTH CHECK
# =============================================================================

@travel_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT COUNT(*) FROM trips")
                count = cur.fetchone()['count']
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'total_trips': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@travel_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@travel_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
