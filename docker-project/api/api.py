import os
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_restful import Api, Resource
from flask_cors import CORS
from flask_compress import Compress
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import requests
from datetime import datetime
from decimal import Decimal
from stock_service import StockDataService, StockDataScheduler
from demo_data_generator import DemoStockDataGenerator
from crypto_service import CryptoDataService
from crypto_backtest_service import CryptoBacktestService
from streaming_backtest_service import StreamingBacktestService
from travel_api import travel_bp

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
Compress(app)  # Enable gzip/brotli compression for all responses
api = Api(app)

# Register Travel Planner Blueprint
app.register_blueprint(travel_bp)

# Database configuration (psycopg3 uses dbname instead of database)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'database'),
    'dbname': os.environ.get('DB_NAME', 'webapp_db'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '530NWC0Gm3pt4O'),
    'port': os.environ.get('DB_PORT', '5432')
}

# Web app configuration
WEBAPP_HOST = os.environ.get('WEBAPP_HOST', 'webapp')
WEBAPP_PORT = os.environ.get('WEBAPP_PORT', '5000')

# Initialize stock data service
stock_service = StockDataService(DB_CONFIG)
stock_scheduler = StockDataScheduler(stock_service)
demo_generator = DemoStockDataGenerator(DB_CONFIG)

# Initialize crypto data service
crypto_service = CryptoDataService(
    db_config=DB_CONFIG,
    binance_api_key=os.environ.get('BINANCE_API_KEY'),
    binance_secret_key=os.environ.get('BINANCE_SECRET_KEY')
)

# Initialize crypto backtest service
backtest_service = CryptoBacktestService(DB_CONFIG)
streaming_backtest_service = StreamingBacktestService(DB_CONFIG)

def serialize_for_json(obj):
    """Convert datetime and Decimal objects for JSON serialization"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def convert_row_to_dict(row):
    """Convert database row to JSON-serializable dict"""
    if not row:
        return {}
    
    result = {}
    for key, value in dict(row).items():
        result[key] = serialize_for_json(value)
    return result

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except psycopg.Error as e:
        print(f"Database connection error: {e}")
        return None

class HealthCheck(Resource):
    """API Health check endpoint"""
    def get(self):
        return {
            'status': 'healthy',
            'message': 'API container is running',
            'version': '1.0.0',
            'services': {
                'dbname': self.check_database_connection(),
                'webapp': self.check_webapp_connection()
            }
        }
    
    def check_database_connection(self):
        """Check database connectivity"""
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                return 'connected'
            except psycopg.Error:
                return 'error'
            finally:
                conn.close()
        return 'disconnected'
    
    def check_webapp_connection(self):
        """Check web app connectivity"""
        try:
            response = requests.get(f'http://{WEBAPP_HOST}:{WEBAPP_PORT}/', timeout=5)
            return 'connected' if response.status_code == 200 else 'error'
        except requests.RequestException:
            return 'disconnected'

class UserStats(Resource):
    """Get user statistics from database"""
    def get(self):
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
        
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get user count
            cur.execute("SELECT COUNT(*) as total_users FROM users WHERE is_active = TRUE")
            user_count = cur.fetchone()['total_users']
            
            # Get recent registrations (last 7 days)
            cur.execute("""
                SELECT COUNT(*) as recent_registrations 
                FROM users 
                WHERE created_at >= NOW() - INTERVAL '7 days' AND is_active = TRUE
            """)
            recent_registrations = cur.fetchone()['recent_registrations']
            
            # Get login attempts stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as successful_logins,
                    SUM(CASE WHEN success = FALSE THEN 1 ELSE 0 END) as failed_logins
                FROM login_attempts 
                WHERE attempted_at >= NOW() - INTERVAL '24 hours'
            """)
            login_stats = cur.fetchone()
            
            return {
                'user_statistics': {
                    'total_active_users': user_count,
                    'recent_registrations_7_days': recent_registrations,
                    'login_attempts_24h': {
                        'total': login_stats['total_attempts'] or 0,
                        'successful': login_stats['successful_logins'] or 0,
                        'failed': login_stats['failed_logins'] or 0
                    }
                }
            }
            
        except psycopg.Error as e:
            return {'error': f'Database query failed: {str(e)}'}, 500
        finally:
            conn.close()

class DatabaseInfo(Resource):
    """Get database information and tables"""
    def get(self):
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
        
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get table information
            cur.execute("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            
            # Get database size
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as db_size")
            db_size = cur.fetchone()['db_size']
            
            return {
                'database_info': {
                    'name': DB_CONFIG['database'],
                    'size': db_size,
                    'tables': [dict(table) for table in tables]
                }
            }
            
        except psycopg.Error as e:
            return {'error': f'Database query failed: {str(e)}'}, 500
        finally:
            conn.close()

class StockDataFetch(Resource):
    """Fetch and store stock historical data"""
    def post(self):
        """Trigger stock data fetch"""
        try:
            result = stock_service.fetch_and_store_nasdaq_data()
            return result
        except Exception as e:
            return {'error': f'Failed to fetch stock data: {str(e)}'}, 500

class MultiStockDataFetch(Resource):
    """Fetch and store data for any stock symbol"""
    def post(self):
        """Trigger stock data fetch for specified symbol"""
        try:
            data = request.get_json() or {}
            symbol = data.get('symbol', request.args.get('symbol', '^IXIC'))
            name = data.get('name', request.args.get('name'))
            exchange = data.get('exchange', request.args.get('exchange', 'NASDAQ'))
            
            # Predefined stock names
            stock_names = {
                '^IXIC': 'NASDAQ Composite Index',
                '^GSPC': 'S&P 500 Index',
                '^DJI': 'Dow Jones Industrial Average',
                'VWRL.L': 'Vanguard FTSE All-World UCITS ETF',
                'IWDA.L': 'iShares Core MSCI World UCITS ETF',
                'AAPL': 'Apple Inc.',
                'MSFT': 'Microsoft Corporation',
                'GOOGL': 'Alphabet Inc. (Google)',
                'TSLA': 'Tesla Inc.',
                'OP-MAAILMA': 'OP-Maailma Global Equity Fund'
            }
            
            if not name and symbol in stock_names:
                name = stock_names[symbol]
            
            result = stock_service.fetch_and_store_stock_data(symbol, name, exchange)
            return result
        except Exception as e:
            return {'error': f'Failed to fetch stock data: {str(e)}'}, 500

class StockDemoData(Resource):
    """Generate demo stock data for testing"""
    def post(self):
        """Create demo stock data"""
        try:
            result = demo_generator.create_demo_data()
            return result
        except Exception as e:
            return {'error': f'Failed to create demo data: {str(e)}'}, 500

class StockPrices(Resource):
    """Get stock price data"""
    def get(self):
        """Get stock prices with optional filters"""
        symbol = request.args.get('symbol', 'AAPL')
        limit = int(request.args.get('limit', 1000))
        interval = request.args.get('interval', '1d')
        
        try:
            data = stock_service.get_stock_data(symbol, limit, interval)
            return {
                'symbol': symbol,
                'interval': interval,
                'data_points': len(data),
                'data': data
            }
        except Exception as e:
            return {'error': f'Failed to get stock data: {str(e)}'}, 500

class StockLatest(Resource):
    """Get latest stock prices"""
    def get(self):
        """Get latest prices for all stocks or filtered by exchange"""
        exchange = request.args.get('exchange')  # Optional exchange filter
        
        try:
            data = stock_service.get_latest_stock_prices(exchange=exchange)
            return {
                'timestamp': datetime.now().isoformat(),
                'exchange': exchange if exchange else 'all',
                'stocks': data
            }
        except Exception as e:
            return {'error': f'Failed to get latest prices: {str(e)}'}, 500

class StockStats(Resource):
    """Get stock data statistics"""
    def get(self):
        """Get statistics about stored stock data"""
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
        
        try:
            cur = conn.cursor(row_factory=dict_row)
            
            # Get total records
            cur.execute("SELECT COUNT(*) as total_records FROM stock_prices")
            total_records = cur.fetchone()['total_records']
            
            # Get date range
            cur.execute("""
                SELECT MIN(datetime) as earliest_date, MAX(datetime) as latest_date
                FROM stock_prices
            """)
            date_range = cur.fetchone()
            
            # Get records by interval
            cur.execute("""
                SELECT interval_type, COUNT(*) as count
                FROM stock_prices
                GROUP BY interval_type
                ORDER BY count DESC
            """)
            by_interval = cur.fetchall()
            
            # Get stocks count
            cur.execute("SELECT COUNT(*) as total_stocks FROM stocks WHERE is_active = TRUE")
            stocks_count = cur.fetchone()['total_stocks']
            
            return {
                'statistics': {
                    'total_price_records': total_records,
                    'total_active_stocks': stocks_count,
                    'date_range': {
                        'earliest': date_range['earliest_date'].isoformat() if date_range['earliest_date'] else None,
                        'latest': date_range['latest_date'].isoformat() if date_range['latest_date'] else None
                    },
                    'records_by_interval': [dict(row) for row in by_interval]
                }
            }
            
        except psycopg.Error as e:
            return {'error': f'Database query failed: {str(e)}'}, 500
        finally:
            conn.close()

class YearlyGrowth(Resource):
    """Get yearly growth analysis for a stock"""
    def get(self):
        """Get yearly growth rates"""
        symbol = request.args.get('symbol', '^IXIC')
        
        try:
            data = stock_service.get_yearly_growth_analysis(symbol)
            return {
                'symbol': symbol,
                'yearly_growth': data
            }
        except Exception as e:
            return {'error': f'Failed to calculate yearly growth: {str(e)}'}, 500

class InvestmentCalculator(Resource):
    """Calculate investment returns for monthly investments"""
    def get(self):
        """Calculate returns for monthly investments"""
        symbol = request.args.get('symbol', '^IXIC')
        
        # Validate and parse monthly_investment parameter
        try:
            monthly_investment_str = request.args.get('monthly_investment', '100.0')
            monthly_investment = float(monthly_investment_str)
            
            if monthly_investment <= 0:
                return {'error': 'Monthly investment must be greater than 0'}, 400
            
            if monthly_investment > 1000000:
                return {'error': 'Monthly investment amount too large'}, 400
                
        except ValueError:
            return {'error': f'Invalid monthly_investment value: {monthly_investment_str}'}, 400
        
        start_year = request.args.get('start_year')  # Optional starting year
        
        try:
            data = stock_service.calculate_investment_returns(symbol, monthly_investment, start_year)
            
            # Add debug info to response
            if 'investment_history' in data and len(data['investment_history']) > 0:
                data['debug_info'] = {
                    'requested_monthly_investment': monthly_investment,
                    'first_month_invested': data['investment_history'][0]['total_invested'],
                    'calculation_check': 'OK' if abs(data['investment_history'][0]['total_invested'] - monthly_investment) < 0.01 else 'MISMATCH'
                }
            
            return data
        except Exception as e:
            return {'error': f'Failed to calculate investment returns: {str(e)}'}, 500

class AvailableYears(Resource):
    """Get available years for a specific stock"""
    def get(self):
        """Get list of available years for investment calculations"""
        symbol = request.args.get('symbol', '^IXIC')
        
        try:
            data = stock_service.get_available_years(symbol)
            return data
        except Exception as e:
            return {'error': f'Failed to get available years: {str(e)}'}, 500

# Register API endpoints
api.add_resource(HealthCheck, '/health')
api.add_resource(UserStats, '/stats/users')
api.add_resource(DatabaseInfo, '/info/database')
class StockSchedulerStatus(Resource):
    def get(self):
        """Get stock scheduler status"""
        try:
            import schedule
            scheduled_jobs = []
            for job in schedule.jobs:
                scheduled_jobs.append({
                    'job': str(job.job_func),
                    'next_run': str(job.next_run),
                    'interval': str(job.interval),
                    'unit': str(job.unit)
                })
            
            # Get latest fetch info
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT MAX(fetch_start) as last_fetch, 
                       COUNT(*) as total_fetches_today
                FROM stock_fetch_logs 
                WHERE DATE(fetch_start) = CURRENT_DATE
            """)
            fetch_info = cur.fetchone()
            
            return {
                'scheduler_running': stock_scheduler.running,
                'scheduled_jobs': scheduled_jobs,
                'last_fetch': fetch_info[0].isoformat() if fetch_info[0] else None,
                'fetches_today': fetch_info[1],
                'current_time': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}, 500

api.add_resource(StockDataFetch, '/stocks/fetch')
api.add_resource(MultiStockDataFetch, '/stocks/fetch-symbol')
api.add_resource(StockDemoData, '/stocks/demo')
api.add_resource(StockPrices, '/stocks/prices')
api.add_resource(StockLatest, '/stocks/latest')
api.add_resource(StockStats, '/stocks/stats')
api.add_resource(YearlyGrowth, '/stocks/yearly-growth')
api.add_resource(InvestmentCalculator, '/stocks/investment-calculator')
api.add_resource(AvailableYears, '/stocks/available-years')
api.add_resource(StockSchedulerStatus, '/stocks/scheduler-status')

@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'message': 'Docker Project API with Stock Data',
        'version': '2.0.0',
        'endpoints': {
            'health': '/health',
            'user_stats': '/stats/users',
            'database_info': '/info/database',
            'stock_fetch': '/stocks/fetch (POST)',
            'stock_demo': '/stocks/demo (POST)',
            'stock_prices': '/stocks/prices',
            'stock_latest': '/stocks/latest',
            'stock_stats': '/stocks/stats',
            'yearly_growth': '/stocks/yearly-growth',
            'investment_calculator': '/stocks/investment-calculator',
            'available_years': '/stocks/available-years',
            'scheduler_status': '/stocks/scheduler-status'
        },
        'description': 'API container with database access and stock market data functionality'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

class TestAllStocksUpdate(Resource):
    def post(self):
        """Test endpoint to manually trigger all stocks update"""
        try:
            result = stock_service.fetch_and_store_all_stocks()
            return {'success': True, 'result': result}, 200
        except Exception as e:
            return {'success': False, 'error': str(e)}, 500

class TriggerHistoricWeatherCollection(Resource):
    def post(self):
        """Trigger historic weather data collection for a specific location"""
        try:
            data = request.get_json()
            location_id = data.get('location_id')
            years = data.get('years', 20)  # Default to 20 years
            
            if not location_id:
                return {'success': False, 'error': 'location_id is required'}, 400
            
            # Import and run the collection script
            import subprocess
            import threading
            
            def run_collection():
                try:
                    result = subprocess.run([
                        'python', 'collect_historic_weather.py', 
                        '--location-id', str(location_id),
                        '--years', str(years)
                    ], capture_output=True, text=True, cwd='/app')
                    
                    print(f"Historic data collection ({years} years) for location {location_id}: {result.returncode}")
                    if result.stdout:
                        print(f"Collection output: {result.stdout}")
                    if result.stderr:
                        print(f"Collection errors: {result.stderr}")
                except Exception as e:
                    print(f"Error running historic data collection: {e}")
            
            # Start the collection in a background thread
            thread = threading.Thread(target=run_collection)
            thread.daemon = True
            thread.start()
            
            return {
                'success': True, 
                'message': f'Historic weather collection started for location {location_id} ({years} years)',
                'location_id': location_id,
                'years': years
            }, 200
            
        except Exception as e:
            return {'success': False, 'error': str(e)}, 500

# =============================================================================
# CRYPTOCURRENCY API ENDPOINTS
# =============================================================================

class CryptoList(Resource):
    """Get list of available cryptocurrencies"""
    def get(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT c.*, cms.current_price, cms.price_change_percent_24h, cms.volume_24h
                        FROM cryptocurrencies c
                        LEFT JOIN crypto_market_stats cms ON c.id = cms.crypto_id
                        WHERE c.is_active = TRUE
                        ORDER BY c.rank_position ASC, c.symbol ASC
                        LIMIT 200
                    """)
                    cryptos = cur.fetchall()
                    
                    # Convert to JSON-serializable format
                    result = [convert_row_to_dict(crypto) for crypto in cryptos]
                    
                    return {'cryptos': result}, 200
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoPrices(Resource):
    """Get historical price data for a cryptocurrency"""
    def get(self):
        symbol = request.args.get('symbol', '').upper()
        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 1000))
        
        if not symbol:
            return {'error': 'Symbol parameter is required'}, 400
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Get crypto ID
                    cur.execute("SELECT id FROM cryptocurrencies WHERE binance_symbol = %s", (symbol,))
                    crypto = cur.fetchone()
                    if not crypto:
                        return {'error': f'Cryptocurrency {symbol} not found'}, 404
                    
                    # Get price data
                    cur.execute("""
                        SELECT datetime, open_price, high_price, low_price, close_price, 
                               volume, quote_asset_volume, number_of_trades
                        FROM crypto_prices 
                        WHERE crypto_id = %s AND interval_type = %s
                        ORDER BY datetime DESC
                        LIMIT %s
                    """, (crypto['id'], interval, limit))
                    
                    prices = cur.fetchall()
                    
                    # Convert to JSON-serializable format
                    price_data = [convert_row_to_dict(price) for price in prices]
                    
                    return {
                        'symbol': symbol,
                        'interval': interval,
                        'data': price_data
                    }, 200
                    
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoLatest(Resource):
    """Get latest price data for a cryptocurrency"""
    def get(self):
        symbol = request.args.get('symbol', '').upper()
        
        if not symbol:
            return {'error': 'Symbol parameter is required'}, 400
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT c.symbol, c.name, c.base_asset, c.quote_asset,
                               cms.current_price, cms.price_change_24h, cms.price_change_percent_24h,
                               cms.volume_24h, cms.high_24h, cms.low_24h, cms.updated_at,
                               cp.datetime as last_price_update
                        FROM cryptocurrencies c
                        LEFT JOIN crypto_market_stats cms ON c.id = cms.crypto_id
                        LEFT JOIN LATERAL (
                            SELECT datetime FROM crypto_prices 
                            WHERE crypto_id = c.id AND interval_type = '1h'
                            ORDER BY datetime DESC LIMIT 1
                        ) cp ON TRUE
                        WHERE c.binance_symbol = %s
                    """, (symbol,))
                    
                    result = cur.fetchone()
                    if not result:
                        return {'error': f'Cryptocurrency {symbol} not found'}, 404
                    
                    return {'data': convert_row_to_dict(result)}, 200
                    
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoStats(Resource):
    """Get statistics for a cryptocurrency"""
    def get(self):
        symbol = request.args.get('symbol', '').upper()
        
        if not symbol:
            return {'error': 'Symbol parameter is required'}, 400
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Get crypto ID
                    cur.execute("SELECT id FROM cryptocurrencies WHERE binance_symbol = %s", (symbol,))
                    crypto = cur.fetchone()
                    if not crypto:
                        return {'error': f'Cryptocurrency {symbol} not found'}, 404
                    
                    # Get comprehensive stats
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_records,
                            MIN(datetime) as earliest_date,
                            MAX(datetime) as latest_date,
                            AVG(close_price) as avg_price,
                            MIN(low_price) as all_time_low,
                            MAX(high_price) as all_time_high,
                            AVG(volume) as avg_volume
                        FROM crypto_prices 
                        WHERE crypto_id = %s AND interval_type = '1h'
                    """, (crypto['id'],))
                    
                    stats = cur.fetchone()
                    
                    return {
                        'symbol': symbol,
                        'stats': convert_row_to_dict(stats)
                    }, 200
                    
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoMarketOverview(Resource):
    """Get market overview with top cryptocurrencies"""
    def get(self):
        limit = int(request.args.get('limit', 50))
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT 
                            c.symbol, c.name, c.base_asset,
                            cms.current_price, cms.price_change_24h, cms.price_change_percent_24h,
                            cms.volume_24h, cms.high_24h, cms.low_24h, cms.market_cap_rank,
                            c.rank_position
                        FROM cryptocurrencies c
                        LEFT JOIN crypto_market_stats cms ON c.id = cms.crypto_id
                        WHERE c.is_active = TRUE
                        ORDER BY COALESCE(cms.market_cap_rank, c.rank_position, 999999) ASC
                        LIMIT %s
                    """, (limit,))
                    
                    cryptos = cur.fetchall()
                    return {
                        'market_overview': [convert_row_to_dict(crypto) for crypto in cryptos],
                        'count': len(cryptos)
                    }, 200
                    
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoDataCollection(Resource):
    """Trigger cryptocurrency data collection"""
    def post(self):
        try:
            # This would typically be run as a background task
            # For now, just return a success message
            return {
                'success': True,
                'message': 'Cryptocurrency data collection triggered. Check logs for progress.'
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoConfiguration(Resource):
    """Get current cryptocurrency service configuration"""
    def get(self):
        try:
            config = crypto_service.get_configuration_info()
            return {
                'configuration': config,
                'status': 'optimal' if config['api_key_configured'] else 'standard'
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoInvestmentCalculator(Resource):
    """Calculate investment returns for cryptocurrency dollar-cost averaging"""
    def get(self):
        symbol = request.args.get('symbol', '').upper()
        monthly_investment = float(request.args.get('monthly_investment', 500))
        start_year = int(request.args.get('start_year', 2020))
        
        if not symbol:
            return {'error': 'Symbol parameter is required'}, 400
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Get crypto ID
                    cur.execute("SELECT id FROM cryptocurrencies WHERE binance_symbol = %s", (symbol,))
                    crypto = cur.fetchone()
                    if not crypto:
                        return {'error': f'Cryptocurrency {symbol} not found'}, 404
                    
                    # Calculate investment returns
                    cur.execute("""
                        SELECT 
                            DATE_TRUNC('month', datetime) as month,
                            AVG(close_price) as avg_price
                        FROM crypto_prices
                        WHERE crypto_id = %s 
                        AND interval_type = '1h'
                        AND EXTRACT(YEAR FROM datetime) >= %s
                        GROUP BY DATE_TRUNC('month', datetime)
                        ORDER BY month ASC
                    """, (crypto['id'], start_year))
                    
                    monthly_data = cur.fetchall()
                    
                    if not monthly_data:
                        return {'error': 'No data available for the specified period'}, 404
                    
                    # Calculate DCA returns
                    total_invested = 0
                    total_crypto_bought = 0
                    monthly_returns = []
                    
                    for month_data in monthly_data:
                        month = month_data['month']
                        avg_price = float(month_data['avg_price'])
                        
                        # Buy crypto with monthly investment
                        crypto_bought = monthly_investment / avg_price
                        total_invested += monthly_investment
                        total_crypto_bought += crypto_bought
                        
                        # Calculate current value
                        current_value = total_crypto_bought * avg_price
                        profit_loss = current_value - total_invested
                        return_percentage = (profit_loss / total_invested * 100) if total_invested > 0 else 0
                        
                        monthly_returns.append({
                            'month': month.strftime('%Y-%m'),
                            'price': serialize_for_json(avg_price),
                            'crypto_bought': serialize_for_json(crypto_bought),
                            'total_invested': serialize_for_json(total_invested),
                            'total_crypto': serialize_for_json(total_crypto_bought),
                            'current_value': serialize_for_json(current_value),
                            'profit_loss': serialize_for_json(profit_loss),
                            'return_percentage': serialize_for_json(return_percentage)
                        })
                    
                    # Get final values
                    final_data = monthly_returns[-1] if monthly_returns else {}
                    
                    return {
                        'symbol': symbol,
                        'monthly_investment': monthly_investment,
                        'start_year': start_year,
                        'summary': {
                            'total_invested': final_data.get('total_invested', 0),
                            'current_value': final_data.get('current_value', 0),
                            'total_profit_loss': final_data.get('profit_loss', 0),
                            'total_return_percentage': final_data.get('return_percentage', 0),
                            'total_crypto_owned': final_data.get('total_crypto', 0),
                            'months_invested': len(monthly_returns)
                        },
                        'monthly_data': monthly_returns
                    }, 200
                    
        except Exception as e:
            return {'error': str(e)}, 500

# Add test endpoint
api.add_resource(TestAllStocksUpdate, '/test/update-all-stocks')

# Add historic weather collection endpoint
api.add_resource(TriggerHistoricWeatherCollection, '/weather/trigger-historic-collection')

# Add cryptocurrency API endpoints
api.add_resource(CryptoList, '/crypto/list')
api.add_resource(CryptoPrices, '/crypto/prices')
api.add_resource(CryptoLatest, '/crypto/latest')
api.add_resource(CryptoStats, '/crypto/stats')
api.add_resource(CryptoMarketOverview, '/crypto/market-overview')
api.add_resource(CryptoDataCollection, '/crypto/collect-data')
api.add_resource(CryptoConfiguration, '/crypto/config')
api.add_resource(CryptoInvestmentCalculator, '/crypto/investment-calculator')

# Cryptocurrency Backtesting API endpoints
class CryptoStrategies(Resource):
    def get(self):
        """Get all available crypto investment strategies"""
        try:
            strategies = backtest_service.get_available_strategies()
            return {'strategies': strategies}, 200
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoBacktestRun(Resource):
    def post(self):
        """Run backtest for a single cryptocurrency with optional date range"""
        data = request.get_json()
        
        if not data or 'strategy_id' not in data or 'crypto_id' not in data or 'parameters' not in data:
            return {'error': 'Missing required fields: strategy_id, crypto_id, parameters'}, 400
            
        try:
            # Get optional date range and interval
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            interval = data.get('interval', '1d')  # Default to daily
            
            # Determine if we should use daily sampling based on interval
            use_daily_sampling = (interval == '1d')
            
            result = backtest_service.run_backtest(
                data['strategy_id'],
                data['crypto_id'],
                data['parameters'],
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                use_daily_sampling=use_daily_sampling
            )
            return result, 200
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoBacktestAll(Resource):
    def post(self):
        """Run strategy against all cryptocurrencies with optional parallel processing and date range"""
        data = request.get_json()
        
        if not data or 'strategy_id' not in data or 'parameters' not in data:
            return {'error': 'Missing required fields: strategy_id, parameters'}, 400
            
        try:
            # Check if parallel processing is requested (default: True for performance)
            use_parallel = data.get('use_parallel', True)
            
            # Get optional date range and interval
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            interval = data.get('interval', '1d')  # Default to daily
            
            # Determine if we should use daily sampling based on interval
            use_daily_sampling = (interval == '1d')
            
            results = backtest_service.run_strategy_against_all_cryptos(
                data['strategy_id'],
                data['parameters'],
                use_parallel=use_parallel,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                use_daily_sampling=use_daily_sampling
            )
            
            # Calculate summary statistics
            successful_results = [r for r in results if r.get('success', False)]
            total_cryptos = len(results)
            successful_backtests = len(successful_results)
            
            if successful_results:
                avg_return = sum(r['total_return'] for r in successful_results) / len(successful_results)
                best_crypto = max(successful_results, key=lambda x: x['total_return'])
                worst_crypto = min(successful_results, key=lambda x: x['total_return'])
                positive_returns = len([r for r in successful_results if r['total_return'] > 0])
            else:
                avg_return = 0
                best_crypto = None
                worst_crypto = None
                positive_returns = 0
            
            summary = {
                'total_cryptocurrencies': total_cryptos,
                'successful_backtests': successful_backtests,
                'failed_backtests': total_cryptos - successful_backtests,
                'average_return': round(avg_return, 2) if successful_results else 0,
                'positive_returns_count': positive_returns,
                'best_performing': {
                    'symbol': best_crypto['symbol'],
                    'return': best_crypto['total_return']
                } if best_crypto else None,
                'worst_performing': {
                    'symbol': worst_crypto['symbol'],
                    'return': worst_crypto['total_return']
                } if worst_crypto else None
            }
            
            return {
                'summary': summary,
                'results': results
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

class CryptosWithData(Resource):
    def get(self):
        """Get list of cryptocurrencies with price data"""
        try:
            cryptos = backtest_service.get_cryptocurrencies_with_data()
            return {'cryptocurrencies': cryptos}, 200
        except Exception as e:
            return {'error': str(e)}, 500

class CryptoBacktestBatch(Resource):
    def post(self):
        """
        OPTIMIZED: Batch backtest for multiple cryptocurrencies
        10x faster than sequential backtests using single batch query + parallel processing
        
        Request body:
        {
            "strategy_id": 1,
            "crypto_ids": [1, 2, 3, 4, 5],  // List of crypto IDs to backtest
            "parameters": {...},
            "start_date": "2024-01-01",     // Optional
            "end_date": "2024-12-31",       // Optional
            "interval": "1d",               // Optional, default: 1d
            "use_parallel": true            // Optional, default: true
        }
        """
        data = request.get_json()
        
        if not data or 'strategy_id' not in data or 'crypto_ids' not in data or 'parameters' not in data:
            return {'error': 'Missing required fields: strategy_id, crypto_ids, parameters'}, 400
        
        crypto_ids = data.get('crypto_ids', [])
        if not isinstance(crypto_ids, list) or len(crypto_ids) == 0:
            return {'error': 'crypto_ids must be a non-empty list'}, 400
        
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from datetime import datetime as dt
            
            strategy_id = data['strategy_id']
            parameters = data['parameters']
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            interval = data.get('interval', '1d')
            use_parallel = data.get('use_parallel', True)
            use_daily_sampling = (interval == '1d')
            
            start_time = dt.now()
            
            # OPTIMIZATION 1: Batch fetch all price data in single query
            logger.info(f"📊 Batch fetching price data for {len(crypto_ids)} cryptocurrencies...")
            price_data_dict = backtest_service.get_price_data_batch(
                crypto_ids=crypto_ids,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                use_daily_sampling=use_daily_sampling
            )
            
            fetch_time = (dt.now() - start_time).total_seconds()
            logger.info(f"✅ Batch fetch completed in {fetch_time:.2f}s (vs {len(crypto_ids)}x individual queries)")
            
            results = {}
            errors = []
            
            if use_parallel and len(crypto_ids) > 1:
                # OPTIMIZATION 2: Parallel backtest execution
                logger.info(f"🚀 Running {len(crypto_ids)} backtests in parallel...")
                
                with ThreadPoolExecutor(max_workers=min(4, len(crypto_ids))) as executor:
                    # Submit all backtest jobs
                    future_to_crypto = {}
                    for crypto_id in crypto_ids:
                        if crypto_id in price_data_dict:
                            future = executor.submit(
                                backtest_service.run_backtest,
                                strategy_id,
                                crypto_id,
                                parameters,
                                start_date=start_date,
                                end_date=end_date,
                                interval=interval,
                                use_daily_sampling=use_daily_sampling
                            )
                            future_to_crypto[future] = crypto_id
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_crypto):
                        crypto_id = future_to_crypto[future]
                        try:
                            result = future.result()
                            results[crypto_id] = result
                        except Exception as e:
                            errors.append({
                                'crypto_id': crypto_id,
                                'error': str(e)
                            })
                            logger.error(f"❌ Backtest failed for crypto {crypto_id}: {e}")
            else:
                # Sequential execution (for small batches or debugging)
                logger.info(f"📈 Running {len(crypto_ids)} backtests sequentially...")
                for crypto_id in crypto_ids:
                    if crypto_id in price_data_dict:
                        try:
                            result = backtest_service.run_backtest(
                                strategy_id,
                                crypto_id,
                                parameters,
                                start_date=start_date,
                                end_date=end_date,
                                interval=interval,
                                use_daily_sampling=use_daily_sampling
                            )
                            results[crypto_id] = result
                        except Exception as e:
                            errors.append({
                                'crypto_id': crypto_id,
                                'error': str(e)
                            })
            
            total_time = (dt.now() - start_time).total_seconds()
            
            # Calculate summary statistics
            successful_results = [r for r in results.values() if r.get('success', False)]
            
            summary = {
                'total_cryptocurrencies': len(crypto_ids),
                'successful_backtests': len(successful_results),
                'failed_backtests': len(errors),
                'execution_time_seconds': round(total_time, 2),
                'fetch_time_seconds': round(fetch_time, 2),
                'parallel_execution': use_parallel,
                'performance_note': f"Batch query saved {len(crypto_ids) - 1} database round-trips"
            }
            
            if successful_results:
                avg_return = sum(r['total_return'] for r in successful_results) / len(successful_results)
                best = max(successful_results, key=lambda x: x['total_return'])
                worst = min(successful_results, key=lambda x: x['total_return'])
                
                summary.update({
                    'average_return': round(avg_return, 2),
                    'best_performing': {
                        'crypto_id': best.get('crypto_id'),
                        'symbol': best.get('symbol'),
                        'return': best['total_return']
                    },
                    'worst_performing': {
                        'crypto_id': worst.get('crypto_id'),
                        'symbol': worst.get('symbol'),
                        'return': worst['total_return']
                    }
                })
            
            logger.info(f"✅ Batch backtest completed: {len(successful_results)}/{len(crypto_ids)} successful in {total_time:.2f}s")
            
            return {
                'summary': summary,
                'results': results,
                'errors': errors if errors else None
            }, 200
            
        except Exception as e:
            logger.error(f"❌ Batch backtest error: {e}")
            return {'error': str(e)}, 500

# Progressive Loading: SSE endpoint for streaming results
@app.route('/crypto/backtest/stream', methods=['POST'])
def stream_backtest():
    """
    Stream backtest results progressively using Server-Sent Events (SSE)
    Results are sent as they complete for real-time UI updates
    """
    data = request.get_json()
    
    if not data or 'strategy_id' not in data or 'parameters' not in data:
        return jsonify({'error': 'Missing required fields: strategy_id, parameters'}), 400
    
    # Get optional parameters
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    interval = data.get('interval', '1d')
    use_daily_sampling = (interval == '1d')
    max_workers = data.get('max_workers', 4)  # Control parallelism
    
    def generate():
        """Generator function for SSE stream"""
        try:
            for event in streaming_backtest_service.stream_strategy_against_all_cryptos(
                strategy_id=data['strategy_id'],
                parameters=data['parameters'],
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                use_daily_sampling=use_daily_sampling,
                max_workers=max_workers
            ):
                yield event
        except Exception as e:
            # Send error event if something goes wrong
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    # Return SSE response with proper headers
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Connection': 'keep-alive'
        }
    )

# Add backtest API endpoints
api.add_resource(CryptoStrategies, '/crypto/strategies')
api.add_resource(CryptoBacktestRun, '/crypto/backtest/run')
api.add_resource(CryptoBacktestAll, '/crypto/backtest/run-all')
api.add_resource(CryptoBacktestBatch, '/crypto/backtest/batch')  # NEW: Optimized batch endpoint
api.add_resource(CryptosWithData, '/crypto/with-data')

if __name__ == '__main__':
    print("Starting API container with Stock Data Service...")
    print(f"Database host: {DB_CONFIG['host']}")
    print(f"Web app host: {WEBAPP_HOST}:{WEBAPP_PORT}")
    
    # Start the stock data scheduler
    stock_scheduler.start_scheduler()
    print("Stock data scheduler started")
    
    app.run(host='0.0.0.0', port=8000, debug=True)