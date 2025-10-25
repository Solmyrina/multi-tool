#!/usr/bin/env python3
"""
Performance Monitoring Service
Collects system, database, and container metrics and stores them in the database.
"""

import os
import sys
import time
import psutil
import docker
import psycopg
import hashlib
import threading
from datetime import datetime, timedelta
from psycopg.rows import dict_row
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/performance_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PerformanceMonitor')

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'database'),
    'port': os.environ.get('DB_PORT', '5432'),
    'dbname': os.environ.get('DB_NAME', 'webapp_db'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '530NWC0Gm3pt4O')
}

class PerformanceMonitor:
    def __init__(self):
        self.docker_client = None
        self.db_connection = None
        self.running = True
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            
        # Alert thresholds
        self.thresholds = {
            'cpu_percent': 90.0,
            'memory_percent': 90.0,
            'disk_percent': 95.0,
            'load_average': 10.0,
            'slow_query_ms': 5000.0,
            'active_connections': 80
        }
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            if self.db_connection is None or self.db_connection.closed:
                self.db_connection = psycopg.connect(**DB_CONFIG)
            return self.db_connection
        except psycopg.Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics (root filesystem)
            disk = psutil.disk_usage('/')
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            # Process metrics
            processes = len(psutil.pids())
            threads = sum(p.num_threads() for p in psutil.process_iter(['num_threads']) if p.info['num_threads'])
            
            metrics = {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_average_1m': load_avg[0],
                'load_average_5m': load_avg[1],
                'load_average_15m': load_avg[2],
                'memory_total': memory.total,
                'memory_used': memory.used,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'memory_cached': getattr(memory, 'cached', 0),
                'memory_buffers': getattr(memory, 'buffers', 0),
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_free': disk.free,
                'disk_percent': (disk.used / disk.total) * 100,
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'network_packets_sent': net_io.packets_sent,
                'network_packets_recv': net_io.packets_recv,
                'processes_count': processes,
                'threads_count': threads
            }
            
            # Check thresholds and create alerts
            self.check_system_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def collect_database_metrics(self):
        """Collect database performance metrics"""
        conn = None
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
                
            cur = conn.cursor(row_factory=dict_row)
            
            # Connection metrics
            cur.execute("""
                SELECT 
                    count(*) as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            conn_stats = cur.fetchone()
            
            # Get max connections
            cur.execute("SHOW max_connections")
            max_conn_result = cur.fetchone()
            max_conn = max_conn_result['max_connections'] if isinstance(max_conn_result, dict) else max_conn_result[0]
            
            # Database size
            cur.execute("""
                SELECT pg_database_size(current_database()) as database_size
            """)
            db_size = cur.fetchone()['database_size']
            
            # Table and index counts
            cur.execute("""
                SELECT 
                    (SELECT count(*) FROM pg_tables WHERE pg_tables.schemaname = 'public') as table_count,
                    (SELECT count(*) FROM pg_indexes WHERE pg_indexes.schemaname = 'public') as index_count
            """)
            counts = cur.fetchone()
            
            # Cache hit ratio
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN (blks_hit + blks_read) = 0 THEN 0
                        ELSE (blks_hit::float / (blks_hit + blks_read)) * 100
                    END as cache_hit_ratio,
                    blks_read,
                    blks_hit
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            cache_stats = cur.fetchone()
            
            # Lock information
            cur.execute("""
                SELECT 
                    count(*) as active_locks,
                    count(*) FILTER (WHERE NOT granted) as waiting_locks
                FROM pg_locks
            """)
            lock_stats = cur.fetchone()
            
            # Transaction stats
            cur.execute("""
                SELECT 
                    xact_commit,
                    xact_rollback,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted,
                    temp_files,
                    temp_bytes
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            tx_stats = cur.fetchone()
            
            metrics = {
                'active_connections': conn_stats['active_connections'],
                'max_connections': int(max_conn),
                'idle_connections': conn_stats['idle_connections'],
                'database_size': db_size,
                'table_count': counts['table_count'] or 0,
                'index_count': counts['index_count'] or 0,
                'cache_hit_ratio': cache_stats['cache_hit_ratio'] or 0,
                'blocks_read': cache_stats['blks_read'],
                'blocks_hit': cache_stats['blks_hit'],
                'active_locks': lock_stats['active_locks'],
                'waiting_locks': lock_stats['waiting_locks'],
                'temp_files': tx_stats['temp_files'] or 0,
                'temp_bytes': tx_stats['temp_bytes'] or 0,
                'total_queries': (tx_stats['tup_returned'] or 0) + (tx_stats['tup_fetched'] or 0),
                'slow_queries': 0,  # Will be updated by slow query monitoring
                'queries_per_second': 0,  # Will be calculated from delta
                'commits_per_second': 0,  # Will be calculated from delta
                'rollbacks_per_second': 0  # Will be calculated from delta
            }
            
            # Check database alerts
            self.check_database_alerts(metrics)
            
            return metrics
            
        except psycopg.Error as e:
            logger.error(f"Database error collecting database metrics: {e}")
            if conn:
                conn.rollback()
            return None
        except Exception as e:
            logger.error(f"Error collecting database metrics: {type(e).__name__}: {e}")
            if conn:
                conn.rollback()
            return None
    
    def collect_container_metrics(self):
        """Collect Docker container health and performance metrics"""
        try:
            if not self.docker_client:
                return []
                
            containers_metrics = []
            containers = self.docker_client.containers.list(all=True)
            
            for container in containers:
                try:
                    # Get container stats
                    stats = container.stats(stream=False) if container.status == 'running' else {}
                    
                    # Calculate CPU percentage
                    cpu_percent = 0
                    if 'cpu_stats' in stats and 'precpu_stats' in stats:
                        cpu_stats = stats['cpu_stats']
                        precpu_stats = stats['precpu_stats']
                        
                        cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                        system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                        
                        if system_delta > 0:
                            cpu_percent = (cpu_delta / system_delta) * len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', [1])) * 100
                    
                    # Memory metrics
                    memory_usage = stats.get('memory_stats', {}).get('usage', 0)
                    memory_limit = stats.get('memory_stats', {}).get('limit', 0)
                    memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
                    
                    # Network metrics
                    networks = stats.get('networks', {})
                    network_rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values())
                    network_tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values())
                    
                    # Disk I/O metrics
                    blkio_stats = stats.get('blkio_stats', {})
                    io_stats = blkio_stats.get('io_service_bytes_recursive', [])
                    disk_read_bytes = sum(stat.get('value', 0) for stat in io_stats if stat.get('op') == 'Read')
                    disk_write_bytes = sum(stat.get('value', 0) for stat in io_stats if stat.get('op') == 'Write')
                    
                    # PIDs
                    pids_stats = stats.get('pids_stats', {})
                    pids_current = pids_stats.get('current', 0)
                    pids_limit = pids_stats.get('limit', 0)
                    
                    # Container info
                    container.reload()
                    attrs = container.attrs
                    
                    # Calculate uptime
                    started_at = datetime.fromisoformat(attrs['State']['StartedAt'].replace('Z', '+00:00'))
                    uptime_seconds = (datetime.now(started_at.tzinfo) - started_at).total_seconds()
                    
                    # Health status
                    health_status = 'none'
                    if 'Health' in attrs['State']:
                        health_status = attrs['State']['Health']['Status']
                    
                    metrics = {
                        'container_name': container.name,
                        'container_id': container.id[:12],
                        'image_name': attrs['Config']['Image'],
                        'status': container.status,
                        'health_status': health_status,
                        'restart_count': attrs['RestartCount'],
                        'cpu_percent': cpu_percent,
                        'memory_usage': memory_usage,
                        'memory_limit': memory_limit,
                        'memory_percent': memory_percent,
                        'network_rx_bytes': network_rx_bytes,
                        'network_tx_bytes': network_tx_bytes,
                        'disk_read_bytes': disk_read_bytes,
                        'disk_write_bytes': disk_write_bytes,
                        'pids_current': pids_current,
                        'pids_limit': pids_limit,
                        'started_at': started_at,
                        'uptime_seconds': int(uptime_seconds)
                    }
                    
                    containers_metrics.append(metrics)
                    
                    # Check container alerts
                    self.check_container_alerts(metrics)
                    
                except Exception as e:
                    logger.error(f"Error collecting metrics for container {container.name}: {e}")
                    continue
            
            return containers_metrics
            
        except Exception as e:
            logger.error(f"Error collecting container metrics: {e}")
            return []
    
    def check_system_alerts(self, metrics):
        """Check system metrics against thresholds and create alerts"""
        alerts = []
        
        if metrics['cpu_percent'] > self.thresholds['cpu_percent']:
            alerts.append({
                'alert_type': 'cpu_high',
                'severity': 'warning',
                'title': 'High CPU Usage',
                'message': f"CPU usage is {metrics['cpu_percent']:.1f}% (threshold: {self.thresholds['cpu_percent']}%)",
                'metric_name': 'cpu_percent',
                'current_value': metrics['cpu_percent'],
                'threshold_value': self.thresholds['cpu_percent']
            })
        
        if metrics['memory_percent'] > self.thresholds['memory_percent']:
            alerts.append({
                'alert_type': 'memory_high',
                'severity': 'warning',
                'title': 'High Memory Usage',
                'message': f"Memory usage is {metrics['memory_percent']:.1f}% (threshold: {self.thresholds['memory_percent']}%)",
                'metric_name': 'memory_percent',
                'current_value': metrics['memory_percent'],
                'threshold_value': self.thresholds['memory_percent']
            })
        
        if metrics['disk_percent'] > self.thresholds['disk_percent']:
            alerts.append({
                'alert_type': 'disk_full',
                'severity': 'critical',
                'title': 'Disk Space Critical',
                'message': f"Disk usage is {metrics['disk_percent']:.1f}% (threshold: {self.thresholds['disk_percent']}%)",
                'metric_name': 'disk_percent',
                'current_value': metrics['disk_percent'],
                'threshold_value': self.thresholds['disk_percent']
            })
        
        self.store_alerts(alerts)
    
    def check_database_alerts(self, metrics):
        """Check database metrics against thresholds"""
        alerts = []
        
        connection_percent = (metrics['active_connections'] / metrics['max_connections']) * 100
        if connection_percent > self.thresholds['active_connections']:
            alerts.append({
                'alert_type': 'database_connections_high',
                'severity': 'warning',
                'title': 'High Database Connections',
                'message': f"Database connections at {connection_percent:.1f}% capacity ({metrics['active_connections']}/{metrics['max_connections']})",
                'metric_name': 'active_connections_percent',
                'current_value': connection_percent,
                'threshold_value': self.thresholds['active_connections']
            })
        
        self.store_alerts(alerts)
    
    def check_container_alerts(self, metrics):
        """Check container health and create alerts"""
        alerts = []
        
        if metrics['status'] != 'running':
            alerts.append({
                'alert_type': 'container_down',
                'severity': 'critical',
                'title': 'Container Not Running',
                'message': f"Container {metrics['container_name']} is {metrics['status']}",
                'container_name': metrics['container_name']
            })
        
        if metrics['health_status'] == 'unhealthy':
            alerts.append({
                'alert_type': 'container_unhealthy',
                'severity': 'warning',
                'title': 'Container Unhealthy',
                'message': f"Container {metrics['container_name']} health check failed",
                'container_name': metrics['container_name']
            })
        
        self.store_alerts(alerts)
    
    def store_alerts(self, alerts):
        """Store alerts in database"""
        if not alerts:
            return
            
        try:
            conn = self.get_db_connection()
            if not conn:
                return
                
            cur = conn.cursor()
            
            for alert in alerts:
                cur.execute("""
                    INSERT INTO system_alerts (
                        alert_type, severity, title, message, metric_name, 
                        current_value, threshold_value, host_name, container_name
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    alert['alert_type'],
                    alert['severity'],
                    alert['title'],
                    alert['message'],
                    alert.get('metric_name'),
                    alert.get('current_value'),
                    alert.get('threshold_value'),
                    alert.get('host_name', 'webapp-container'),
                    alert.get('container_name')
                ))
            
            conn.commit()
            logger.info(f"Stored {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"Error storing alerts: {e}")
    
    def store_system_metrics(self, metrics):
        """Store system metrics in database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO system_performance_history (
                    cpu_percent, cpu_count, load_average_1m, load_average_5m, load_average_15m,
                    memory_total, memory_used, memory_available, memory_percent, memory_cached, memory_buffers,
                    disk_total, disk_used, disk_free, disk_percent,
                    network_bytes_sent, network_bytes_recv, network_packets_sent, network_packets_recv,
                    processes_count, threads_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                metrics['cpu_percent'], metrics['cpu_count'], metrics['load_average_1m'], 
                metrics['load_average_5m'], metrics['load_average_15m'],
                metrics['memory_total'], metrics['memory_used'], metrics['memory_available'], 
                metrics['memory_percent'], metrics['memory_cached'], metrics['memory_buffers'],
                metrics['disk_total'], metrics['disk_used'], metrics['disk_free'], metrics['disk_percent'],
                metrics['network_bytes_sent'], metrics['network_bytes_recv'], 
                metrics['network_packets_sent'], metrics['network_packets_recv'],
                metrics['processes_count'], metrics['threads_count']
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")
            return False
    
    def store_database_metrics(self, metrics):
        """Store database metrics in database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO database_performance_history (
                    active_connections, max_connections, idle_connections,
                    total_queries, slow_queries, queries_per_second,
                    database_size, table_count, index_count,
                    cache_hit_ratio, active_locks, waiting_locks,
                    commits_per_second, rollbacks_per_second,
                    blocks_read, blocks_hit, temp_files, temp_bytes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                metrics['active_connections'], metrics['max_connections'], metrics['idle_connections'],
                metrics['total_queries'], metrics['slow_queries'], metrics['queries_per_second'],
                metrics['database_size'], metrics['table_count'], metrics['index_count'],
                metrics['cache_hit_ratio'], metrics['active_locks'], metrics['waiting_locks'],
                metrics['commits_per_second'], metrics['rollbacks_per_second'],
                metrics['blocks_read'], metrics['blocks_hit'], metrics['temp_files'], metrics['temp_bytes']
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing database metrics: {e}")
            return False
    
    def store_container_metrics(self, containers_metrics):
        """Store container metrics in database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cur = conn.cursor()
            
            for metrics in containers_metrics:
                cur.execute("""
                    INSERT INTO container_health_history (
                        container_name, container_id, image_name, status, health_status, restart_count,
                        cpu_percent, memory_usage, memory_limit, memory_percent,
                        network_rx_bytes, network_tx_bytes, disk_read_bytes, disk_write_bytes,
                        pids_current, pids_limit, started_at, uptime_seconds
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    metrics['container_name'], metrics['container_id'], metrics['image_name'],
                    metrics['status'], metrics['health_status'], metrics['restart_count'],
                    metrics['cpu_percent'], metrics['memory_usage'], metrics['memory_limit'], metrics['memory_percent'],
                    metrics['network_rx_bytes'], metrics['network_tx_bytes'], 
                    metrics['disk_read_bytes'], metrics['disk_write_bytes'],
                    metrics['pids_current'], metrics['pids_limit'], 
                    metrics['started_at'], metrics['uptime_seconds']
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing container metrics: {e}")
            return False
    
    def cleanup_old_data(self):
        """Clean up old performance data based on retention policies"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return
                
            cur = conn.cursor()
            
            # Clean up old system performance data (keep 30 days)
            cur.execute("DELETE FROM system_performance_history WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days'")
            system_deleted = cur.rowcount
            
            # Clean up old container health data (keep 30 days)
            cur.execute("DELETE FROM container_health_history WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days'")
            container_deleted = cur.rowcount
            
            # Clean up old database performance data (keep 30 days)
            cur.execute("DELETE FROM database_performance_history WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days'")
            db_deleted = cur.rowcount
            
            # Clean up old slow queries (keep 7 days)
            cur.execute("DELETE FROM slow_query_log WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '7 days'")
            query_deleted = cur.rowcount
            
            # Clean up resolved alerts (keep 7 days)
            cur.execute("DELETE FROM system_alerts WHERE status = 'resolved' AND resolved_at < CURRENT_TIMESTAMP - INTERVAL '7 days'")
            alert_deleted = cur.rowcount
            
            conn.commit()
            
            if any([system_deleted, container_deleted, db_deleted, query_deleted, alert_deleted]):
                logger.info(f"Cleaned up old data: {system_deleted} system records, {container_deleted} container records, "
                          f"{db_deleted} database records, {query_deleted} slow queries, {alert_deleted} alerts")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def run_collection_cycle(self):
        """Run one complete collection cycle"""
        logger.info("Starting performance data collection cycle")
        
        # Collect system metrics
        system_metrics = self.collect_system_metrics()
        if system_metrics:
            self.store_system_metrics(system_metrics)
            logger.debug("System metrics collected and stored")
        
        # Collect database metrics
        db_metrics = self.collect_database_metrics()
        if db_metrics:
            self.store_database_metrics(db_metrics)
            logger.debug("Database metrics collected and stored")
        
        # Collect container metrics
        container_metrics = self.collect_container_metrics()
        if container_metrics:
            self.store_container_metrics(container_metrics)
            logger.debug(f"Container metrics collected for {len(container_metrics)} containers")
        
        logger.info("Performance data collection cycle completed")
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Performance monitoring service starting...")
        
        # Run cleanup on startup
        self.cleanup_old_data()
        
        collection_interval = 60  # Collect metrics every 60 seconds
        cleanup_interval = 3600   # Cleanup old data every hour
        last_cleanup = time.time()
        
        while self.running:
            try:
                cycle_start = time.time()
                
                # Run collection cycle
                self.run_collection_cycle()
                
                # Run cleanup if needed
                if time.time() - last_cleanup > cleanup_interval:
                    self.cleanup_old_data()
                    last_cleanup = time.time()
                
                # Calculate sleep time to maintain consistent interval
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, collection_interval - cycle_duration)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Collection cycle took {cycle_duration:.2f}s, longer than {collection_interval}s interval")
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retrying
        
        logger.info("Performance monitoring service stopped")
    
    def stop(self):
        """Stop the monitoring service"""
        self.running = False

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down performance monitor...")
        monitor.stop()