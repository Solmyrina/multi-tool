import os
import bcrypt
import uuid
import requests
import subprocess
import threading
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import docker
import psutil
import socket

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Trust proxy headers for HTTPS support
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'database'),
    'dbname': os.environ.get('DB_NAME', 'webapp_db'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '530NWC0Gm3pt4O'),
    'port': os.environ.get('DB_PORT', '5432')
}

# Activity Logging and Security Functions
def get_client_ip():
    """Get client IP address, handling proxy headers"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def log_user_activity(user_id=None, activity_type='page_view', description=None, request_data=None, response_status=200, duration_ms=None, additional_data=None):
    """Log user activity to the database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        
        # Get session ID if available
        session_id = session.get('session_token', None) if hasattr(session, 'get') else None
        
        # Prepare activity data
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
        request_method = request.method
        request_url = request.url
        
        # Sanitize request data (remove sensitive info)
        sanitized_request_data = None
        if request_data:
            sanitized_request_data = dict(request_data)
            # Remove sensitive fields
            sensitive_fields = ['password', 'token', 'session', 'csrf_token']
            for field in sensitive_fields:
                if field in sanitized_request_data:
                    sanitized_request_data[field] = '[REDACTED]'
        
        # Convert additional_data and request_data to JSON strings if needed
        additional_data_json = None
        if additional_data is not None:
            additional_data_json = json.dumps(additional_data) if isinstance(additional_data, dict) else additional_data
            
        sanitized_request_data_json = None
        if sanitized_request_data is not None:
            sanitized_request_data_json = json.dumps(sanitized_request_data) if isinstance(sanitized_request_data, dict) else sanitized_request_data
        
        cur.execute("""
            INSERT INTO user_activity_logs 
            (user_id, session_id, activity_type, activity_description, ip_address, user_agent, 
             request_method, request_url, request_data, response_status, duration_ms, additional_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, session_id, activity_type, description, ip_address, user_agent,
            request_method, request_url, sanitized_request_data_json, response_status, duration_ms, additional_data_json
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error logging user activity: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def log_security_event(user_id=None, event_type='suspicious_activity', severity='medium', description='', additional_data=None):
    """Log security events for monitoring"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')[:500]
        
        # Convert additional_data dict to JSON string if needed
        additional_data_json = None
        if additional_data is not None:
            additional_data_json = json.dumps(additional_data) if isinstance(additional_data, dict) else additional_data
        
        cur.execute("""
            INSERT INTO security_events 
            (user_id, event_type, severity, description, ip_address, user_agent, additional_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, event_type, severity, description, ip_address, user_agent, additional_data_json))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error logging security event: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def update_session_activity(session_token=None):
    """Update last activity timestamp for session management"""
    try:
        if not session_token:
            session_token = session.get('session_token')
        
        if not session_token:
            return False
            
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE user_sessions 
            SET last_activity = CURRENT_TIMESTAMP,
                ip_address = %s,
                user_agent = %s
            WHERE session_token = %s AND is_active = TRUE
        """, (get_client_ip(), request.headers.get('User-Agent', '')[:500], session_token))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating session activity: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

# Request timing and logging middleware
@app.before_request
def before_request():
    """Track request start time and update session activity"""
    request.start_time = datetime.now()
    
    # Update session activity for logged in users
    if current_user.is_authenticated:
        update_session_activity()

@app.after_request
def after_request(response):
    """Log activity after request completion"""
    try:
        # Calculate request duration
        duration_ms = None
        if hasattr(request, 'start_time'):
            duration = datetime.now() - request.start_time
            duration_ms = int(duration.total_seconds() * 1000)
        
        # Determine activity type based on request
        activity_type = 'page_view'
        description = f"{request.method} {request.endpoint or request.path}"
        
        if request.endpoint:
            if 'login' in request.endpoint:
                activity_type = 'authentication'
            elif 'logout' in request.endpoint:
                activity_type = 'authentication'
            elif 'widget' in request.endpoint:
                activity_type = 'widget_action'
                description = f"Widget access: {request.endpoint}"
            elif request.method in ['POST', 'PUT', 'DELETE']:
                activity_type = 'data_modification'
            elif 'settings' in request.endpoint:
                activity_type = 'settings_change'
        
        # Get request data for logging (be careful with sensitive data)
        request_data = None
        if request.method in ['POST', 'PUT'] and request.is_json:
            try:
                request_data = request.get_json()
            except:
                pass
        elif request.method in ['POST', 'PUT'] and request.form:
            request_data = dict(request.form)
        
        # Log activity for authenticated users
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Only log if it's not a static file request
        if not (request.endpoint and request.endpoint.startswith('static')):
            log_user_activity(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                request_data=request_data,
                response_status=response.status_code,
                duration_ms=duration_ms
            )
    
    except Exception as e:
        print(f"Error in after_request logging: {str(e)}")
    
    return response

class User(UserMixin):
    def __init__(self, id, username, email, is_active=True, user_level_id=4, level_name='User', level_code='user', permissions=None):
        self.id = id
        self.username = username
        self.email = email
        self._is_active = is_active
        self.user_level_id = user_level_id
        self.level_name = level_name
        self.level_code = level_code
        self.permissions = permissions or ['basic_access']

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value
    
    def has_permission(self, permission):
        """Check if user has a specific permission"""
        return 'all' in self.permissions or permission in self.permissions
    
    def is_admin(self):
        """Check if user is admin or super admin"""
        return self.level_code in ['admin', 'super_admin']
    
    def is_super_admin(self):
        """Check if user is super admin"""
        return self.level_code == 'super_admin'

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except psycopg.Error as e:
        print(f"Database connection error: {e}")
        return None

# User Action Logging Functions
def log_user_action(category, action, description, target_type=None, target_id=None, 
                   details=None, success=True, error_message=None, user=None):
    """
    Log a user action for audit trail
    
    Args:
        category: Action category ('Authentication', 'Dashboard', 'Widgets', 'Settings', 'Admin')
        action: Specific action ('Login', 'Add Widget', 'Change Password', etc.)
        description: Human-readable description of the action
        target_type: Type of object affected ('widget', 'user', 'settings', etc.)
        target_id: ID of the affected object
        details: Additional context as dict
        success: Whether the action succeeded
        error_message: Error message if action failed
        user: User object (defaults to current_user)
    """
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cur = conn.cursor()
        
        # Use provided user or current_user
        if user is None and hasattr(current_user, 'id'):
            user = current_user
            
        user_id = user.id if user and hasattr(user, 'id') else None
        username = user.username if user and hasattr(user, 'username') else 'Unknown'
        session_id = session.get('session_token')
        
        # Get client info
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent')
        
        cur.execute("""
            INSERT INTO user_actions 
            (user_id, username, session_id, category, action, description, 
             target_type, target_id, details, ip_address, user_agent, success, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, username, session_id, category, action, description,
              target_type, target_id, json.dumps(details) if details else None,
              ip_address, user_agent, success, error_message))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error logging user action: {e}")
        if conn:
            conn.close()

def log_authentication_action(action, username, success=True, error_message=None, details=None):
    """Log authentication-related actions"""
    description = f"User {username} {action.lower()}"
    if not success and error_message:
        description += f" - {error_message}"
    
    log_user_action(
        category='Authentication',
        action=action,
        description=description,
        target_type='user',
        target_id=username,
        details=details,
        success=success,
        error_message=error_message,
        user=None  # Authentication might not have current_user set
    )

def log_widget_action(action, widget_type=None, widget_id=None, success=True, details=None):
    """Log widget-related actions"""
    if widget_type and widget_id:
        description = f"{action} {widget_type} widget ({widget_id})"
    elif widget_type:
        description = f"{action} {widget_type} widget"
    else:
        description = f"{action} widget"
    
    log_user_action(
        category='Widgets',
        action=action,
        description=description,
        target_type='widget',
        target_id=widget_id,
        details=details,
        success=success
    )

def log_settings_action(action, setting_type=None, success=True, details=None):
    """Log settings-related actions"""
    description = f"{action}"
    if setting_type:
        description += f" {setting_type}"
    
    log_user_action(
        category='Settings',
        action=action,
        description=description,
        target_type='settings',
        target_id=setting_type,
        details=details,
        success=success
    )

def log_admin_action(action, target_type=None, target_id=None, success=True, details=None):
    """Log admin-related actions"""
    description = f"Admin: {action}"
    if target_type and target_id:
        description += f" {target_type} ({target_id})"
    elif target_type:
        description += f" {target_type}"
    
    log_user_action(
        category='Admin',
        action=action,
        description=description,
        target_type=target_type,
        target_id=target_id,
        details=details,
        success=success
    )

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login with session validation"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get current session token from Flask session
            session_token = session.get('session_token')
            
            if session_token:
                # Check if user exists AND their current session is active
                cur.execute("""
                    SELECT u.*, ul.level_name, ul.level_code, ul.permissions 
                    FROM users u 
                    JOIN user_levels ul ON u.user_level_id = ul.id 
                    LEFT JOIN user_sessions us ON u.id = us.user_id AND us.session_token = %s
                    WHERE u.id = %s AND u.is_active = TRUE 
                    AND (us.is_active = TRUE OR us.session_token IS NULL)
                """, (session_token, user_id))
            else:
                # No session token, just check user status
                cur.execute("""
                    SELECT u.*, ul.level_name, ul.level_code, ul.permissions 
                    FROM users u 
                    JOIN user_levels ul ON u.user_level_id = ul.id 
                    WHERE u.id = %s AND u.is_active = TRUE
                """, (user_id,))
            
            user_data = cur.fetchone()
            if user_data:
                return User(
                    user_data['id'], 
                    user_data['username'], 
                    user_data['email'], 
                    user_data['is_active'],
                    user_data['user_level_id'],
                    user_data['level_name'],
                    user_data['level_code'],
                    user_data['permissions']
                )
        except psycopg.Error as e:
            print(f"Error loading user: {e}")
        finally:
            conn.close()
    return None

def log_login_attempt(username, ip_address, user_agent, success, failure_reason=None):
    """Log login attempt to database"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO login_attempts (username, ip_address, user_agent, success, failure_reason)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, ip_address, user_agent, success, failure_reason))
            conn.commit()
        except psycopg.Error as e:
            print(f"Error logging login attempt: {e}")
        finally:
            conn.close()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def hash_password(password):
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator to require super admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if not current_user.is_super_admin():
            flash('Super admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard route - redirects to index for compatibility"""
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with enhanced security logging"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            log_security_event(
                event_type='incomplete_login',
                severity='low',
                description=f'Incomplete login attempt for username: {username or "empty"}',
                additional_data={'username': username, 'missing_fields': ['username' if not username else None, 'password' if not password else None]}
            )
            return render_template('login.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor(row_factory=dict_row)
                
                # Check for rate limiting (basic protection)
                cur.execute("""
                    SELECT COUNT(*) as attempt_count
                    FROM login_attempts 
                    WHERE ip_address = %s 
                    AND attempted_at > %s
                    AND success = FALSE
                """, (get_client_ip(), datetime.now() - timedelta(minutes=15)))
                
                failed_attempts = cur.fetchone()['attempt_count']
                if failed_attempts >= 20:
                    log_security_event(
                        event_type='rate_limit_exceeded',
                        severity='high',
                        description=f'Too many failed login attempts from IP: {get_client_ip()}',
                        additional_data={'failed_attempts': failed_attempts, 'username': username}
                    )
                    flash('Too many failed attempts. Please try again in 15 minutes.', 'error')
                    return render_template('login.html')
                
                # Get user data
                cur.execute("""
                    SELECT u.*, ul.level_name, ul.level_code, ul.permissions 
                    FROM users u 
                    JOIN user_levels ul ON u.user_level_id = ul.id 
                    WHERE u.username = %s AND u.is_active = TRUE
                """, (username,))
                user_data = cur.fetchone()
                
                if user_data and verify_password(password, user_data['password_hash']):
                    # Successful login
                    user = User(
                        user_data['id'], 
                        user_data['username'], 
                        user_data['email'], 
                        user_data['is_active'],
                        user_data['user_level_id'],
                        user_data['level_name'],
                        user_data['level_code'],
                        user_data['permissions']
                    )
                    login_user(user, remember=remember_me)
                    
                    # Create enhanced session record
                    session_token = str(uuid.uuid4())
                    session['session_token'] = session_token
                    
                    try:
                        # Update user last login
                        cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (datetime.now(), user_data['id']))
                        
                        # SINGLE SESSION ENFORCEMENT: Invalidate all existing active sessions for this user
                        cur.execute("""
                            UPDATE user_sessions 
                            SET is_active = FALSE, 
                                logout_reason = 'new_login',
                                logout_timestamp = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND is_active = TRUE
                        """, (user_data['id'],))
                        
                        # Create/update session record with enhanced data
                        expires_at = datetime.now() + timedelta(days=30 if remember_me else 1)
                        cur.execute("""
                            INSERT INTO user_sessions 
                            (user_id, session_token, ip_address, user_agent, login_method, device_fingerprint, is_active, expires_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (session_token) DO UPDATE SET
                            last_activity = CURRENT_TIMESTAMP,
                            is_active = TRUE,
                            expires_at = %s
                        """, (
                            user_data['id'], 
                            session_token, 
                            get_client_ip(), 
                            request.headers.get('User-Agent', '')[:500],
                            'remember_me' if remember_me else 'password',
                            hash(request.headers.get('User-Agent', '') + get_client_ip()),  # Simple device fingerprint
                            True,
                            expires_at,
                            expires_at
                        ))
                        
                        conn.commit()
                    except psycopg.Error as session_error:
                        # If session creation fails, still allow login but log the error
                        print(f"Session creation error during login: {session_error}")
                        conn.rollback()
                        log_security_event(
                            event_type='session_creation_error',
                            severity='medium',
                            description=f'Session creation error during login: {str(session_error)}',
                            additional_data={'username': username, 'error': str(session_error)}
                        )
                    
                    # These logging operations are non-critical - if they fail, don't show error to user
                    try:
                        log_login_attempt(username, get_client_ip(), request.headers.get('User-Agent'), True)
                        log_user_activity(
                            user_id=user_data['id'],
                            activity_type='login',
                            description=f'Successful login for user: {username}',
                            additional_data={'remember_me': remember_me, 'session_token': session_token}
                        )
                        log_authentication_action(
                            action='Login',
                            username=username,
                            success=True,
                            details={'remember_me': remember_me, 'method': 'password'}
                        )
                    except Exception as logging_error:
                        # Log the logging error but don't affect user experience
                        print(f"Logging error during successful login: {logging_error}")
                    
                    flash(f'Welcome back, {username}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    # Failed login
                    failure_reason = 'Invalid credentials'
                    log_login_attempt(username, get_client_ip(), request.headers.get('User-Agent'), False, failure_reason)
                    
                    # Log security event for failed login
                    log_security_event(
                        event_type='failed_login',
                        severity='medium',
                        description=f'Failed login attempt for username: {username}',
                        additional_data={'username': username, 'reason': failure_reason}
                    )
                    
                    # Log authentication action for audit trail
                    log_authentication_action(
                        action='Login',
                        username=username,
                        success=False,
                        error_message=failure_reason,
                        details={'attempted_username': username}
                    )
                    
                    flash('Invalid username or password', 'error')
                    
            except psycopg.Error as e:
                # Only show error message for critical database errors during authentication
                error_str = str(e)
                print(f"Database error during login: {e}")
                
                # Check if this is a critical authentication error vs. logging error
                if any(keyword in error_str.lower() for keyword in ['users', 'user_levels', 'authentication', 'login']):
                    # Critical authentication error - show message to user
                    log_security_event(
                        event_type='authentication_database_error',
                        severity='high',
                        description=f'Critical database error during authentication: {error_str}',
                        additional_data={'username': username, 'error': error_str}
                    )
                    flash('An error occurred during authentication. Please try again.', 'error')
                else:
                    # Likely a logging/session error - don't confuse the user
                    log_security_event(
                        event_type='database_error',
                        severity='medium',
                        description=f'Non-critical database error during login: {error_str}',
                        additional_data={'username': username, 'error': error_str}
                    )
                    # No flash message - user might already be logged in
            finally:
                conn.close()
        else:
            log_security_event(
                event_type='database_connection_failed',
                severity='critical',
                description='Database connection failed during login attempt'
            )
            flash('Database connection error', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor(row_factory=dict_row)
                
                # Check if username or email already exists
                cur.execute("SELECT username, email FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cur.fetchone()
                
                if existing_user:
                    if existing_user['username'] == username:
                        flash('Username already exists', 'error')
                    else:
                        flash('Email already registered', 'error')
                    return render_template('register.html')
                
                # Hash password and create user
                password_hash = hash_password(password)
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, user_level_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (username, email, password_hash, 4))  # 4 = User level
                
                user_id = cur.fetchone()['id']
                conn.commit()
                
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
                
            except psycopg.Error as e:
                print(f"Database error during registration: {e}")
                flash('An error occurred during registration. Please try again.', 'error')
            finally:
                conn.close()
        else:
            flash('Database connection error', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user with session management"""
    user_id = current_user.id
    username = current_user.username
    session_token = session.get('session_token')
    
    # Log logout activity
    log_user_activity(
        user_id=user_id,
        activity_type='logout',
        description=f'User {username} logged out',
        additional_data={'session_token': session_token}
    )
    
    # Log authentication action for audit trail
    log_authentication_action(
        action='Logout',
        username=username,
        success=True,
        details={'session_token': session_token}
    )
    
    # Deactivate session in database
    if session_token:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE user_sessions 
                    SET is_active = FALSE, 
                        last_activity = CURRENT_TIMESTAMP 
                    WHERE session_token = %s
                """, (session_token,))
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Error deactivating session: {str(e)}")
    
    # Clear session data
    session.clear()
    logout_user()
    
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    conn = get_db_connection()
    recent_attempts = []
    
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute("""
                SELECT attempted_at, ip_address, success, failure_reason 
                FROM login_attempts 
                WHERE username = %s 
                ORDER BY attempted_at DESC 
                LIMIT 10
            """, (current_user.username,))
            attempts = cur.fetchall()
            
            # Convert to list of dictionaries for easier frontend handling
            recent_attempts = []
            for attempt in attempts:
                recent_attempts.append({
                    'attempted_at': attempt['attempted_at'],
                    'attempted_at_iso': attempt['attempted_at'].isoformat() if attempt['attempted_at'] else None,
                    'ip_address': attempt['ip_address'],
                    'success': attempt['success'],
                    'failure_reason': attempt['failure_reason']
                })
                
        except psycopg.Error as e:
            print(f"Error fetching login attempts: {e}")
        finally:
            conn.close()
    
    return render_template('profile.html', user=current_user, recent_attempts=recent_attempts)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allow users to change their own password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return render_template('change_password.html')
        
        if current_password == new_password:
            flash('New password must be different from current password', 'error')
            return render_template('change_password.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor(row_factory=dict_row)
                
                # Get current user's password hash
                cur.execute("SELECT password_hash FROM users WHERE id = %s", (current_user.id,))
                user_data = cur.fetchone()
                
                if user_data and verify_password(current_password, user_data['password_hash']):
                    # Current password is correct, update to new password
                    new_password_hash = hash_password(new_password)
                    cur.execute("""
                        UPDATE users 
                        SET password_hash = %s, updated_at = %s 
                        WHERE id = %s
                    """, (new_password_hash, datetime.now(), current_user.id))
                    conn.commit()
                    
                    flash('Password changed successfully!', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Current password is incorrect', 'error')
                    
            except psycopg.Error as e:
                print(f"Error changing password: {e}")
                flash('An error occurred while changing password', 'error')
            finally:
                conn.close()
    
    return render_template('change_password.html')

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin user management page"""
    conn = get_db_connection()
    users = []
    user_levels = []
    
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get all users with their levels
            cur.execute("""
                SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.last_login,
                       ul.level_name, ul.level_code, u.user_level_id
                FROM users u 
                JOIN user_levels ul ON u.user_level_id = ul.id 
                ORDER BY u.created_at DESC
            """)
            users = cur.fetchall()
            
            # Get all available user levels
            cur.execute("SELECT * FROM user_levels ORDER BY id")
            user_levels = cur.fetchall()
            
        except psycopg.Error as e:
            print(f"Error fetching users: {e}")
            flash('Error loading users', 'error')
        finally:
            conn.close()
    
    return render_template('admin_users.html', users=users, user_levels=user_levels)

# Admin: Add User
@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    conn = get_db_connection()
    user_levels = []
    error = None
    success = None
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute("SELECT * FROM user_levels ORDER BY id")
            user_levels = cur.fetchall()
            print(f"DEBUG: Found {len(user_levels)} user levels: {user_levels}")
            if request.method == 'POST':
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                user_level_id = request.form.get('user_level_id')
                if not all([username, email, password, user_level_id]):
                    error = 'All fields are required.'
                elif len(password) < 6:
                    error = 'Password must be at least 6 characters.'
                else:
                    # Check for duplicate username/email
                    cur.execute("SELECT 1 FROM users WHERE username = %s OR email = %s", (username, email))
                    if cur.fetchone():
                        error = 'Username or email already exists.'
                    else:
                        password_hash = hash_password(password)
                        new_id = str(uuid.uuid4())
                        cur.execute("""
                            INSERT INTO users (id, username, email, password_hash, user_level_id, is_active, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s)
                        """, (new_id, username, email, password_hash, int(user_level_id), datetime.now(), datetime.now()))
                        conn.commit()
                        success = f'User {username} created successfully.'
        except Exception as e:
            error = f'Error creating user: {str(e)}'
        finally:
            conn.close()
    return render_template('admin_add_user.html', user_levels=user_levels, error=error, success=success)

@app.route('/admin/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Edit user details"""
    conn = get_db_connection()
    user_levels = []
    user_data = None
    
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get user data
            cur.execute("""
                SELECT u.*, ul.level_name, ul.level_code
                FROM users u 
                JOIN user_levels ul ON u.user_level_id = ul.id 
                WHERE u.id = %s
            """, (user_id,))
            user_data = cur.fetchone()
            
            # Get all available user levels
            cur.execute("SELECT * FROM user_levels ORDER BY id")
            user_levels = cur.fetchall()
            
            if request.method == 'POST':
                new_level_id = request.form.get('user_level_id')
                is_active = request.form.get('is_active') == 'on'
                
                # Only super admin can change super admin users
                if user_data['level_code'] == 'super_admin' and not current_user.is_super_admin():
                    flash('Only super admins can modify super admin accounts', 'error')
                    return redirect(url_for('admin_users'))
                
                # Update user
                cur.execute("""
                    UPDATE users 
                    SET user_level_id = %s, is_active = %s, updated_at = %s 
                    WHERE id = %s
                """, (new_level_id, is_active, datetime.now(), user_id))
                conn.commit()
                
                flash(f'User {user_data["username"]} updated successfully', 'success')
                return redirect(url_for('admin_users'))
                
        except psycopg.Error as e:
            print(f"Error editing user: {e}")
            flash('Error updating user', 'error')
        finally:
            conn.close()
    
    if not user_data:
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_edit_user.html', user_data=user_data, user_levels=user_levels)

@app.route('/admin/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete user (deactivate)"""
    conn = get_db_connection()
    
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get user data first
            cur.execute("SELECT username, user_level_id FROM users WHERE id = %s", (user_id,))
            user_data = cur.fetchone()
            
            if user_data:
                # Don't allow deleting super admin users unless current user is super admin
                cur.execute("SELECT level_code FROM user_levels WHERE id = %s", (user_data['user_level_id'],))
                level_data = cur.fetchone()
                
                if level_data and level_data['level_code'] == 'super_admin' and not current_user.is_super_admin():
                    flash('Only super admins can delete super admin accounts', 'error')
                    return redirect(url_for('admin_users'))
                
                # Don't allow self-deletion
                if str(user_id) == str(current_user.id):
                    flash('You cannot delete your own account', 'error')
                    return redirect(url_for('admin_users'))
                
                # Deactivate user instead of deleting
                cur.execute("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,))
                conn.commit()
                
                flash(f'User {user_data["username"]} has been deactivated', 'success')
            else:
                flash('User not found', 'error')
                
        except psycopg.Error as e:
            print(f"Error deleting user: {e}")
            flash('Error deleting user', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<user_id>/activate', methods=['POST'])
@login_required
@admin_required
def admin_activate_user(user_id):
    """Activate user"""
    conn = get_db_connection()
    
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get user data first
            cur.execute("SELECT username, user_level_id FROM users WHERE id = %s", (user_id,))
            user_data = cur.fetchone()
            
            if user_data:
                # Activate user
                cur.execute("UPDATE users SET is_active = TRUE WHERE id = %s", (user_id,))
                conn.commit()
                
                flash(f'User {user_data["username"]} has been activated', 'success')
            else:
                flash('User not found', 'error')
                
        except psycopg.Error as e:
            print(f"Error activating user: {e}")
            flash('Error activating user', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<user_id>/permanent-delete', methods=['POST'])
@login_required
@super_admin_required
def admin_permanent_delete_user(user_id):
    """Permanently delete user from database (super admin only)"""
    conn = get_db_connection()
    
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get user data first
            cur.execute("SELECT username, user_level_id FROM users WHERE id = %s", (user_id,))
            user_data = cur.fetchone()
            
            if user_data:
                # Don't allow self-deletion
                if str(user_id) == str(current_user.id):
                    flash('You cannot delete your own account', 'error')
                    return redirect(url_for('admin_users'))
                
                # Get username for flash message
                username = user_data['username']
                
                # Delete user-related data first (foreign key constraints)
                # Delete user widget settings
                cur.execute("DELETE FROM user_widget_settings WHERE user_id = %s", (user_id,))
                
                # Delete user favorite weather locations
                cur.execute("DELETE FROM user_favorite_weather_locations WHERE user_id = %s", (user_id,))
                
                # Delete user sessions (if any)
                cur.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,)) 
                
                # Finally delete the user
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                
                if cur.rowcount > 0:
                    conn.commit()
                    flash(f'User {username} has been permanently deleted from the system', 'success')
                else:
                    flash('User not found or already deleted', 'error')
            else:
                flash('User not found', 'error')
                
        except psycopg.Error as e:
            print(f"Error permanently deleting user: {e}")
            flash('Error permanently deleting user. Check for database constraints.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """Admin reset user password"""
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not new_password or not confirm_password:
        flash('Both password fields are required', 'error')
        return redirect(url_for('admin_edit_user', user_id=user_id))
    
    if new_password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('admin_edit_user', user_id=user_id))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('admin_edit_user', user_id=user_id))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get user data first
            cur.execute("""
                SELECT u.username, ul.level_code 
                FROM users u 
                JOIN user_levels ul ON u.user_level_id = ul.id 
                WHERE u.id = %s
            """, (user_id,))
            user_data = cur.fetchone()
            
            if user_data:
                # Don't allow resetting super admin passwords unless current user is super admin
                if user_data['level_code'] == 'super_admin' and not current_user.is_super_admin():
                    flash('Only super admins can reset super admin passwords', 'error')
                    return redirect(url_for('admin_edit_user', user_id=user_id))
                
                # Hash new password and update
                new_password_hash = hash_password(new_password)
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, updated_at = %s 
                    WHERE id = %s
                """, (new_password_hash, datetime.now(), user_id))
                conn.commit()
                
                flash(f'Password reset successfully for user {user_data["username"]}', 'success')
            else:
                flash('User not found', 'error')
                
        except psycopg.Error as e:
            print(f"Error resetting password: {e}")
            flash('Error resetting password', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('admin_edit_user', user_id=user_id))

@app.route('/admin/database')
@login_required
@admin_required
def admin_database():
    """Admin database management via pgAdmin"""
    return render_template('admin_database.html')

@app.route('/containers')
@login_required
def containers():
    """Docker containers monitoring page"""
    if not (current_user.is_admin() or current_user.has_permission('system_settings')):
        flash('Permission denied - admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get Docker client
        client = docker.from_env()
        
        # Get all containers (running and stopped)
        containers = client.containers.list(all=True)
        
        container_data = []
        for container in containers:
            try:
                # Get container stats (only for running containers)
                stats = None
                if container.status == 'running':
                    try:
                        # Get fresh stats with decode=True for proper data format
                        stats = container.stats(stream=False, decode=True)
                    except Exception as e:
                        print(f"Error getting stats for {container.name}: {e}")
                
                # Calculate memory usage
                memory_usage = 0
                memory_limit = 0
                memory_percent = 0
                
                if stats and 'memory' in stats:
                    memory_usage = stats['memory']['usage']
                    memory_limit = stats['memory']['limit']
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                
                # Calculate CPU usage
                cpu_percent = 0
                if stats and 'cpu_stats' in stats and 'precpu_stats' in stats:
                    cpu_stats = stats['cpu_stats']
                    precpu_stats = stats['precpu_stats']
                    
                    # Calculate CPU percentage properly
                    cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                    system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                    
                    if system_delta > 0 and cpu_delta > 0:
                        number_cpus = len(cpu_stats['cpu_usage']['percpu_usage'])
                        cpu_percent = (cpu_delta / system_delta) * number_cpus * 100.0
                
                # Get container image size
                try:
                    image = client.images.get(container.image.id)
                    image_size = image.attrs['Size']
                except:
                    image_size = 0
                
                container_info = {
                    'name': container.name,
                    'id': container.short_id,
                    'image': container.image.tags[0] if container.image.tags else str(container.image.id)[:12],
                    'status': container.status,
                    'created': container.attrs['Created'][:19].replace('T', ' '),
                    'ports': ', '.join([f"{port['PrivatePort']}/{port['Type']}" + 
                                      (f"→{port['PublicPort']}" if 'PublicPort' in port else '') 
                                      for port in container.attrs['NetworkSettings']['Ports'].values() 
                                      if port for port in port]),
                    'memory_usage': memory_usage,
                    'memory_limit': memory_limit,
                    'memory_percent': round(memory_percent, 2),
                    'cpu_percent': round(cpu_percent, 2),
                    'image_size': image_size
                }
                
                container_data.append(container_info)
                
            except Exception as e:
                print(f"Error processing container {container.name}: {e}")
                # Add basic container info even if stats fail
                container_data.append({
                    'name': container.name,
                    'id': container.short_id,
                    'image': container.image.tags[0] if container.image.tags else str(container.image.id)[:12],
                    'status': container.status,
                    'created': container.attrs['Created'][:19].replace('T', ' '),
                    'ports': 'N/A',
                    'memory_usage': 0,
                    'memory_limit': 0,
                    'memory_percent': 0,
                    'cpu_percent': 0,
                    'network_rx': 0,
                    'network_tx': 0,
                    'block_read': 0,
                    'block_write': 0,
                    'image_size': 0
                })
        
        # Get host system information
        host_info = {
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_total': psutil.virtual_memory().total,
            'memory_used': psutil.virtual_memory().used,
            'memory_percent': psutil.virtual_memory().percent,
            'disk_total': psutil.disk_usage('/').total,
            'disk_used': psutil.disk_usage('/').used,
            'disk_percent': psutil.disk_usage('/').percent,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        }
        
        # Get network interfaces
        network_interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    network_interfaces.append({
                        'interface': interface,
                        'ip': addr.address,
                        'netmask': addr.netmask
                    })
        
        host_info['network_interfaces'] = network_interfaces
        
        return render_template('containers.html', 
                             containers=container_data, 
                             host_info=host_info)
        
    except Exception as e:
        flash(f'Error accessing Docker: {str(e)}', 'error')
        return render_template('containers.html', containers=[], host_info={})

@app.route('/stocks')
def stocks_dashboard():
    """Stock market data dashboard - public access"""
    return render_template('stocks_dashboard.html')

@app.route('/stocks/test')
def stocks_test():
    """Stock API test page"""
    return render_template('stocks_test.html')

@app.route('/pid_demo')
def pid_demo():
    """P&ID Process Control Demo"""
    return render_template('pid_demo.html')

@app.route('/animation_test')
def animation_test():
    """Animation Test Page"""
    return render_template('animation_test.html')

@app.route('/simple_test')
def simple_test():
    """Simple Animation Test Page"""
    return render_template('simple_test.html')

@app.route('/standalone_pid')
def standalone_pid():
    """Standalone P&ID Demo without base template"""
    response = make_response(render_template('standalone_pid.html'))
    # Allow this page to be embedded in iframes by removing X-Frame-Options
    response.headers.pop('X-Frame-Options', None)
    # Or explicitly set it to allow same origin
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@app.route('/api/stocks/data')
@login_required
def stocks_api_data():
    """API endpoint for stock data (for AJAX calls from frontend)"""
    if not current_user.has_permission('stock_view'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        import requests
        # Get data from our API container
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        symbol = request.args.get('symbol', '^IXIC')
        limit = request.args.get('limit', '1000')
        interval = request.args.get('interval', '1h')
        
        api_url = f"http://{api_host}:{api_port}/stocks/prices"
        response = requests.get(api_url, params={
            'symbol': symbol,
            'limit': limit,
            'interval': interval
        }, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch stock data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error fetching stock data: {str(e)}'}), 500

@app.route('/api/stocks/latest')
@login_required
def stocks_api_latest():
    """API endpoint for latest stock prices"""
    if not current_user.has_permission('stock_view'):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get exchange filter from query parameters
    exchange = request.args.get('exchange')
    
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        api_url = f"http://{api_host}:{api_port}/stocks/latest"
        
        # Add exchange parameter if provided
        params = {}
        if exchange:
            params['exchange'] = exchange
            
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch latest stock data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error fetching latest stock data: {str(e)}'}), 500

@app.route('/api/stocks/fetch', methods=['POST'])
@login_required
def stocks_api_fetch():
    """Trigger stock data fetch (admin only)"""
    if not current_user.has_permission('stock_admin'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        api_url = f"http://{api_host}:{api_port}/stocks/fetch"
        response = requests.post(api_url, timeout=300)  # 5 minute timeout for data fetch
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to trigger stock data fetch'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error triggering stock data fetch: {str(e)}'}), 500

# Public stock dashboard endpoints (no authentication required)
@app.route('/stocks/public')
def stocks_dashboard_public():
    """Public stock market data dashboard"""
    return render_template('stocks_dashboard.html')

@app.route('/stocks/api/prices')
def stocks_api_prices_public():
    """Public API endpoint for stock prices"""
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        symbol = request.args.get('symbol', 'AAPL')
        limit = request.args.get('limit', '100')
        interval = request.args.get('interval', '1d')
        
        api_url = f"http://{api_host}:{api_port}/stocks/prices"
        response = requests.get(api_url, params={
            'symbol': symbol,
            'limit': limit,
            'interval': interval
        }, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch stock data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error fetching stock data: {str(e)}'}), 500

@app.route('/stocks/api/latest')
def stocks_api_latest_public():
    """Public API endpoint for latest stock prices"""
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        api_url = f"http://{api_host}:{api_port}/stocks/latest"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch latest stock data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error fetching latest stock data: {str(e)}'}), 500

@app.route('/stocks/api/yearly-growth')
def stocks_api_yearly_growth_public():
    """Public API endpoint for yearly growth analysis"""
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        symbol = request.args.get('symbol', '^IXIC')
        
        api_url = f"http://{api_host}:{api_port}/stocks/yearly-growth"
        response = requests.get(api_url, params={'symbol': symbol}, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch yearly growth data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error fetching yearly growth data: {str(e)}'}), 500

@app.route('/stocks/api/investment-calculator')
def stocks_api_investment_calculator_public():
    """Public API endpoint for investment calculator"""
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        symbol = request.args.get('symbol', '^IXIC')
        monthly_investment = request.args.get('monthly_investment', '100')
        start_year = request.args.get('start_year')  # New parameter
        
        params = {
            'symbol': symbol,
            'monthly_investment': monthly_investment
        }
        if start_year:
            params['start_year'] = start_year
        
        api_url = f"http://{api_host}:{api_port}/stocks/investment-calculator"
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to calculate investment returns'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error calculating investment returns: {str(e)}'}), 500

@app.route('/stocks/api/available-years')
def stocks_api_available_years_public():
    """Public API endpoint for available years"""
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        symbol = request.args.get('symbol', '^IXIC')
        
        api_url = f"http://{api_host}:{api_port}/stocks/available-years"
        response = requests.get(api_url, params={'symbol': symbol}, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to get available years'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error getting available years: {str(e)}'}), 500

@app.route('/stocks/api/fetch-symbol', methods=['POST'])
def stocks_api_fetch_symbol_public():
    """Public API endpoint to fetch data for any stock symbol"""
    try:
        import requests
        api_host = os.environ.get('API_HOST', 'api')
        api_port = os.environ.get('API_PORT', '8000')
        
        # Forward the request data
        api_url = f"http://{api_host}:{api_port}/stocks/fetch-symbol"
        response = requests.post(api_url, json=request.get_json(), timeout=60)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch stock data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error fetching stock data: {str(e)}'}), 500

@app.route('/stocks/api/available')
def stocks_api_available():
    """Get list of stocks that have data in the database"""
    # Get exchange filter from query parameters
    exchange = request.args.get('exchange')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with optional exchange filter
        base_query = """
            SELECT s.symbol, s.name, s.exchange, COUNT(sp.id) as record_count,
                   MAX(sp.close_price) as latest_price
            FROM stocks s
            LEFT JOIN stock_prices sp ON s.id = sp.stock_id
            WHERE 1=1
        """
        
        params = []
        if exchange:
            base_query += " AND s.exchange = %s"
            params.append(exchange)
            
        base_query += """
            GROUP BY s.id, s.symbol, s.name, s.exchange 
            HAVING COUNT(sp.id) > 0
            ORDER BY record_count DESC
        """
        
        cursor.execute(base_query, params)
        
        available_stocks = []
        for symbol, name, stock_exchange, record_count, latest_price in cursor.fetchall():
            # Define display names for common symbols
            display_names = {
                '^IXIC': 'NASDAQ Composite (^IXIC)',
                '^GSPC': 'S&P 500 (^GSPC)', 
                '^DJI': 'Dow Jones (^DJI)',
                'VWRL.L': 'Vanguard All-World ETF (VWRL.L) *World Fund',
                'IWDA.L': 'iShares World ETF (IWDA.L)',
                'AAPL': 'Apple Inc. (AAPL)',
                'MSFT': 'Microsoft (MSFT)',
                'GOOGL': 'Google (GOOGL)', 
                'TSLA': 'Tesla (TSLA)'
            }
            
            display_name = display_names.get(symbol, f'{name} ({symbol})')
            
            available_stocks.append({
                'symbol': symbol,
                'name': display_name,
                'record_count': record_count,
                'latest_price': float(latest_price) if latest_price else 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(available_stocks)
        
    except Exception as e:
        return jsonify({'error': f'Error fetching available stocks: {str(e)}'}), 500

@app.route('/webapp/api/table-statistics')
@login_required
def table_statistics():
    """Get database table statistics including row counts and disk usage"""
    if not (current_user.is_admin() or current_user.has_permission('system_settings')):
        return jsonify({'error': 'Permission denied - admin access required'}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table statistics with size information
        cursor.execute("""
            SELECT 
                schemaname,
                relname as tablename,
                n_tup_ins as total_inserts,
                n_tup_upd as total_updates,
                n_tup_del as total_deletes,
                n_live_tup as row_count,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC;
        """)
        
        stats_data = cursor.fetchall()
        
        # Get table sizes
        cursor.execute("""
            SELECT 
                table_name,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as total_size,
                pg_size_pretty(pg_relation_size(quote_ident(table_name))) as data_size,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_name)) - pg_relation_size(quote_ident(table_name))) as index_size
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
        """)
        
        size_data = cursor.fetchall()
        
        # Combine statistics and size data
        size_dict = {row[0]: {'total_size': row[1], 'data_size': row[2], 'index_size': row[3]} for row in size_data}
        
        tables = []
        for row in stats_data:
            table_name = row[1]
            size_info = size_dict.get(table_name, {'total_size': '0 MB', 'data_size': '0 MB', 'index_size': '0 MB'})
            
            tables.append({
                'table_name': table_name,
                'row_count': row[5] or 0,
                'total_size': size_info['total_size'],
                'data_size': size_info['data_size'], 
                'index_size': size_info['index_size'],
                'dead_rows': row[6] or 0,
                'last_vacuum': row[7].strftime('%Y-%m-%d %H:%M') if row[7] else None,
                'last_analyze': row[9].strftime('%Y-%m-%d %H:%M') if row[9] else None,
                'last_autoanalyze': row[10].strftime('%Y-%m-%d %H:%M') if row[10] else None
            })
        
        # Add any tables that have size but no stats (shouldn't happen but just in case)
        for table_name, size_info in size_dict.items():
            if not any(t['table_name'] == table_name for t in tables):
                tables.append({
                    'table_name': table_name,
                    'row_count': 0,
                    'total_size': size_info['total_size'],
                    'data_size': size_info['data_size'],
                    'index_size': size_info['index_size'],
                    'dead_rows': 0,
                    'last_vacuum': None,
                    'last_analyze': None,
                    'last_autoanalyze': None
                })
        
        cursor.close()
        conn.close()
        
        return jsonify({'tables': tables})
        
    except Exception as e:
        return jsonify({'error': f'Error fetching table statistics: {str(e)}'}), 500

@app.route('/containers/demo')
def containers_demo():
    """Demo version of containers page (public access for testing)"""
    try:
        # Get Docker client
        client = docker.from_env()
        
        # Get all containers (running and stopped)
        containers = client.containers.list(all=True)
        
        container_data = []
        for container in containers:
            try:
                # Get container stats (only for running containers)
                stats = None
                if container.status == 'running':
                    try:
                        # Get fresh stats with decode=True for proper data format
                        stats = container.stats(stream=False, decode=True)
                    except Exception as e:
                        print(f"Error getting stats for {container.name}: {e}")
                
                # Calculate memory usage
                memory_usage = 0
                memory_limit = 0
                memory_percent = 0
                
                if stats and 'memory' in stats:
                    memory_usage = stats['memory']['usage']
                    memory_limit = stats['memory']['limit']
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                
                # Calculate CPU usage
                cpu_percent = 0
                if stats and 'cpu_stats' in stats and 'precpu_stats' in stats:
                    cpu_stats = stats['cpu_stats']
                    precpu_stats = stats['precpu_stats']
                    
                    # Calculate CPU percentage properly
                    cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                    system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                    
                    if system_delta > 0 and cpu_delta > 0:
                        number_cpus = len(cpu_stats['cpu_usage']['percpu_usage'])
                        cpu_percent = (cpu_delta / system_delta) * number_cpus * 100.0
                
                # Get container image size
                try:
                    image = client.images.get(container.image.id)
                    image_size = image.attrs['Size']
                except:
                    image_size = 0
                
                container_info = {
                    'name': container.name,
                    'id': container.short_id,
                    'image': container.image.tags[0] if container.image.tags else str(container.image.id)[:12],
                    'status': container.status,
                    'created': container.attrs['Created'][:19].replace('T', ' '),
                    'ports': ', '.join([f"{port['PrivatePort']}/{port['Type']}" + 
                                      (f"→{port['PublicPort']}" if 'PublicPort' in port else '') 
                                      for port in container.attrs['NetworkSettings']['Ports'].values() 
                                      if port for port in port]),
                    'memory_usage': memory_usage,
                    'memory_limit': memory_limit,
                    'memory_percent': round(memory_percent, 2),
                    'cpu_percent': round(cpu_percent, 2),
                    'image_size': image_size
                }
                
                container_data.append(container_info)
                
            except Exception as e:
                print(f"Error processing container {container.name}: {e}")
                # Add basic container info even if stats fail
                container_data.append({
                    'name': container.name,
                    'id': container.short_id,
                    'image': container.image.tags[0] if container.image.tags else str(container.image.id)[:12],
                    'status': container.status,
                    'created': container.attrs['Created'][:19].replace('T', ' '),
                    'ports': 'N/A',
                    'memory_usage': 0,
                    'memory_limit': 0,
                    'memory_percent': 0,
                    'cpu_percent': 0,
                    'network_rx': 0,
                    'network_tx': 0,
                    'block_read': 0,
                    'block_write': 0,
                    'image_size': 0
                })
        
        # Get host system information
        host_info = {
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_total': psutil.virtual_memory().total,
            'memory_used': psutil.virtual_memory().used,
            'memory_percent': psutil.virtual_memory().percent,
            'disk_total': psutil.disk_usage('/').total,
            'disk_used': psutil.disk_usage('/').used,
            'disk_percent': psutil.disk_usage('/').percent,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        }
        
        # Get network interfaces
        network_interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    network_interfaces.append({
                        'interface': interface,
                        'ip': addr.address,
                        'netmask': addr.netmask
                    })
        
        host_info['network_interfaces'] = network_interfaces
        
        return render_template('containers.html', 
                             containers=container_data, 
                             host_info=host_info)
        
    except Exception as e:
        return f'Error accessing Docker: {str(e)}', 500

@app.route('/webapp/api/host-info')
def host_info_api():
    """API endpoint for real-time host system information"""
    try:
        # Get host system information
        host_info = {
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),  # Short interval for responsiveness
            'memory_total': psutil.virtual_memory().total,
            'memory_used': psutil.virtual_memory().used,
            'memory_percent': psutil.virtual_memory().percent,
            'disk_total': psutil.disk_usage('/').total,
            'disk_used': psutil.disk_usage('/').used,
            'disk_percent': psutil.disk_usage('/').percent,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        }
        
        return jsonify({
            'success': True,
            'host_info': host_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/webapp/api/containers/test')
def containers_api_test():
    """Test API endpoint to check Docker container access"""
    try:
        # Get Docker client
        client = docker.from_env()
        
        # Get basic container list
        containers = client.containers.list(all=True)
        
        container_info = []
        for container in containers:
            container_info.append({
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else str(container.image.id)[:12]
            })
        
        # Get basic host info
        host_info = {
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': round(psutil.virtual_memory().total / 1024**3, 2)
        }
        
        return jsonify({
            'success': True,
            'containers': container_info,
            'host_info': host_info,
            'container_count': len(container_info)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Weather Routes
@app.route('/weather')
@login_required
def weather():
    """Weather dashboard page"""
    return render_template('weather_dashboard.html')

@app.route('/performance')
@login_required
def performance():
    """Performance monitoring dashboard page with detailed database health"""
    return render_template('performance_dashboard.html')

@app.route('/performance-original')
@login_required
def performance_original():
    """Original complex performance dashboard"""
    return render_template('performance_dashboard.html')

@app.route('/performance-debug')
@login_required
def performance_debug():
    """Performance debug page"""
    return render_template('performance_debug.html')

@app.route('/performance-test')
@login_required
def performance_test():
    """Performance API test page"""
    return render_template('performance_test.html')

@app.route('/performance-simple-test')
@login_required
def performance_simple_test():
    """Simple performance test page with visible debugging"""
    return render_template('performance_simple_test.html')

@app.route('/weather/api/locations', methods=['GET'])
@login_required
def get_weather_locations():
    """Get user's favorite weather locations using shared location system"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        cur.execute("""
            SELECT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude, ufwl.added_at as created_at
            FROM user_favorite_weather_locations ufwl
            JOIN shared_weather_locations swl ON ufwl.weather_location_id = swl.id
            WHERE ufwl.user_id = %s 
            ORDER BY swl.city_name ASC
        """, (current_user.id,))
        
        locations = cur.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'locations': [dict(location) for location in locations]
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching locations: {str(e)}'}), 500

def trigger_historic_data_collection(location_id):
    """Trigger historic weather data collection for a new location in background"""
    def run_collection():
        try:
            # Make HTTP request to API container to trigger historic weather collection
            api_url = "http://api:8000/weather/trigger-historic-collection"
            payload = {
                "location_id": location_id,
                "years": 20
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Historic data collection (20 years) triggered for location {location_id}: {result}")
            else:
                print(f"Failed to trigger historic data collection for location {location_id}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error triggering historic data collection for location {location_id}: {e}")
    
    # Run collection in background thread to not block the API response
    thread = threading.Thread(target=run_collection)
    thread.daemon = True
    thread.start()

@app.route('/weather/api/locations', methods=['POST'])
@login_required
def add_weather_location():
    """Add a new favorite weather location using shared location system"""
    try:
        print(f"DEBUG: Current user: {current_user.id if current_user.is_authenticated else 'Not authenticated'}", flush=True)  # Debug logging
        
        data = request.get_json()
        print(f"DEBUG: Received data: {data}", flush=True)  # Debug logging
        
        if not data:
            print("DEBUG: No JSON data received", flush=True)  # Debug logging
            return jsonify({'error': 'No data provided'}), 400
        
        city_name = data.get('city_name', '').strip()
        country = data.get('country', '').strip()
        print(f"DEBUG: Stripped values - city: '{city_name}', country: '{country}'", flush=True)  # Debug logging
        
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        print(f"DEBUG: Converted coordinates - lat: {latitude}, lon: {longitude}", flush=True)  # Debug logging
        
        if not city_name or not country:
            print(f"DEBUG: Missing city or country", flush=True)  # Debug logging
            return jsonify({'error': 'City name and country are required'}), 400
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            print(f"DEBUG: Invalid coordinates range", flush=True)  # Debug logging
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        print(f"DEBUG: About to connect to database", flush=True)  # Debug logging
        
        conn = get_db_connection()
        if not conn:
            print(f"DEBUG: Database connection failed", flush=True)  # Debug logging
            return jsonify({'error': 'Database connection failed'}), 500
        
        print(f"DEBUG: Database connection successful", flush=True)  # Debug logging
        cur = conn.cursor()
        try:
            print(f"DEBUG: About to query for existing location", flush=True)  # Debug logging
            # First, check if this location already exists in shared locations
            cur.execute("""
                SELECT id FROM shared_weather_locations 
                WHERE city_name = %s AND country = %s AND latitude = %s AND longitude = %s
            """, (city_name, country, latitude, longitude))
            
            existing_location = cur.fetchone()
            print(f"DEBUG: Existing location query result: {existing_location}", flush=True)  # Debug logging
            
            if existing_location:
                # Location exists, just add to user's favorites
                shared_location_id = existing_location[0]
                
                # Check if user already has this location as favorite
                cur.execute("""
                    SELECT id FROM user_favorite_weather_locations 
                    WHERE user_id = %s AND weather_location_id = %s
                """, (current_user.id, shared_location_id))
                
                if cur.fetchone():
                    conn.close()
                    return jsonify({'error': 'Location already exists in your favorites'}), 400
                
                # Add to user's favorites
                cur.execute("""
                    INSERT INTO user_favorite_weather_locations (user_id, weather_location_id)
                    VALUES (%s, %s)
                    RETURNING id
                """, (current_user.id, shared_location_id))
                
                favorite_id = cur.fetchone()[0]
                conn.commit()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'Added {city_name}, {country} to your favorites.',
                    'location_id': shared_location_id,
                    'favorite_id': favorite_id
                })
            
            else:
                # Location doesn't exist, create new shared location
                print(f"DEBUG: Creating new shared location for {city_name}, {country}", flush=True)  # Debug logging
                cur.execute("""
                    INSERT INTO shared_weather_locations (city_name, country, latitude, longitude)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (city_name, country, latitude, longitude))
                
                shared_location_id = cur.fetchone()[0]
                print(f"DEBUG: Created shared location with ID: {shared_location_id}", flush=True)  # Debug logging
                
                # Add to user's favorites
                print(f"DEBUG: Adding to user favorites", flush=True)  # Debug logging
                cur.execute("""
                    INSERT INTO user_favorite_weather_locations (user_id, weather_location_id)
                    VALUES (%s, %s)
                    RETURNING id
                """, (current_user.id, shared_location_id))
                
                favorite_id = cur.fetchone()[0]
                print(f"DEBUG: Created favorite with ID: {favorite_id}", flush=True)  # Debug logging
                conn.commit()
                print(f"DEBUG: Database transaction committed", flush=True)  # Debug logging
                conn.close()
                
                # Trigger historic weather data collection in background for new location
                print(f"DEBUG: Triggering historic data collection", flush=True)  # Debug logging
                trigger_historic_data_collection(shared_location_id)
                
                print(f"DEBUG: Returning success response", flush=True)  # Debug logging
                return jsonify({
                    'success': True,
                    'message': f'Added {city_name}, {country} to favorites. Weather data collection started.',
                    'location_id': shared_location_id,
                    'favorite_id': favorite_id
                })
            
        except psycopg.IntegrityError as e:
            conn.rollback()
            conn.close()
            return jsonify({'error': 'Database constraint violation'}), 400
        
    except (ValueError, TypeError) as e:
        print(f"DEBUG: ValueError/TypeError in add_weather_location: {str(e)}", flush=True)  # Debug logging
        return jsonify({'error': 'Invalid coordinate format'}), 400
    except Exception as e:
        print(f"DEBUG: Unexpected error in add_weather_location: {str(e)}", flush=True)  # Debug logging
        return jsonify({'error': f'Error adding location: {str(e)}'}), 500

@app.route('/weather/api/locations/<int:location_id>', methods=['DELETE'])
@login_required
def remove_weather_location(location_id):
    """Remove a favorite weather location from user's favorites"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor()
        
        # Get location details before deletion
        cur.execute("""
            SELECT swl.city_name, swl.country 
            FROM user_favorite_weather_locations ufwl
            JOIN shared_weather_locations swl ON ufwl.weather_location_id = swl.id
            WHERE ufwl.user_id = %s AND swl.id = %s
        """, (current_user.id, location_id))
        
        location_info = cur.fetchone()
        if not location_info:
            conn.close()
            return jsonify({'error': 'Location not found in your favorites'}), 404
        
        # Remove from user's favorites
        cur.execute("""
            DELETE FROM user_favorite_weather_locations 
            WHERE user_id = %s AND weather_location_id = %s
        """, (current_user.id, location_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Removed {location_info[0]}, {location_info[1]} from favorites'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error removing location: {str(e)}'}), 500

@app.route('/weather/api/historical/<int:location_id>')
@login_required
def get_historical_weather(location_id):
    """Get historical weather data for a specific location"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Verify location belongs to current user using new shared system
        cur.execute("""
            SELECT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude
            FROM user_favorite_weather_locations ufwl
            JOIN shared_weather_locations swl ON ufwl.weather_location_id = swl.id
            WHERE ufwl.user_id = %s AND swl.id = %s
        """, (current_user.id, location_id))
        
        location = cur.fetchone()
        if not location:
            conn.close()
            return jsonify({'error': 'Location not found or access denied'}), 404
        
        # Get summary statistics for the location
        cur.execute("""
            SELECT 
                COUNT(*) as total_days,
                ROUND(AVG(temperature_avg)::numeric, 2) as avg_temperature,
                ROUND(MIN(temperature_min)::numeric, 2) as min_temperature,
                ROUND(MAX(temperature_max)::numeric, 2) as max_temperature,
                ROUND(AVG(humidity_avg)::numeric, 1) as avg_humidity,
                ROUND(SUM(precipitation_total)::numeric, 1) as total_precipitation,
                ROUND(AVG(precipitation_total)::numeric, 2) as avg_precipitation,
                ROUND(AVG(wind_speed_avg)::numeric, 1) as avg_wind_speed,
                ROUND(MAX(wind_speed_max)::numeric, 1) as max_wind_speed
            FROM historic_weather_data 
            WHERE shared_weather_location_id = %s
        """, (location_id,))
        
        stats = cur.fetchone()
        
        # Get recent 30 days of weather data
        # Filter out incomplete records (recent dates might have NULL data)
        cur.execute("""
            SELECT 
                date,
                temperature_min,
                temperature_max,
                temperature_avg,
                humidity_avg,
                precipitation_total,
                wind_speed_avg,
                weather_symbol,
                CASE 
                    WHEN temperature_min IS NULL AND temperature_max IS NULL AND temperature_avg IS NULL
                    THEN 'incomplete'
                    ELSE 'complete'
                END as data_status
            FROM historic_weather_data 
            WHERE shared_weather_location_id = %s
            ORDER BY date DESC
            LIMIT 30
        """, (location_id,))
        
        recent_weather_raw = cur.fetchall()
        
        # Separate complete and incomplete records
        recent_weather = []
        incomplete_dates = []
        
        for row in recent_weather_raw:
            row_dict = dict(row)
            if row_dict['data_status'] == 'complete':
                # Remove the data_status field before adding to results
                del row_dict['data_status']
                recent_weather.append(row_dict)
            else:
                incomplete_dates.append(row_dict['date'])
        
        # Try to get current weather data for incomplete dates if they're recent (last 3 days)
        from datetime import date, timedelta
        recent_threshold = date.today() - timedelta(days=3)
        
        for incomplete_date in incomplete_dates:
            if incomplete_date >= recent_threshold:
                # Try to get current weather data for this date
                cur.execute("""
                    SELECT 
                        DATE(recorded_at) as date,
                        temperature as temperature_avg,
                        humidity as humidity_avg,
                        wind_speed as wind_speed_avg,
                        weather_symbol,
                        weather_description
                    FROM current_weather_data 
                    WHERE DATE(recorded_at) = %s
                    AND shared_weather_location_id = %s
                    ORDER BY recorded_at DESC
                    LIMIT 1
                """, (incomplete_date, location_id))
                
                current_data = cur.fetchone()
                if current_data:
                    # Convert current weather to historical format
                    historical_equivalent = {
                        'date': current_data['date'],
                        'temperature_min': None,  # Not available from current weather
                        'temperature_max': None,  # Not available from current weather  
                        'temperature_avg': current_data['temperature_avg'],
                        'humidity_avg': current_data['humidity_avg'],
                        'precipitation_total': None,  # Not available from current weather
                        'wind_speed_avg': current_data['wind_speed_avg'],
                        'weather_symbol': current_data['weather_symbol']
                    }
                    recent_weather.append(historical_equivalent)
        
        # Sort by date descending after combining data sources
        recent_weather.sort(key=lambda x: x['date'], reverse=True)
        
        # Get monthly averages from all historical data
        cur.execute("""
            SELECT 
                EXTRACT(MONTH FROM date) as month,
                TO_CHAR(DATE_TRUNC('month', date), 'Month') as month_name,
                ROUND(AVG(temperature_avg)::numeric, 1) as avg_temperature,
                ROUND(AVG(precipitation_total)::numeric, 1) as avg_precipitation,
                COUNT(*) as data_points
            FROM historic_weather_data 
            WHERE shared_weather_location_id = %s
            GROUP BY EXTRACT(MONTH FROM date), TO_CHAR(DATE_TRUNC('month', date), 'Month')
            ORDER BY EXTRACT(MONTH FROM date)
        """, (location_id,))
        
        monthly_averages = cur.fetchall()
        conn.close()
        
        # Convert to regular dicts for JSON serialization
        stats_dict = dict(stats) if stats else {}
        recent_weather_list = [dict(row) for row in recent_weather]
        monthly_averages_list = [dict(row) for row in monthly_averages]
        
        # Add data availability info
        data_info = {
            'total_recent_records': len(recent_weather_list),
            'incomplete_recent_dates': len(incomplete_dates),
            'data_note': None
        }
        
        if incomplete_dates:
            missing_dates_str = ', '.join([d.strftime('%Y-%m-%d') for d in incomplete_dates[:3]])
            if len(incomplete_dates) > 3:
                missing_dates_str += f' and {len(incomplete_dates) - 3} more'
            data_info['data_note'] = f'Historical data for recent dates ({missing_dates_str}) may not be immediately available from weather services.'
        
        return jsonify({
            'success': True,
            'data': {
                'location': dict(location),
                'stats': stats_dict,
                'recent_weather': recent_weather_list,
                'monthly_averages': monthly_averages_list,
                'data_info': data_info
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching historical data: {str(e)}'}), 500

@app.route('/weather/api/monthly-trends/<int:location_id>')
@login_required
def get_monthly_trends(location_id):
    """Get monthly temperature trends over the past 20 years"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Verify location belongs to current user
        cur.execute("""
            SELECT swl.id, swl.city_name, swl.country
            FROM user_favorite_weather_locations ufwl
            JOIN shared_weather_locations swl ON ufwl.weather_location_id = swl.id
            WHERE ufwl.user_id = %s AND swl.id = %s
        """, (current_user.id, location_id))
        
        location = cur.fetchone()
        if not location:
            conn.close()
            return jsonify({'error': 'Location not found or access denied'}), 404
        
        # Get monthly averages for each year over the past 20 years
        cur.execute("""
            SELECT 
                EXTRACT(YEAR FROM date) as year,
                EXTRACT(MONTH FROM date) as month,
                ROUND(AVG(temperature_avg)::numeric, 2) as avg_temperature,
                ROUND(AVG(temperature_min)::numeric, 2) as avg_min_temp,
                ROUND(AVG(temperature_max)::numeric, 2) as avg_max_temp,
                ROUND(SUM(precipitation_total)::numeric, 1) as total_precipitation,
                COUNT(*) as data_points
            FROM historic_weather_data 
            WHERE shared_weather_location_id = %s 
            AND temperature_avg IS NOT NULL
            AND date >= CURRENT_DATE - INTERVAL '20 years'
            GROUP BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date)
            HAVING COUNT(*) >= 20  -- Only include months with significant data
            ORDER BY year, month
        """, (location_id,))
        
        monthly_data = cur.fetchall()
        
        # Organize data by month (1-12) and create trends
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        trends = {}
        for month_num in range(1, 13):
            month_name = months[month_num - 1]
            trends[month_name] = {
                'years': [],
                'avg_temperatures': [],
                'min_temperatures': [],
                'max_temperatures': [],
                'precipitation': []
            }
        
        # Populate trends data
        for row in monthly_data:
            month_name = months[int(row['month']) - 1]
            trends[month_name]['years'].append(int(row['year']))
            trends[month_name]['avg_temperatures'].append(float(row['avg_temperature']) if row['avg_temperature'] else None)
            trends[month_name]['min_temperatures'].append(float(row['avg_min_temp']) if row['avg_min_temp'] else None)
            trends[month_name]['max_temperatures'].append(float(row['avg_max_temp']) if row['avg_max_temp'] else None)
            trends[month_name]['precipitation'].append(float(row['total_precipitation']) if row['total_precipitation'] else None)
        
        # Calculate overall statistics
        cur.execute("""
            SELECT 
                MIN(EXTRACT(YEAR FROM date)) as earliest_year,
                MAX(EXTRACT(YEAR FROM date)) as latest_year,
                COUNT(DISTINCT EXTRACT(YEAR FROM date)) as total_years,
                COUNT(*) as total_data_points
            FROM historic_weather_data 
            WHERE shared_weather_location_id = %s 
            AND temperature_avg IS NOT NULL
            AND date >= CURRENT_DATE - INTERVAL '20 years'
        """, (location_id,))
        
        stats = cur.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'location': {
                    'id': location['id'],
                    'city_name': location['city_name'],
                    'country': location['country']
                },
                'trends': trends,
                'statistics': {
                    'earliest_year': int(stats['earliest_year']) if stats['earliest_year'] else None,
                    'latest_year': int(stats['latest_year']) if stats['latest_year'] else None,
                    'total_years': int(stats['total_years']) if stats['total_years'] else 0,
                    'total_data_points': int(stats['total_data_points']) if stats['total_data_points'] else 0
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching monthly trends: {str(e)}'}), 500

@app.route('/weather/api/forecast/<int:location_id>')
@login_required
def get_forecast_data(location_id):
    """Get 7-day forecast data for a specific location"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get location details using new shared system
        cur.execute("""
            SELECT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude
            FROM user_favorite_weather_locations ufwl
            JOIN shared_weather_locations swl ON ufwl.weather_location_id = swl.id
            WHERE ufwl.user_id = %s AND swl.id = %s
        """, (current_user.id, location_id))
        
        location = cur.fetchone()
        conn.close()
        
        if not location:
            return jsonify({'error': 'Location not found'}), 404
        
        # Fetch 7-day forecast from yr.no API
        import requests
        
        # yr.no API endpoint for forecast
        lat = float(location['latitude'])
        lon = float(location['longitude'])
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
        
        headers = {
            'User-Agent': 'WeatherApp/1.0 (contact@example.com)'  # yr.no requires proper User-Agent
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        forecast_data = response.json()
        
        # Process forecast data to get daily forecasts for next 7 days
        daily_forecasts = []
        from datetime import datetime, timedelta
        
        # Get current date and next 7 days
        today = datetime.now().date()
        
        for i in range(7):
            forecast_date = today + timedelta(days=i)
            date_str = forecast_date.strftime('%Y-%m-%d')
            
            # Find forecast data for this date
            day_data = {
                'date': date_str,
                'temperature_min': None,
                'temperature_max': None,
                'precipitation': 0,
                'humidity': None,
                'wind_speed': None,
                'weather_symbol': None,
                'weather_description': 'Unknown'
            }
            
            temps = []
            precip_total = 0
            humidity_values = []
            wind_values = []
            symbols = []
            
            # Extract data for this day from yr.no response
            if 'properties' in forecast_data and 'timeseries' in forecast_data['properties']:
                for entry in forecast_data['properties']['timeseries']:
                    entry_time = datetime.fromisoformat(entry['time'].replace('Z', '+00:00'))
                    if entry_time.date() == forecast_date:
                        details = entry['data']['instant']['details']
                        
                        # Collect temperature data
                        if 'air_temperature' in details:
                            temps.append(details['air_temperature'])
                        
                        # Collect humidity
                        if 'relative_humidity' in details:
                            humidity_values.append(details['relative_humidity'])
                        
                        # Collect wind speed
                        if 'wind_speed' in details:
                            wind_values.append(details['wind_speed'])
                        
                        # Collect precipitation if available
                        if 'next_1_hours' in entry['data']:
                            precip_data = entry['data']['next_1_hours']
                            if 'details' in precip_data and 'precipitation_amount' in precip_data['details']:
                                precip_total += precip_data['details']['precipitation_amount']
                            
                            # Get weather symbol
                            if 'summary' in precip_data and 'symbol_code' in precip_data['summary']:
                                symbols.append(precip_data['summary']['symbol_code'])
            
            # Calculate daily aggregates
            if temps:
                day_data['temperature_min'] = min(temps)
                day_data['temperature_max'] = max(temps)
            
            if humidity_values:
                day_data['humidity'] = sum(humidity_values) / len(humidity_values)
            
            if wind_values:
                day_data['wind_speed'] = sum(wind_values) / len(wind_values)
            
            day_data['precipitation'] = precip_total
            
            # Use most common weather symbol
            if symbols:
                day_data['weather_symbol'] = max(set(symbols), key=symbols.count)
                day_data['weather_description'] = get_weather_description_from_symbol(day_data['weather_symbol'])
            
            daily_forecasts.append(day_data)
        
        return jsonify({
            'success': True,
            'data': {
                'location': dict(location),
                'forecasts': daily_forecasts
            }
        })
        
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch forecast data: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error processing forecast data: {str(e)}'}), 500

@app.route('/weather/api/hourly/<int:location_id>')
@login_required
def get_hourly_weather(location_id):
    """Get next 24 hours hourly weather data for a specific location"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get location details using new shared system
        cur.execute("""
            SELECT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude
            FROM user_favorite_weather_locations ufwl
            JOIN shared_weather_locations swl ON ufwl.weather_location_id = swl.id
            WHERE ufwl.user_id = %s AND swl.id = %s
        """, (current_user.id, location_id))
        
        location = cur.fetchone()
        conn.close()
        
        if not location:
            return jsonify({'error': 'Location not found'}), 404
        
        # Fetch hourly forecast from yr.no API
        import requests
        from datetime import datetime, timedelta, timezone
        
        lat = float(location['latitude'])
        lon = float(location['longitude'])
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
        
        headers = {
            'User-Agent': 'WeatherApp/1.0 (contact@example.com)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        forecast_data = response.json()
        
        # Process hourly data for next 24 hours
        hourly_forecasts = []
        now = datetime.now(timezone.utc)  # Make timezone-aware
        
        if 'properties' in forecast_data and 'timeseries' in forecast_data['properties']:
            for entry in forecast_data['properties']['timeseries']:
                entry_time = datetime.fromisoformat(entry['time'].replace('Z', '+00:00'))
                
                # Only include next 24 hours
                if entry_time > now and entry_time <= now + timedelta(hours=24):
                    details = entry['data']['instant']['details']
                    
                    # Get precipitation and weather symbol from next_1_hours or next_6_hours
                    next_1h = entry['data'].get('next_1_hours', {})
                    next_6h = entry['data'].get('next_6_hours', {})
                    
                    precipitation = 0
                    weather_symbol = 'unknown'
                    
                    if next_1h:
                        precipitation = next_1h.get('details', {}).get('precipitation_amount', 0)
                        weather_symbol = next_1h.get('summary', {}).get('symbol_code', 'unknown')
                    elif next_6h:
                        precipitation = next_6h.get('details', {}).get('precipitation_amount', 0)
                        weather_symbol = next_6h.get('summary', {}).get('symbol_code', 'unknown')
                    
                    hourly_data = {
                        'time': entry_time.strftime('%H:%M'),
                        'date': entry_time.strftime('%Y-%m-%d'),
                        'datetime': entry['time'],
                        'timestamp': int(entry_time.timestamp()),  # Unix timestamp for JS conversion
                        'temperature': details.get('air_temperature'),
                        'humidity': details.get('relative_humidity'),
                        'pressure': details.get('air_pressure_at_sea_level'),
                        'wind_speed': details.get('wind_speed'),
                        'wind_direction': details.get('wind_from_direction'),
                        'precipitation': precipitation,
                        'weather_symbol': weather_symbol,
                        'weather_description': get_weather_description_from_symbol(weather_symbol)
                    }
                    
                    hourly_forecasts.append(hourly_data)
        
        # Limit to first 24 entries (one per hour)
        hourly_forecasts = hourly_forecasts[:24]
        
        return jsonify({
            'success': True,
            'data': {
                'location': dict(location),
                'hourly_forecasts': hourly_forecasts
            }
        })
        
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch hourly forecast data: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error processing hourly forecast data: {str(e)}'}), 500

def get_weather_description_from_symbol(symbol):
    """Convert yr.no weather symbol to description"""
    symbol_map = {
        'clearsky': 'Clear Sky',
        'fair': 'Fair',
        'partlycloudy': 'Partly Cloudy',
        'cloudy': 'Cloudy',
        'rainshowers': 'Rain Showers',
        'rain': 'Rain',
        'heavyrain': 'Heavy Rain',
        'snow': 'Snow',
        'fog': 'Fog'
    }
    
    # Extract base symbol (remove _day/_night suffix)
    base_symbol = symbol.split('_')[0] if symbol else 'unknown'
    return symbol_map.get(base_symbol, symbol.replace('_', ' ').title())

@app.route('/weather/api/current')
@login_required
def get_current_weather():
    """Get current weather for all user's favorite locations"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        cur.execute("""
            SELECT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude
            FROM user_favorite_weather_locations ufwl
            JOIN shared_weather_locations swl ON ufwl.weather_location_id = swl.id
            WHERE ufwl.user_id = %s 
            ORDER BY swl.city_name ASC
        """, (current_user.id,))
        
        locations = cur.fetchall()
        conn.close()
        
        weather_data = []
        for location in locations:
            try:
                # Fetch weather data from yr.no API
                weather_info = fetch_weather_data(location['latitude'], location['longitude'])
                weather_data.append({
                    'location_id': location['id'],
                    'city_name': location['city_name'],
                    'country': location['country'],
                    'latitude': float(location['latitude']),
                    'longitude': float(location['longitude']),
                    'weather': weather_info
                })
            except Exception as e:
                # If weather fetch fails, still include location with error
                weather_data.append({
                    'location_id': location['id'],
                    'city_name': location['city_name'],
                    'country': location['country'],
                    'latitude': float(location['latitude']),
                    'longitude': float(location['longitude']),
                    'weather': {'error': f'Failed to fetch weather: {str(e)}'}
                })
        
        return jsonify({
            'success': True,
            'weather_data': weather_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching weather data: {str(e)}'}), 500

def fetch_weather_data(latitude, longitude):
    """Fetch weather data from yr.no API"""
    try:
        # yr.no API endpoint for location forecast
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        headers = {
            'User-Agent': 'DockerWebApp/1.0 (contact@example.com)'  # Required by yr.no
        }
        params = {
            'lat': latitude,
            'lon': longitude
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract current weather from the first time period
        current_time = data['properties']['timeseries'][0]
        instant_details = current_time['data']['instant']['details']
        
        # Get next hour data for precipitation if available
        next_1h = current_time['data'].get('next_1_hours', {})
        next_6h = current_time['data'].get('next_6_hours', {})
        
        # Find tomorrow's forecast temperature (look for data 24 hours ahead)
        from datetime import datetime, timedelta
        tomorrow_forecast_temp = None
        tomorrow_forecast_symbol = None
        
        current_datetime = datetime.fromisoformat(current_time['time'].replace('Z', '+00:00'))
        tomorrow_target = current_datetime + timedelta(days=1)
        
        # Look for the closest forecast to 24 hours from now
        closest_forecast = None
        min_time_diff = float('inf')
        
        for forecast in data['properties']['timeseries']:
            forecast_datetime = datetime.fromisoformat(forecast['time'].replace('Z', '+00:00'))
            time_diff = abs((forecast_datetime - tomorrow_target).total_seconds())
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast
        
        if closest_forecast:
            tomorrow_details = closest_forecast['data']['instant']['details']
            tomorrow_forecast_temp = tomorrow_details.get('air_temperature')
            
            # Get tomorrow's weather symbol from next hour or next 6 hour forecast
            tomorrow_next_1h = closest_forecast['data'].get('next_1_hours', {})
            tomorrow_next_6h = closest_forecast['data'].get('next_6_hours', {})
            tomorrow_forecast_symbol = (tomorrow_next_1h.get('summary', {}).get('symbol_code') or 
                                      tomorrow_next_6h.get('summary', {}).get('symbol_code') or 
                                      'unknown')
        
        weather_info = {
            'timestamp': current_time['time'],
            'temperature': instant_details.get('air_temperature'),
            'humidity': instant_details.get('relative_humidity'),
            'pressure': instant_details.get('air_pressure_at_sea_level'),
            'wind_speed': instant_details.get('wind_speed'),
            'wind_direction': instant_details.get('wind_from_direction'),
            'cloud_cover': instant_details.get('cloud_area_fraction'),
            'precipitation_1h': next_1h.get('details', {}).get('precipitation_amount', 0),
            'symbol': next_1h.get('summary', {}).get('symbol_code', 'unknown'),
            'tomorrow_temperature': tomorrow_forecast_temp,
            'tomorrow_symbol': tomorrow_forecast_symbol
        }
        
        return weather_info
        
    except requests.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except KeyError as e:
        raise Exception(f"Unexpected API response format: {str(e)}")
    except Exception as e:
        raise Exception(f"Weather fetch error: {str(e)}")

@app.route('/weather/api/search-cities')
@login_required
def search_cities():
    """Search for cities using OpenStreetMap Nominatim API"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'success': True, 'cities': []})
        
        # Use OpenStreetMap Nominatim API for geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 15,
            'addressdetails': 1,
            'extratags': 1
        }
        headers = {
            'User-Agent': 'DockerWebApp/1.0 (contact@example.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        cities = []
        
        for item in data:
            # Filter to include cities, towns, villages, and administrative boundaries
            place_type = item.get('type', '').lower()
            place_class = item.get('class', '').lower()  # Use 'class' instead of 'category'
            osm_type = item.get('osm_type', '').lower()
            
            # More inclusive filtering - include places and administrative boundaries
            is_valid_place = (
                (place_class == 'place' and place_type in ['city', 'town', 'village', 'hamlet', 'suburb', 'neighbourhood']) or
                (place_class == 'boundary' and place_type == 'administrative') or
                (osm_type in ['relation', 'way'] and place_class == 'place')
            )
            
            if is_valid_place:
                address = item.get('address', {})
                display_name = item.get('display_name', '')
                
                # Extract city name and country with more flexible extraction
                city_name = (address.get('city') or 
                           address.get('town') or 
                           address.get('village') or 
                           address.get('hamlet') or
                           address.get('suburb') or
                           address.get('municipality') or
                           item.get('name', ''))
                
                country = address.get('country', '')
                state = address.get('state', '') or address.get('region', '')
                
                # Create a clean display name
                if state and country:
                    full_name = f"{city_name}, {state}, {country}"
                elif country:
                    full_name = f"{city_name}, {country}"
                else:
                    full_name = city_name
                
                if city_name and country:
                    city_data = {
                        'name': city_name,
                        'country': country,
                        'state': state,
                        'full_name': full_name,
                        'latitude': float(item['lat']),
                        'longitude': float(item['lon']),
                        'display_name': display_name
                    }
                    cities.append(city_data)
                    print(f"Added city: {city_data}")
                else:
                    print(f"Skipped due to missing city_name or country: {city_name}, {country}")
            else:
                print(f"Skipped due to filtering: {category}/{place_type}")
        
        # Remove duplicates based on city name and country
        unique_cities = []
        seen = set()
        for city in cities:
            key = (city['name'].lower(), city['country'].lower())
            if key not in seen:
                seen.add(key)
                unique_cities.append(city)
        
        result = {
            'success': True,
            'cities': unique_cities[:8]  # Limit to 8 suggestions
        }
        print(f"Returning {len(result['cities'])} unique cities for '{query}'")
        return jsonify(result)
        
    except requests.RequestException as e:
        print(f"API request error for '{query}': {str(e)}")
        return jsonify({'error': f'Search service unavailable: {str(e)}'}), 500
    except Exception as e:
        print(f"Search error for '{query}': {str(e)}")
        return jsonify({'error': f'Search error: {str(e)}'}), 500

@app.route('/weather/api/search-locations')
@login_required
def search_locations():
    """Search for any location (addresses, POIs, landmarks) using OpenStreetMap Nominatim API
    This is more permissive than search-cities and includes hotels, attractions, streets, etc."""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 3:
            return jsonify({'success': True, 'locations': []})
        
        # Use OpenStreetMap Nominatim API for geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 12,
            'addressdetails': 1,
            'extratags': 1
        }
        headers = {
            'User-Agent': 'DockerWebApp/1.0 (contact@example.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        locations = []
        
        for item in data:
            address = item.get('address', {})
            place_type = item.get('type', '').lower()
            place_class = item.get('class', '').lower()
            display_name = item.get('display_name', '')
            
            # Extract location details with fallbacks
            name = item.get('name', '')
            
            # Try to get city/town from address
            city_name = (address.get('city') or 
                        address.get('town') or 
                        address.get('village') or 
                        address.get('hamlet') or
                        address.get('suburb') or
                        address.get('municipality') or
                        address.get('county') or
                        '')
            
            country = address.get('country', '')
            state = address.get('state', '') or address.get('region', '')
            
            # Get specific address components
            road = address.get('road', '') or address.get('street', '')
            house_number = address.get('house_number', '')
            postcode = address.get('postcode', '')
            
            # Build a readable address string
            address_parts = []
            if house_number and road:
                address_parts.append(f"{house_number} {road}")
            elif road:
                address_parts.append(road)
            
            if name and name != city_name:
                address_parts.insert(0, name)
            
            if city_name:
                address_parts.append(city_name)
            if state and state != city_name:
                address_parts.append(state)
            if country:
                address_parts.append(country)
            
            full_address = ', '.join(filter(None, address_parts))
            
            # Create location type label
            type_label = ''
            if place_class == 'tourism':
                type_label = '🏛️ ' + place_type.replace('_', ' ').title()
            elif place_class == 'amenity':
                type_label = '🏨 ' + place_type.replace('_', ' ').title()
            elif place_class == 'place':
                type_label = '🏙️ ' + place_type.replace('_', ' ').title()
            elif place_class == 'highway':
                type_label = '🛣️ ' + place_type.replace('_', ' ').title()
            elif place_class == 'building':
                type_label = '🏢 ' + place_type.replace('_', ' ').title()
            else:
                type_label = place_type.replace('_', ' ').title()
            
            location_data = {
                'name': name or city_name,
                'city': city_name,
                'country': country,
                'state': state,
                'road': road,
                'house_number': house_number,
                'postcode': postcode,
                'full_address': full_address or display_name,
                'type': type_label,
                'place_class': place_class,
                'place_type': place_type,
                'latitude': float(item['lat']),
                'longitude': float(item['lon']),
                'display_name': display_name
            }
            locations.append(location_data)
        
        result = {
            'success': True,
            'locations': locations[:10]  # Limit to 10 suggestions
        }
        print(f"Returning {len(result['locations'])} locations for '{query}'")
        return jsonify(result)
        
    except requests.RequestException as e:
        print(f"API request error for '{query}': {str(e)}")
        return jsonify({'error': f'Search service unavailable: {str(e)}'}), 500
    except Exception as e:
        print(f"Search error for '{query}': {str(e)}")
        return jsonify({'error': f'Search error: {str(e)}'}), 500

@app.route('/weather/api/forecast-by-coords')
@login_required
def get_weather_by_coords():
    """Get weather forecast for specific coordinates (for trip weather widget)"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Latitude and longitude are required'}), 400
        
        # Fetch weather data from yr.no API
        weather_info = fetch_weather_data(lat, lon)
        
        return jsonify({
            'success': True,
            'weather': weather_info
        })
        
    except Exception as e:
        print(f"Weather forecast error: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to fetch weather: {str(e)}'}), 500

# Widget API endpoints for dashboard
@app.route('/widgets/stock/<symbol>')
@login_required
def widget_stock(symbol):
    """Get stock data for dashboard widget with live data"""
    print(f"Stock widget requested for symbol: {symbol}")
    try:
        # First try to get fresh data from the API container
        import requests
        
        try:
            # Call the API container for live stock data
            api_response = requests.get(f'http://api:8000/stock/{symbol}', timeout=10)
            if api_response.status_code == 200:
                api_data = api_response.json()
                if api_data.get('success') and 'data' in api_data:
                    stock_data = api_data['data']
                    result = {
                        'success': True,
                        'data': {
                            'symbol': symbol.upper(),
                            'price': float(stock_data.get('price', 0)),
                            'change': float(stock_data.get('change', 0)),
                            'change_percent': float(stock_data.get('change_percent', 0)),
                            'last_updated': stock_data.get('last_updated', 'just now')
                        }
                    }
                    print(f"Stock widget success (API data) for {symbol}: {result}")
                    return jsonify(result)
        except requests.RequestException as e:
            print(f"Failed to get live stock data from API: {e}")
        
        # Fallback to database data if live data fails
        conn = get_db_connection()
        cur = conn.cursor(row_factory=dict_row)
        
        # Get the latest stock price data for the symbol
        cur.execute("""
            SELECT 
                s.symbol,
                s.name,
                sp.close_price as current_price,
                sp.datetime as last_updated,
                LAG(sp.close_price) OVER (ORDER BY sp.datetime) as previous_price
            FROM stocks s
            JOIN stock_prices sp ON s.id = sp.stock_id
            WHERE s.symbol = %s 
            ORDER BY sp.datetime DESC 
            LIMIT 2
        """, (symbol.upper(),))
        
        prices = cur.fetchall()
        
        if prices and len(prices) > 0:
            current = prices[0]
            current_price = float(current['current_price'])
            
            # Calculate price change if we have previous price
            if len(prices) > 1 and prices[1]['previous_price']:
                previous_price = float(prices[1]['previous_price'])
                price_change = current_price - previous_price
                change_percent = (price_change / previous_price) * 100 if previous_price > 0 else 0
            else:
                price_change = 0
                change_percent = 0
        
            result = {
                'success': True,
                'data': {
                    'symbol': current['symbol'],
                    'price': current_price,
                    'change': price_change,
                    'change_percent': change_percent,
                    'last_updated': current['last_updated'].isoformat() if current['last_updated'] else None
                }
            }
            print(f"Stock widget success for {symbol}: {result}")
            return jsonify(result)
        else:
            error_result = {
                'success': False,
                'error': f'No data found for symbol {symbol}'
            }
            print(f"Stock widget no data for {symbol}: {error_result}")
            return jsonify(error_result)
            
    except Exception as e:
        print(f"Stock widget error for {symbol}: {str(e)}")
        error_result = {
            'success': False,
            'error': 'Failed to fetch stock data'
        }
        print(f"Stock widget exception for {symbol}: {error_result}")
        return jsonify(error_result)
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/widgets/weather/<location>')
@login_required
def widget_weather(location):
    """Get weather data for dashboard widget with fresh data"""
    try:
        # First try to get fresh weather data
        try:
            import requests
            from datetime import datetime
            
            # Get location coordinates first
            conn = get_db_connection()
            cur = conn.cursor(row_factory=dict_row)
            
            cur.execute("""
                SELECT DISTINCT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude
                FROM shared_weather_locations swl
                WHERE (
                    LOWER(swl.city_name) = LOWER(%s) OR
                    LOWER(REPLACE(swl.city_name, '-', ' ')) = LOWER(%s) OR
                    LOWER(REPLACE(swl.city_name, ' ', '-')) = LOWER(%s)
                )
                LIMIT 1
            """, (location, location, location))
            
            location_data = cur.fetchone()
            
            if location_data:
                # Fetch fresh weather data from Open-Meteo API with forecast
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={location_data['latitude']}&longitude={location_data['longitude']}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=3&timezone=auto"
                
                response = requests.get(weather_url, timeout=10)
                if response.status_code == 200:
                    weather_data = response.json()
                    current = weather_data.get('current', {})
                    daily = weather_data.get('daily', {})
                    
                    # Map weather codes to descriptions
                    weather_codes = {
                        0: ("Clear sky", "☀️"),
                        1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"), 3: ("Overcast", "☁️"),
                        45: ("Fog", "🌫️"), 48: ("Depositing rime fog", "🌫️"),
                        51: ("Light drizzle", "🌦️"), 53: ("Moderate drizzle", "🌦️"), 55: ("Dense drizzle", "🌧️"),
                        61: ("Slight rain", "🌧️"), 63: ("Moderate rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
                        80: ("Slight rain showers", "🌦️"), 81: ("Moderate rain showers", "🌧️"), 82: ("Violent rain showers", "⛈️"),
                        95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm with hail", "⛈️"), 99: ("Thunderstorm with heavy hail", "⛈️")
                    }
                    
                    weather_code = current.get('weather_code', 0)
                    description, symbol = weather_codes.get(weather_code, ("Unknown", "🌤️"))
                    
                    # Generate forecast data from API response
                    forecast_days = []
                    if daily and 'time' in daily:
                        day_names = ['Today', 'Tomorrow', 'Day 3']
                        for i in range(min(3, len(daily['time']))):
                            forecast_weather_code = daily.get('weather_code', [0])[i] if i < len(daily.get('weather_code', [])) else 0
                            forecast_desc, forecast_symbol = weather_codes.get(forecast_weather_code, ("Unknown", "🌤️"))
                            
                            forecast_days.append({
                                'day': day_names[i] if i < len(day_names) else f'Day {i+1}',
                                'temp_min': int(daily.get('temperature_2m_min', [0])[i]) if i < len(daily.get('temperature_2m_min', [])) else 0,
                                'temp_max': int(daily.get('temperature_2m_max', [0])[i]) if i < len(daily.get('temperature_2m_max', [])) else 0,
                                'symbol': forecast_symbol,
                                'precipitation': float(daily.get('precipitation_sum', [0])[i]) if i < len(daily.get('precipitation_sum', [])) else 0
                            })
                    
                    # Return fresh weather data with forecast
                    return jsonify({
                        'success': True,
                        'data': {
                            'location': f"{location_data['city_name']}, {location_data['country']}",
                            'temperature': int(current.get('temperature_2m', 0)),
                            'condition': description,
                            'humidity': current.get('relative_humidity_2m', 0),
                            'wind_speed': current.get('wind_speed_10m', 0),
                            'symbol': symbol,
                            'forecast': forecast_days,
                            'last_updated': datetime.now().strftime('%H:%M')
                        }
                    })
            
        except Exception as e:
            print(f"Failed to fetch fresh weather data: {e}")
            # Fall back to database data
            pass
        
        # Fallback to database weather data
        conn = get_db_connection()
        cur = conn.cursor(row_factory=dict_row)
        
        # Get the shared weather location that has current weather data
        cur.execute("""
            SELECT DISTINCT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude, cwd.recorded_at
            FROM shared_weather_locations swl
            INNER JOIN current_weather_data cwd ON swl.id = cwd.shared_weather_location_id
            WHERE (
                LOWER(swl.city_name) = LOWER(%s) OR
                LOWER(REPLACE(swl.city_name, '-', ' ')) = LOWER(%s) OR
                LOWER(REPLACE(swl.city_name, ' ', '-')) = LOWER(%s)
            )
            ORDER BY cwd.recorded_at DESC
            LIMIT 1
        """, (location, location, location))
        
        location_data = cur.fetchone()
        
        if not location_data:
            return jsonify({
                'success': False,
                'error': f'Location {location} not found in database'
            })
        
        # Get current weather using shared location ID
        cur.execute("""
            SELECT temperature, humidity, weather_description, weather_symbol, wind_speed
            FROM current_weather_data 
            WHERE shared_weather_location_id = %s 
            ORDER BY recorded_at DESC 
            LIMIT 1
        """, (location_data['id'],))
        
        current_weather = cur.fetchone()
        
        if not current_weather:
            return jsonify({
                'success': False,
                'error': f'No current weather data for {location}'
            })
        
        # Get recent 7-day historical data for trend analysis using shared location ID
        cur.execute("""
            SELECT 
                date,
                temperature_min,
                temperature_max,
                temperature_avg,
                humidity_avg,
                weather_symbol,
                precipitation_total,
                wind_speed_avg
            FROM historic_weather_data 
            WHERE shared_weather_location_id = %s 
            AND date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY date DESC 
            LIMIT 7
        """, (location_data['id'],))
        
        recent_history = cur.fetchall()
        
        # Function to convert weather symbols to emoji
        def get_weather_emoji(symbol):
            if not symbol:
                return '☀️'
            symbol = str(symbol).lower()
            if 'clear' in symbol or 'sunny' in symbol:
                return '☀️'
            elif 'cloud' in symbol:
                return '☁️'
            elif 'rain' in symbol or 'shower' in symbol:
                return '🌧️'
            elif 'snow' in symbol:
                return '🌨️'
            elif 'thunder' in symbol or 'storm' in symbol:
                return '⛈️'
            elif 'fog' in symbol or 'mist' in symbol:
                return '🌫️'
            elif 'partly' in symbol or 'partial' in symbol:
                return '⛅'
            else:
                return '🌤️'
        
        # Create forecast based on recent trends and seasonal patterns
        forecast_days = []
        if recent_history:
            # Calculate average trends from recent data
            avg_temp_trend = 0
            avg_humidity = sum(float(day['humidity_avg'] or 0) for day in recent_history) / len(recent_history)
            
            # Simple forecast: use recent averages with slight daily variations
            for i in range(3):  # 3-day forecast
                if len(recent_history) > i:
                    base_temp_min = float(recent_history[0]['temperature_min'] or current_weather['temperature'])
                    base_temp_max = float(recent_history[0]['temperature_max'] or current_weather['temperature'])
                    
                    # Add slight variation for future days
                    temp_variation = (i * 0.5) if i > 0 else 0
                    
                    forecast_days.append({
                        'day': ['Today', 'Tomorrow', 'Day 3'][i],
                        'temp_min': int(base_temp_min - temp_variation),
                        'temp_max': int(base_temp_max + temp_variation),
                        'symbol': get_weather_emoji(recent_history[min(i, len(recent_history)-1)]['weather_symbol']),
                        'precipitation': float(recent_history[min(i, len(recent_history)-1)]['precipitation_total'] or 0)
                    })
        else:
            # Fallback forecast when no historical data is available
            current_temp = int(current_weather['temperature'])
            current_symbol = get_weather_emoji(current_weather['weather_symbol'])
            
            for i in range(3):  # 3-day forecast
                forecast_days.append({
                    'day': ['Today', 'Tomorrow', 'Day 3'][i],
                    'temp_min': current_temp - 2 - i,  # Slight variation
                    'temp_max': current_temp + 3 + i,  # Slight variation
                    'symbol': current_symbol,
                    'precipitation': 0
                })
        
        # Enhanced response with forecast
        return jsonify({
            'success': True,
            'data': {
                'location': f"{location_data['city_name']}, {location_data['country']}",
                'temperature': int(current_weather['temperature']),
                'condition': current_weather['weather_description'].title() if current_weather['weather_description'] else 'Unknown',
                'humidity': current_weather['humidity'],
                'wind_speed': current_weather['wind_speed'],
                'symbol': get_weather_emoji(current_weather['weather_symbol']),
                'forecast': forecast_days,
                'recent_trend': {
                    'avg_humidity': round(avg_humidity, 1) if recent_history else None,
                    'days_of_data': len(recent_history)
                }
            }
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Weather error: {str(e)}'
        })
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/widgets/weather-locations')
@login_required
def widget_weather_locations():
    """Get available weather locations for widget configuration"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get all shared weather locations that have current weather data
        cur.execute("""
            SELECT DISTINCT swl.city_name, swl.country
            FROM shared_weather_locations swl
            INNER JOIN current_weather_data cwd ON swl.id = cwd.shared_weather_location_id
            ORDER BY swl.city_name
        """)
        
        locations = cur.fetchall()
        
        return jsonify({
            'success': True,
            'locations': [f"{loc['city_name']}, {loc['country']}" for loc in locations]
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching weather locations: {str(e)}'
        })
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/widget-settings', methods=['GET'])
@login_required
def get_widget_settings():
    """Get user's widget settings from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get user's widget settings
        cur.execute("""
            SELECT widget_id, enabled
            FROM user_widget_settings
            WHERE user_id = %s
        """, (current_user.id,))
        
        settings = cur.fetchall()
        
        # Convert to dictionary format
        widget_settings = {setting['widget_id']: setting['enabled'] for setting in settings}
        
        return jsonify({
            'success': True,
            'settings': widget_settings
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching widget settings: {str(e)}'
        })
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/widget-settings', methods=['POST'])
@login_required
def save_widget_settings():
    """Save user's widget settings to database"""
    try:
        data = request.get_json()
        if not data or 'settings' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request data'
            })
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        cur = conn.cursor()
        
        # Clear existing settings for this user
        cur.execute("DELETE FROM user_widget_settings WHERE user_id = %s", (current_user.id,))
        
        # Insert new settings
        for widget_id, enabled in data['settings'].items():
            cur.execute("""
                INSERT INTO user_widget_settings (user_id, widget_id, enabled)
                VALUES (%s, %s, %s)
            """, (current_user.id, widget_id, enabled))
        
        conn.commit()
        
        # Log widget settings action
        log_widget_action(
            action='Save Settings',
            details={
                'widget_count': len(data['settings']),
                'enabled_widgets': [wid for wid, enabled in data['settings'].items() if enabled],
                'disabled_widgets': [wid for wid, enabled in data['settings'].items() if not enabled]
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Saved {len(data["settings"])} widget settings'
        })
            
    except Exception as e:
        conn.rollback() if 'conn' in locals() else None
        return jsonify({
            'success': False,
            'error': f'Error saving widget settings: {str(e)}'
        })
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# Global storage for CPU usage history (last 120 seconds)
import time
from collections import deque

# Store CPU usage history with timestamps
cpu_history = deque(maxlen=60)  # 60 data points for 120 seconds (2-second intervals)

def update_cpu_history():
    """Update CPU history with current usage"""
    current_time = time.time()
    cpu_percent = psutil.cpu_percent(interval=0.1)  # Quick sample
    
    # Add new data point
    cpu_history.append({
        'timestamp': current_time,
        'usage': cpu_percent
    })
    
    # Clean old data (older than 120 seconds)
    cutoff_time = current_time - 120
    while cpu_history and cpu_history[0]['timestamp'] < cutoff_time:
        cpu_history.popleft()
    
    return cpu_percent

@app.route('/widgets/system/<metric>')
@login_required
def widget_system(metric):
    """Get system metrics for dashboard widget"""
    try:
        if metric == 'cpu':
            # Update and get CPU usage with history
            cpu_percent = update_cpu_history()
            
            # Prepare trend data (last 120 seconds)
            trend_data = []
            current_time = time.time()
            for data_point in cpu_history:
                # Calculate seconds ago
                seconds_ago = int(current_time - data_point['timestamp'])
                trend_data.append({
                    'time': seconds_ago,
                    'usage': data_point['usage']
                })
            
            # Sort by time (oldest first for chart)
            trend_data.sort(key=lambda x: x['time'], reverse=True)
            
            return jsonify({
                'success': True,
                'data': {
                    'value': f"{cpu_percent:.1f}%",
                    'label': 'CPU Usage',
                    'details': f"{psutil.cpu_count()} cores",
                    'trend': trend_data[-30:] if len(trend_data) > 30 else trend_data  # Last 60 seconds for display
                }
            })
            
        elif metric == 'memory':
            # Get memory usage
            memory = psutil.virtual_memory()
            used_gb = memory.used / (1024**3)
            total_gb = memory.total / (1024**3)
            return jsonify({
                'success': True,
                'data': {
                    'value': f"{memory.percent:.1f}%",
                    'label': 'Memory Usage',
                    'details': f"{used_gb:.1f}GB / {total_gb:.1f}GB"
                }
            })
            
        elif metric == 'disk':
            # Get disk usage
            disk = psutil.disk_usage('/')
            used_gb = disk.used / (1024**3)
            total_gb = disk.total / (1024**3)
            return jsonify({
                'success': True,
                'data': {
                    'value': f"{(disk.used / disk.total * 100):.1f}%",
                    'label': 'Disk Usage',
                    'details': f"{used_gb:.1f}GB / {total_gb:.1f}GB"
                }
            })
            
        elif metric == 'network':
            # Get network I/O
            network = psutil.net_io_counters()
            sent_mb = network.bytes_sent / (1024**2)
            recv_mb = network.bytes_recv / (1024**2)
            return jsonify({
                'success': True,
                'data': {
                    'value': f"{sent_mb + recv_mb:.0f}MB",
                    'label': 'Network I/O',
                    'details': f"↑{sent_mb:.0f}MB ↓{recv_mb:.0f}MB"
                }
            })
            
        elif metric == 'dbname':
            # Get comprehensive database statistics
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                
                # Get database size
                cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cur.fetchone()[0]
                
                # Get total row count across all user tables
                cur.execute("""
                    SELECT SUM(n_tup_ins + n_tup_upd + n_tup_del) as total_rows
                    FROM pg_stat_user_tables
                """)
                row_result = cur.fetchone()
                total_rows = row_result[0] if row_result and row_result[0] else 0
                
                # Get active connections
                cur.execute("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active' AND datname = current_database()
                """)
                active_connections = cur.fetchone()[0]
                
                # Get cache hit ratio
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN (blks_hit + blks_read) = 0 THEN 0
                            ELSE ROUND(CAST((blks_hit::float / (blks_hit + blks_read)) * 100 AS NUMERIC), 1)
                        END as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """)
                cache_hit_ratio = cur.fetchone()[0] or 0
                
                return jsonify({
                    'success': True,
                    'data': {
                        'value': db_size,
                        'label': 'Database Stats',
                        'details': f"{total_rows:,} rows | {active_connections} conn | {cache_hit_ratio}% cache",
                        'extended_stats': {
                            'size': db_size,
                            'total_rows': total_rows,
                            'active_connections': active_connections,
                            'cache_hit_ratio': cache_hit_ratio
                        }
                    }
                })
            except Exception as e:
                print(f"Database widget error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Database connection failed'
                })
            finally:
                if 'cur' in locals():
                    cur.close()
                if 'conn' in locals():
                    conn.close()
                    
        elif metric == 'containers':
            # Get Docker container status
            try:
                client = docker.from_env()
                containers = client.containers.list(all=True)
                running = len([c for c in containers if c.status == 'running'])
                total = len(containers)
                return jsonify({
                    'success': True,
                    'data': {
                        'value': f"{running}/{total}",
                        'label': 'Containers',
                        'details': f"{running} running"
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'Docker connection failed'
                })
                
        elif metric == 'users':
            # Get active user count
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM users")
                user_count = cur.fetchone()[0]
                return jsonify({
                    'success': True,
                    'data': {
                        'value': str(user_count),
                        'label': 'Total Users',
                        'details': 'Registered'
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'Database connection failed'
                })
            finally:
                if 'cur' in locals():
                    cur.close()
                if 'conn' in locals():
                    conn.close()
                    
        elif metric == 'uptime':
            # Get system uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            if uptime_seconds < 3600:  # Less than 1 hour
                uptime_str = f"{uptime_seconds / 60:.0f}m"
            elif uptime_seconds < 86400:  # Less than 1 day
                hours = uptime_seconds / 3600
                uptime_str = f"{hours:.1f}h"
            else:  # 1 day or more
                days = uptime_seconds / 86400
                uptime_str = f"{days:.1f}d"
                
            return jsonify({
                'success': True,
                'data': {
                    'value': uptime_str,
                    'label': 'System Uptime',
                    'details': datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M')
                }
            })
            
        elif metric == 'health':
            # Comprehensive system health check
            health_status = {
                'dbname': {'status': 'unknown', 'details': ''},
                'docker': {'status': 'unknown', 'details': ''},
                'api': {'status': 'unknown', 'details': ''},
                'system': {'status': 'unknown', 'details': ''}
            }
            
            overall_status = 'healthy'
            
            # Check database connection
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                health_status['database'] = {'status': 'healthy', 'details': 'Connected'}
            except Exception as e:
                health_status['database'] = {'status': 'error', 'details': str(e)[:50]}
                overall_status = 'error'
            finally:
                if 'cur' in locals():
                    cur.close()
                if 'conn' in locals():
                    conn.close()
            
            # Check Docker connection
            try:
                client = docker.from_env()
                containers = client.containers.list(all=True)
                running = len([c for c in containers if c.status == 'running'])
                total = len(containers)
                health_status['docker'] = {'status': 'healthy', 'details': f'{running}/{total} running'}
            except Exception as e:
                health_status['docker'] = {'status': 'warning', 'details': 'Connection failed'}
                if overall_status == 'healthy':
                    overall_status = 'warning'
            
            # Check API service (basic)
            try:
                api_host = os.environ.get('API_HOST', 'api')
                api_port = os.environ.get('API_PORT', '8000')
                import requests
                response = requests.get(f"http://{api_host}:{api_port}/health", timeout=5)
                if response.status_code == 200:
                    health_status['api'] = {'status': 'healthy', 'details': 'Responding'}
                else:
                    health_status['api'] = {'status': 'warning', 'details': f'HTTP {response.status_code}'}
                    if overall_status == 'healthy':
                        overall_status = 'warning'
            except Exception as e:
                health_status['api'] = {'status': 'warning', 'details': 'Unavailable'}
                if overall_status == 'healthy':
                    overall_status = 'warning'
            
            # Check system resources
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Consider system unhealthy if critical resources are exhausted
                if cpu_percent > 90 or memory.percent > 95 or (disk.used / disk.total * 100) > 95:
                    health_status['system'] = {'status': 'warning', 'details': 'High resource usage'}
                    if overall_status == 'healthy':
                        overall_status = 'warning'
                else:
                    health_status['system'] = {'status': 'healthy', 'details': 'Resources OK'}
            except Exception as e:
                health_status['system'] = {'status': 'error', 'details': 'Monitoring failed'}
                overall_status = 'error'
            
            return jsonify({
                'success': True,
                'data': {
                    'overall_status': overall_status,
                    'components': health_status,
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown metric: {metric}'
            })
            
    except Exception as e:
        print(f"System widget error for {metric}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch {metric} data'
        })

# Security Dashboard API Endpoints
@app.route('/api/security/user-activity')
@login_required
def get_user_activity():
    """Get user activity logs for security dashboard"""
    # Check if user has admin privileges
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 records
        user_id = request.args.get('user_id')
        activity_type = request.args.get('activity_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("ual.user_id = %s")
            params.append(user_id)
        
        if activity_type:
            where_conditions.append("ual.activity_type = %s")
            params.append(activity_type)
        
        if start_date:
            where_conditions.append("ual.timestamp >= %s")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("ual.timestamp <= %s")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM user_activity_logs ual
            LEFT JOIN users u ON ual.user_id = u.id
            {where_clause}
        """
        cur.execute(count_query, params)
        total_count = cur.fetchone()['total']
        
        # Get paginated results
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        query = f"""
            SELECT 
                ual.id,
                ual.user_id,
                u.username,
                ual.activity_type,
                ual.activity_description,
                ual.ip_address,
                ual.request_method,
                ual.request_url,
                ual.response_status,
                ual.timestamp,
                ual.duration_ms
            FROM user_activity_logs ual
            LEFT JOIN users u ON ual.user_id = u.id
            {where_clause}
            ORDER BY ual.timestamp DESC
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, params)
        activities = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'activities': [dict(activity) for activity in activities],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching user activity: {str(e)}'}), 500

@app.route('/api/security/active-sessions')
@login_required  
def get_active_sessions():
    """Get active user sessions for monitoring"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get active sessions using the view we created
        cur.execute("""
            SELECT 
                id,
                user_id,
                username,
                email,
                session_token,
                ip_address,
                user_agent,
                login_time,
                last_activity,
                login_method,
                idle_minutes
            FROM active_user_sessions
            ORDER BY last_activity DESC
        """)
        
        sessions = cur.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': [dict(session) for session in sessions],
                'total_active': len(sessions)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching active sessions: {str(e)}'}), 500

@app.route('/api/security/audit-trail')
@login_required
def get_audit_trail():
    """Get user actions audit trail"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        category = request.args.get('category')
        action = request.args.get('action') 
        username = request.args.get('username')
        success = request.args.get('success')
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if category:
            where_conditions.append("ua.category = %s")
            params.append(category)
        
        if action:
            where_conditions.append("ua.action ILIKE %s")
            params.append(f"%{action}%")
        
        if username:
            where_conditions.append("ua.username ILIKE %s")
            params.append(f"%{username}%")
            
        if success is not None:
            where_conditions.append("ua.success = %s")
            params.append(success.lower() == 'true')
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM user_actions ua
            {where_clause}
        """
        cur.execute(count_query, params)
        total_count = cur.fetchone()['total']
        
        # Calculate pagination
        total_pages = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # Get audit records with pagination
        query = f"""
            SELECT 
                ua.id,
                ua.timestamp,
                ua.username,
                ua.category,
                ua.action,
                ua.description,
                ua.target_type,
                ua.target_id,
                ua.success,
                ua.error_message,
                ua.ip_address,
                ua.details
            FROM user_actions ua
            {where_clause}
            ORDER BY ua.timestamp DESC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        cur.execute(query, params)
        audit_records = cur.fetchall()
        
        # Get available categories for filter
        cur.execute("SELECT DISTINCT category FROM user_actions ORDER BY category")
        categories = [row['category'] for row in cur.fetchall()]
        
        # Get available actions for filter  
        cur.execute("SELECT DISTINCT action FROM user_actions ORDER BY action")
        actions = [row['action'] for row in cur.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'audit_records': [dict(record) for record in audit_records],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': total_pages
                },
                'filters': {
                    'categories': categories,
                    'actions': actions
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching audit trail: {str(e)}'}), 500

@app.route('/api/security/security-events')
@login_required
def get_security_events():
    """Get security events for monitoring"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        severity = request.args.get('severity')
        resolved = request.args.get('resolved')
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if severity:
            where_conditions.append("se.severity = %s")
            params.append(severity)
        
        if resolved is not None:
            where_conditions.append("se.resolved = %s")
            params.append(resolved.lower() == 'true')
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM security_events se
            LEFT JOIN users u ON se.user_id = u.id
            {where_clause}
        """
        cur.execute(count_query, params)
        total_count = cur.fetchone()['total']
        
        # Get paginated results
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        query = f"""
            SELECT 
                se.id,
                se.user_id,
                u.username,
                se.event_type,
                se.severity,
                se.description,
                se.ip_address,
                se.timestamp,
                se.resolved,
                se.resolved_at,
                se.additional_data
            FROM security_events se
            LEFT JOIN users u ON se.user_id = u.id
            {where_clause}
            ORDER BY se.timestamp DESC
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, params)
        events = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'events': [dict(event) for event in events],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching security events: {str(e)}'}), 500

@app.route('/api/security/session/<session_id>/terminate', methods=['POST'])
@login_required
def terminate_session(session_id):
    """Terminate a specific user session"""
    print(f"DEBUG: Terminate session called with session_id: {session_id}")
    if not current_user.is_admin():
        print(f"DEBUG: User {current_user.username} is not admin, level_code: {current_user.level_code}")
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor()
        
        # Deactivate the session
        cur.execute("""
            UPDATE user_sessions 
            SET is_active = FALSE, 
                last_activity = CURRENT_TIMESTAMP 
            WHERE id = %s
            RETURNING user_id, session_token
        """, (session_id,))
        
        result = cur.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Session not found'}), 404
        
        user_id, session_token = result
        conn.commit()
        conn.close()
        
        # Log the administrative action
        log_user_activity(
            user_id=current_user.id,
            activity_type='admin_action',
            description=f'Admin terminated session for user ID: {user_id}',
            additional_data={'terminated_session_id': session_id, 'terminated_session_token': session_token}
        )
        
        return jsonify({
            'success': True,
            'message': 'Session terminated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error terminating session: {str(e)}'}), 500

@app.route('/security')
@login_required
def security_dashboard():
    """Security monitoring dashboard"""
    print(f"DEBUG: Security dashboard accessed by user: {current_user.username if current_user.is_authenticated else 'anonymous'}")
    print(f"DEBUG: User level_code: {current_user.level_code if current_user.is_authenticated else 'none'}")
    print(f"DEBUG: User is_admin(): {current_user.is_admin() if current_user.is_authenticated else 'none'}")
    
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('security_dashboard.html')

@app.route('/api/security/test')
def test_security_api():
    """Test route to verify API routing works"""
    return jsonify({'status': 'success', 'message': 'Security API is working'})

# Performance Monitoring API Endpoints
@app.route('/api/performance/test')
def test_performance_api():
    """Test endpoint for performance API (no auth required)"""
    return jsonify({
        'success': True,
        'message': 'Performance API is working',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/performance/system/current')
@login_required
def get_current_system_metrics():
    """Get current system performance metrics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get latest system metrics
        cur.execute("""
            SELECT * FROM system_performance_history 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        metrics = cur.fetchone()
        
        if metrics:
            return jsonify({
                'success': True,
                'data': dict(metrics)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No system metrics available'
            })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching system metrics: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/performance/system/history')
@login_required
def get_system_metrics_history():
    """Get historical system performance metrics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = min(hours, 168)  # Max 7 days
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        cur.execute("""
            SELECT 
                timestamp,
                cpu_percent,
                memory_percent,
                disk_percent,
                load_average_1m,
                processes_count,
                threads_count
            FROM system_performance_history 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
            ORDER BY timestamp ASC
        """, (hours,))
        
        metrics = cur.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(metric) for metric in metrics],
            'period_hours': hours
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching system history: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/performance/database/current')
@login_required
def get_current_database_metrics():
    """Get current database performance metrics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get latest database metrics
        cur.execute("""
            SELECT * FROM database_performance_history 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        metrics = cur.fetchone()
        
        if metrics:
            return jsonify({
                'success': True,
                'data': dict(metrics)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No database metrics available'
            })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching database metrics: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/performance/database/history')
@login_required
def get_database_metrics_history():
    """Get historical database performance metrics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = min(hours, 168)  # Max 7 days
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        cur.execute("""
            SELECT 
                timestamp,
                active_connections,
                max_connections,
                cache_hit_ratio,
                database_size,
                active_locks,
                waiting_locks,
                slow_queries
            FROM database_performance_history 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
            ORDER BY timestamp ASC
        """, (hours,))
        
        metrics = cur.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(metric) for metric in metrics],
            'period_hours': hours
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching database history: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/performance/containers/current')
@login_required
def get_current_container_metrics():
    """Get current container health metrics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get latest metrics for each container
        cur.execute("""
            SELECT DISTINCT ON (container_name)
                container_name,
                timestamp,
                status,
                health_status,
                cpu_percent,
                memory_percent,
                restart_count,
                uptime_seconds,
                memory_usage,
                memory_limit
            FROM container_health_history 
            ORDER BY container_name, timestamp DESC
        """)
        
        containers = cur.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(container) for container in containers]
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching container metrics: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/performance/containers/history')
@login_required
def get_container_metrics_history():
    """Get historical container performance metrics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        container_name = request.args.get('container')
        hours = min(hours, 168)  # Max 7 days
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        if container_name:
            cur.execute("""
                SELECT 
                    timestamp,
                    container_name,
                    status,
                    cpu_percent,
                    memory_percent,
                    restart_count,
                    uptime_seconds
                FROM container_health_history 
                WHERE container_name = %s 
                  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
                ORDER BY timestamp ASC
            """, (container_name, hours))
        else:
            cur.execute("""
                SELECT 
                    timestamp,
                    container_name,
                    status,
                    cpu_percent,
                    memory_percent,
                    restart_count,
                    uptime_seconds
                FROM container_health_history 
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
                ORDER BY timestamp ASC
            """, (hours,))
        
        metrics = cur.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(metric) for metric in metrics],
            'period_hours': hours,
            'container_name': container_name
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching container history: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/performance/alerts')
@login_required
def get_performance_alerts():
    """Get system performance alerts"""
    try:
        status = request.args.get('status', 'active')
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        if status == 'all':
            cur.execute("""
                SELECT * FROM system_alerts 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
        else:
            cur.execute("""
                SELECT * FROM system_alerts 
                WHERE status = %s
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (status, limit))
        
        alerts = cur.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(alert) for alert in alerts],
            'status_filter': status,
            'count': len(alerts)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching alerts: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/performance/slow-queries')
@login_required
def get_slow_queries():
    """Get slow query log"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = min(request.args.get('limit', 50, type=int), 100)
        hours = min(hours, 168)  # Max 7 days
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        cur.execute("""
            SELECT 
                timestamp,
                query_text,
                execution_time_ms,
                database_name,
                user_name,
                rows_examined,
                rows_sent,
                query_type
            FROM slow_query_log 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
            ORDER BY execution_time_ms DESC 
            LIMIT %s
        """, (hours, limit))
        
        queries = cur.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(query) for query in queries],
            'period_hours': hours,
            'count': len(queries)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching slow queries: {str(e)}'}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/crypto/backtest')
@login_required
def crypto_backtest():
    """Cryptocurrency investment strategy backtesting page"""
    start_time = datetime.now()
    
    try:
        # For now, render a placeholder template
        return render_template('crypto_backtest.html', 
                             page_title="Crypto Investment Strategy Backtesting")
    
    except Exception as e:
        flash(f'Error loading backtesting page: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        log_user_activity(
            user_id=current_user.id if current_user.is_authenticated else None,
            activity_type='page_view',
            description='Viewed crypto backtesting page',
            duration_ms=duration_ms
        )

@app.route('/api-test')
def api_test():
    """Simple API test page"""
    return render_template('api_test.html')

@app.route('/api/performance/database/health')
@login_required
def get_database_health():
    """Get detailed database health metrics including index usage and dead tuples"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get table statistics with dead tuples
        cur.execute("""
            SELECT 
                schemaname,
                relname as table_name,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples,
                ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_tuple_ratio,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY n_dead_tup DESC 
            LIMIT 20
        """)
        table_stats = cur.fetchall()
        
        # Get index usage statistics
        cur.execute("""
            SELECT 
                schemaname,
                relname as tablename,
                indexrelname as indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
            LIMIT 20
        """)
        index_stats = cur.fetchall()
        
        # Get query performance stats
        cur.execute("""
            SELECT 
                datname as database,
                numbackends as active_connections,
                xact_commit as commits,
                xact_rollback as rollbacks,
                blks_read as blocks_read,
                blks_hit as blocks_hit,
                ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_ratio,
                tup_returned as tuples_returned,
                tup_fetched as tuples_fetched,
                tup_inserted as tuples_inserted,
                tup_updated as tuples_updated,
                tup_deleted as tuples_deleted
            FROM pg_stat_database
            WHERE datname = 'webapp_db'
        """)
        query_stats = cur.fetchone()
        
        # Get crypto-specific metrics (highly optimized - <1 second)
        # Use cryptocurrencies master table for dynamic count
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM cryptocurrencies WHERE is_active = true) as total_cryptos,
                COALESCE((SELECT reltuples::bigint FROM pg_class WHERE relname = 'crypto_prices'), 0) as total_price_records,
                (SELECT datetime FROM crypto_prices ORDER BY datetime DESC LIMIT 1) as latest_data,
                0 as recent_records_24h
        """)
        crypto_prices = cur.fetchone()
        
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM cryptocurrencies WHERE is_active = true) as cryptos_with_indicators,
                COALESCE((SELECT reltuples::bigint FROM pg_class WHERE relname = 'crypto_technical_indicators'), 0) as total_indicator_records,
                (SELECT datetime FROM crypto_technical_indicators ORDER BY datetime DESC LIMIT 1) as latest_indicator,
                0 as recent_indicators_24h
        """)
        crypto_indicators = cur.fetchone()
        
        # Get stock data metrics (optimized)
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM stocks) as total_stocks,
                COALESCE((SELECT reltuples::bigint FROM pg_class WHERE relname = 'stock_prices'), 0) as total_price_records,
                (SELECT datetime FROM stock_prices ORDER BY datetime DESC LIMIT 1) as latest_data,
                0 as recent_records_24h
        """)
        stock_stats = cur.fetchone()
        
        # Get weather data metrics
        cur.execute("""
            SELECT 
                COUNT(*) as total_historic_records,
                COUNT(DISTINCT weather_location_id) as locations,
                MAX(date) as latest_data
            FROM historic_weather_data
        """)
        weather_historic = cur.fetchone()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_current_records,
                MAX(recorded_at) as latest_data,
                COUNT(*) FILTER (WHERE recorded_at > NOW() - INTERVAL '1 hour') as recent_records_1h
            FROM current_weather_data
        """)
        weather_current = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'table_stats': [dict(row) for row in table_stats],
                'index_stats': [dict(row) for row in index_stats],
                'query_stats': dict(query_stats) if query_stats else {},
                'crypto_prices': dict(crypto_prices) if crypto_prices else {},
                'crypto_indicators': dict(crypto_indicators) if crypto_indicators else {},
                'stock_stats': dict(stock_stats) if stock_stats else {},
                'weather_historic': dict(weather_historic) if weather_historic else {},
                'weather_current': dict(weather_current) if weather_current else {}
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching database health: {str(e)}")
        return jsonify({'error': f'Error fetching database health: {str(e)}'}), 500


# =============================================================================
# TRAVEL PLANNER ROUTES
# =============================================================================

@app.route('/travel')
@login_required
def travel_list():
    """List all trips for the current user"""
    try:
        # Get filter parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Call API to get trips
        api_url = f'http://api:8000/api/travel/trips?limit={limit}&offset={offset}'
        if status:
            api_url += f'&status={status}'
        
        response = requests.get(api_url, cookies={'user_id': str(current_user.id)})
        
        if response.status_code == 200:
            data = response.json()
            trips = data.get('trips', [])
            total = data.get('total', 0)
            
            # Calculate duration for each trip
            for trip in trips:
                if trip.get('start_date') and trip.get('end_date'):
                    from datetime import datetime
                    start = datetime.fromisoformat(trip['start_date'])
                    end = datetime.fromisoformat(trip['end_date'])
                    trip['duration_days'] = (end - start).days + 1
            
            return render_template('travel/trip_list.html', 
                                 trips=trips, 
                                 total=total, 
                                 limit=limit, 
                                 offset=offset)
        else:
            flash('Error loading trips', 'danger')
            return render_template('travel/trip_list.html', trips=[], total=0, limit=limit, offset=offset)
            
    except Exception as e:
        app.logger.error(f"Error loading trips: {str(e)}")
        flash('Error loading trips', 'danger')
        return render_template('travel/trip_list.html', trips=[], total=0, limit=50, offset=0)


@app.route('/travel/create', methods=['GET', 'POST'])
@login_required
def travel_create():
    """Create a new trip"""
    return render_template('travel/trip_create.html')


@app.route('/travel/trips/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    """View trip details"""
    try:
        # Get trip from API
        response = requests.get(
            f'http://api:8000/api/travel/trips/{trip_id}',
            cookies={'user_id': str(current_user.id)}
        )
        
        if response.status_code == 200:
            data = response.json()
            trip = data.get('trip')
            
            if trip:
                # Calculate duration
                if trip.get('start_date') and trip.get('end_date'):
                    from datetime import datetime
                    start = datetime.fromisoformat(trip['start_date'])
                    end = datetime.fromisoformat(trip['end_date'])
                    trip['duration_days'] = (end - start).days + 1
                
                return render_template('travel/trip_detail.html', trip=trip)
        
        flash('Trip not found', 'danger')
        return redirect(url_for('travel_list'))
        
    except Exception as e:
        app.logger.error(f"Error loading trip: {str(e)}")
        flash('Error loading trip', 'danger')
        return redirect(url_for('travel_list'))


@app.route('/travel/trips/<int:trip_id>/edit', methods=['GET', 'POST'])
@login_required
def trip_edit(trip_id):
    """Edit a trip"""
    if request.method == 'GET':
        try:
            # Get trip from API
            response = requests.get(
                f'http://api:8000/api/travel/trips/{trip_id}',
                cookies={'user_id': str(current_user.id)}
            )
            
            if response.status_code == 200:
                data = response.json()
                trip = data.get('trip')
                
                if trip:
                    return render_template('travel/trip_edit.html', trip=trip)
            
            flash('Trip not found', 'danger')
            return redirect(url_for('travel_list'))
            
        except Exception as e:
            app.logger.error(f"Error loading trip for edit: {str(e)}")
            flash('Error loading trip', 'danger')
            return redirect(url_for('travel_list'))
    
    # POST request handled by JavaScript/API


@app.route('/travel/trips/<int:trip_id>/calendar/export')
@login_required
def export_calendar(trip_id):
    """Export trip to calendar .ics file"""
    try:
        # Proxy to API
        response = requests.get(
            f'http://api:8000/api/travel/trips/{trip_id}/export/calendar',
            cookies={'user_id': str(current_user.id)}
        )
        
        if response.status_code == 200:
            # Return the .ics file
            ics_response = make_response(response.content)
            ics_response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
            ics_response.headers['Content-Disposition'] = f'attachment; filename="trip_{trip_id}.ics"'
            return ics_response
        else:
            flash('Error exporting calendar', 'danger')
            return redirect(url_for('trip_detail', trip_id=trip_id))
            
    except Exception as e:
        app.logger.error(f"Error exporting calendar: {str(e)}")
        flash('Error exporting calendar', 'danger')
        return redirect(url_for('trip_detail', trip_id=trip_id))


# API Proxy Routes for AJAX calls
@app.route('/api/travel/trips', methods=['GET', 'POST'])
@login_required
def api_trips():
    """Proxy trips API endpoint"""
    try:
        if request.method == 'GET':
            response = requests.get(
                'http://api:8000/api/travel/trips',
                params=request.args,
                cookies={'user_id': str(current_user.id)}
            )
        else:  # POST
            response = requests.post(
                'http://api:8000/api/travel/trips',
                json=request.get_json(),
                cookies={'user_id': str(current_user.id)}
            )
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying trips API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_trip_detail(trip_id):
    """Proxy trip detail API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}'
        
        if request.method == 'GET':
            response = requests.get(url, cookies={'user_id': str(current_user.id)})
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        else:  # DELETE
            response = requests.delete(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying trip detail API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/activities', methods=['GET', 'POST'])
@login_required
def api_activities(trip_id):
    """Proxy activities API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/activities'
        
        if request.method == 'GET':
            response = requests.get(url, cookies={'user_id': str(current_user.id)})
        else:  # POST
            response = requests.post(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying activities API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/activities/<int:activity_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_activity_detail(trip_id, activity_id):
    """Proxy activity detail API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/activities/{activity_id}'
        
        if request.method == 'GET':
            response = requests.get(url, cookies={'user_id': str(current_user.id)})
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        else:  # DELETE
            response = requests.delete(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying activity detail API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/accommodations', methods=['GET', 'POST'])
@login_required
def api_accommodations(trip_id):
    """Proxy accommodations API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/accommodations'
        
        if request.method == 'GET':
            response = requests.get(url, cookies={'user_id': str(current_user.id)})
        else:  # POST
            response = requests.post(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying accommodations API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/accommodations/<int:accommodation_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_accommodation_detail(trip_id, accommodation_id):
    """Proxy accommodation detail API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/accommodations/{accommodation_id}'
        
        if request.method == 'GET':
            response = requests.get(url, cookies={'user_id': str(current_user.id)})
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        else:  # DELETE
            response = requests.delete(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying accommodation detail API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Expenses API proxy
@app.route('/api/travel/trips/<int:trip_id>/expenses', methods=['GET', 'POST'])
@login_required
def api_expenses(trip_id):
    """Proxy expenses API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/expenses'
        
        if request.method == 'GET':
            response = requests.get(url, cookies={'user_id': str(current_user.id)})
        else:  # POST
            response = requests.post(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying expenses API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/expenses/<int:expense_id>', methods=['PUT', 'DELETE'])
@login_required
def api_expense_detail(expense_id):
    """Proxy expense detail API endpoint"""
    try:
        url = f'http://api:8000/api/travel/expenses/{expense_id}'
        
        if request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        else:  # DELETE
            response = requests.delete(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying expense detail API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Packing List API proxy
@app.route('/api/travel/trips/<int:trip_id>/packing', methods=['GET', 'POST'])
@login_required
def api_packing(trip_id):
    """Proxy packing list API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/packing'
        
        if request.method == 'GET':
            response = requests.get(url, cookies={'user_id': str(current_user.id)})
        else:  # POST
            response = requests.post(url, json=request.get_json(), cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying packing API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/packing/<int:item_id>/toggle', methods=['POST'])
@login_required
def api_packing_toggle(item_id):
    """Proxy packing item toggle API endpoint"""
    try:
        url = f'http://api:8000/api/travel/packing/{item_id}/toggle'
        response = requests.post(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying packing toggle API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== TRIP SHARING API PROXY ROUTES ====================

@app.route('/api/travel/trips/<int:trip_id>/shares', methods=['GET'])
@login_required
def api_get_trip_shares(trip_id):
    """Proxy get trip shares API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/shares'
        response = requests.get(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying get trip shares API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/shares', methods=['POST'])
@login_required
def api_share_trip(trip_id):
    """Proxy share trip API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/shares'
        response = requests.post(
            url,
            json=request.get_json(),
            cookies={'user_id': str(current_user.id)}
        )
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying share trip API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/shares/<int:share_id>', methods=['PUT'])
@login_required
def api_update_trip_share(trip_id, share_id):
    """Proxy update trip share permissions API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/shares/{share_id}'
        response = requests.put(
            url,
            json=request.get_json(),
            cookies={'user_id': str(current_user.id)}
        )
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying update trip share API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/shares/<int:share_id>', methods=['DELETE'])
@login_required
def api_delete_trip_share(trip_id, share_id):
    """Proxy delete trip share API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/shares/{share_id}'
        response = requests.delete(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying delete trip share API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/trips/<int:trip_id>/permissions', methods=['GET'])
@login_required
def api_get_trip_permissions(trip_id):
    """Proxy get trip permissions API endpoint"""
    try:
        url = f'http://api:8000/api/travel/trips/{trip_id}/permissions'
        response = requests.get(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying get trip permissions API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/travel/users/search', methods=['GET'])
@login_required
def api_search_users():
    """Proxy search users API endpoint"""
    try:
        query = request.args.get('q', '')
        url = f'http://api:8000/api/travel/users/search?q={query}'
        response = requests.get(url, cookies={'user_id': str(current_user.id)})
        
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        app.logger.error(f"Error proxying search users API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Custom Jinja2 filters for travel templates
@app.template_filter('format_date')
def format_date(date_str):
    """Format date string for display"""
    if not date_str:
        return ''
    try:
        from datetime import datetime
        if isinstance(date_str, str):
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = date_str
        return date_obj.strftime('%b %d, %Y')
    except:
        return date_str


if __name__ == '__main__':
    @app.route('/api/test')
    def test_api():
        return jsonify({'message': 'API is working'})
    
    app.run(host='0.0.0.0', port=5000, debug=True)
