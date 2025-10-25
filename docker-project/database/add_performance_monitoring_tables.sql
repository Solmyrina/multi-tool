-- Performance Monitoring Tables
-- Add tables for historical system performance tracking

-- System Performance Metrics (CPU, Memory, Disk)
CREATE TABLE IF NOT EXISTS system_performance_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    host_name VARCHAR(100) DEFAULT 'webapp-container',
    
    -- CPU Metrics
    cpu_percent DECIMAL(5,2) NOT NULL,
    cpu_count INTEGER,
    load_average_1m DECIMAL(4,2),
    load_average_5m DECIMAL(4,2),
    load_average_15m DECIMAL(4,2),
    
    -- Memory Metrics (in bytes)
    memory_total BIGINT NOT NULL,
    memory_used BIGINT NOT NULL,
    memory_available BIGINT NOT NULL,
    memory_percent DECIMAL(5,2) NOT NULL,
    memory_cached BIGINT,
    memory_buffers BIGINT,
    
    -- Disk Metrics (in bytes)
    disk_total BIGINT NOT NULL,
    disk_used BIGINT NOT NULL,
    disk_free BIGINT NOT NULL,
    disk_percent DECIMAL(5,2) NOT NULL,
    
    -- Network Metrics (in bytes)
    network_bytes_sent BIGINT,
    network_bytes_recv BIGINT,
    network_packets_sent BIGINT,
    network_packets_recv BIGINT,
    
    -- Additional metrics
    processes_count INTEGER,
    threads_count INTEGER
);

-- Database Performance Metrics
CREATE TABLE IF NOT EXISTS database_performance_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Connection metrics
    active_connections INTEGER NOT NULL,
    max_connections INTEGER,
    idle_connections INTEGER,
    
    -- Query performance
    total_queries BIGINT,
    slow_queries BIGINT,
    queries_per_second DECIMAL(10,2),
    
    -- Database size metrics (in bytes)
    database_size BIGINT,
    table_count INTEGER,
    index_count INTEGER,
    
    -- Cache metrics
    cache_hit_ratio DECIMAL(5,2),
    shared_buffers_used BIGINT,
    
    -- Lock metrics
    active_locks INTEGER,
    waiting_locks INTEGER,
    
    -- Transaction metrics
    commits_per_second DECIMAL(10,2),
    rollbacks_per_second DECIMAL(10,2),
    
    -- I/O metrics
    blocks_read BIGINT,
    blocks_hit BIGINT,
    temp_files INTEGER,
    temp_bytes BIGINT
);

-- Container Health Monitoring
CREATE TABLE IF NOT EXISTS container_health_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Container identification
    container_name VARCHAR(100) NOT NULL,
    container_id VARCHAR(64),
    image_name VARCHAR(200),
    
    -- Container status
    status VARCHAR(50) NOT NULL, -- running, stopped, paused, etc.
    health_status VARCHAR(50), -- healthy, unhealthy, starting, none
    restart_count INTEGER DEFAULT 0,
    
    -- Resource usage
    cpu_percent DECIMAL(5,2),
    memory_usage BIGINT, -- in bytes
    memory_limit BIGINT,
    memory_percent DECIMAL(5,2),
    
    -- Network metrics
    network_rx_bytes BIGINT,
    network_tx_bytes BIGINT,
    
    -- Disk I/O
    disk_read_bytes BIGINT,
    disk_write_bytes BIGINT,
    
    -- Process metrics
    pids_current INTEGER,
    pids_limit INTEGER,
    
    -- Uptime
    started_at TIMESTAMP WITH TIME ZONE,
    uptime_seconds INTEGER
);

-- Slow Query Log
CREATE TABLE IF NOT EXISTS slow_query_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Query information
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64), -- MD5 hash for grouping similar queries
    execution_time_ms DECIMAL(10,3) NOT NULL,
    
    -- Query context
    database_name VARCHAR(100),
    user_name VARCHAR(100),
    application_name VARCHAR(100),
    
    -- Resource usage
    rows_examined BIGINT,
    rows_sent BIGINT,
    
    -- Indexes
    indexes_used TEXT[], -- array of index names used
    full_table_scan BOOLEAN DEFAULT FALSE,
    
    -- Additional metadata
    query_type VARCHAR(20), -- SELECT, INSERT, UPDATE, DELETE, etc.
    tables_accessed TEXT[] -- array of table names
);

-- System Alerts
CREATE TABLE IF NOT EXISTS system_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Alert details
    alert_type VARCHAR(50) NOT NULL, -- cpu_high, memory_high, disk_full, container_down, etc.
    severity VARCHAR(20) NOT NULL, -- critical, warning, info
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    
    -- Threshold information
    metric_name VARCHAR(100),
    current_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    
    -- Alert status
    status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional context
    host_name VARCHAR(100),
    container_name VARCHAR(100),
    additional_data JSONB
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_system_performance_timestamp ON system_performance_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_performance_host ON system_performance_history(host_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_database_performance_timestamp ON database_performance_history(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_container_health_timestamp ON container_health_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_container_health_name ON container_health_history(container_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_container_health_status ON container_health_history(status, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_slow_query_timestamp ON slow_query_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_slow_query_execution_time ON slow_query_log(execution_time_ms DESC);
CREATE INDEX IF NOT EXISTS idx_slow_query_hash ON slow_query_log(query_hash, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_system_alerts_timestamp ON system_alerts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_alerts_status ON system_alerts(status, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_alerts_type ON system_alerts(alert_type, timestamp DESC);

-- Views for easier querying
CREATE OR REPLACE VIEW latest_system_metrics AS
SELECT DISTINCT ON (host_name) 
    host_name,
    timestamp,
    cpu_percent,
    memory_percent,
    disk_percent,
    load_average_1m,
    processes_count
FROM system_performance_history
ORDER BY host_name, timestamp DESC;

CREATE OR REPLACE VIEW latest_container_health AS
SELECT DISTINCT ON (container_name)
    container_name,
    timestamp,
    status,
    health_status,
    cpu_percent,
    memory_percent,
    restart_count,
    uptime_seconds
FROM container_health_history
ORDER BY container_name, timestamp DESC;

CREATE OR REPLACE VIEW active_alerts AS
SELECT 
    alert_type,
    severity,
    title,
    message,
    current_value,
    threshold_value,
    timestamp,
    host_name,
    container_name
FROM system_alerts
WHERE status = 'active'
ORDER BY timestamp DESC;

-- Data retention policy views (show data older than X days for cleanup)
CREATE OR REPLACE VIEW old_performance_data AS
SELECT id FROM system_performance_history WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';

CREATE OR REPLACE VIEW old_container_data AS
SELECT id FROM container_health_history WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';

CREATE OR REPLACE VIEW old_slow_queries AS
SELECT id FROM slow_query_log WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '7 days';