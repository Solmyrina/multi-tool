# Database & System Access

Connect to PostgreSQL database and system interfaces.

## 🗄️ PostgreSQL Access

### Method 1: pgAdmin (Easiest - Web UI)

**URL**: http://localhost:5050

**Login**: (pre-configured, should auto-connect)

**What you can do**:
- Browse tables
- Run SQL queries
- Export data
- Create backups
- User management

### Method 2: SSH Tunnel (Most Secure)

From your local machine:
```bash
ssh -L 5432:localhost:5432 user@your-server
```

Then connect from another terminal:
```bash
psql -h localhost -U root -d webapp_db
```

### Method 3: Direct Connection

```bash
# From inside container
docker exec -it docker-project-database psql -U root -d webapp_db

# From host machine (if PostgreSQL installed)
PGPASSWORD=yourpassword psql -h localhost -U root -d webapp_db
```

## 🔌 Connection String

```
Host:     localhost (or your-server.com)
Port:     5432
Database: webapp_db
User:     root
Password: (see docker-compose.yml or .env)
```

## 📊 Database Structure

**Main Tables**:
- `cryptocurrencies` - 230 active cryptos
- `crypto_prices` - 2,054,215+ hourly price records
- `backtest_results` - Backtest execution history
- `trades` - Individual trade records
- `users` - User accounts and roles
- `performance_metrics` - System monitoring data

**Size**: ~5-10 GB

## 🎯 Common Queries

### View All Active Cryptocurrencies
```sql
SELECT id, symbol, name, has_price_data 
FROM cryptocurrencies 
WHERE is_active = true 
ORDER BY name;
```

### Check Latest Price Data
```sql
SELECT DISTINCT 
  crypto_id, 
  MAX(datetime) as latest_price,
  interval_type
FROM crypto_prices 
GROUP BY crypto_id, interval_type
ORDER BY latest_price DESC;
```

### Backtest Results Summary
```sql
SELECT 
  strategy_id,
  COUNT(*) as count,
  AVG(total_return_percentage) as avg_return,
  MAX(total_return_percentage) as best_return,
  MIN(total_return_percentage) as worst_return
FROM backtest_results
GROUP BY strategy_id;
```

## 🛡️ Security

**DO**:
- Keep credentials in `.env` file
- Use SSH tunnels for remote access
- Rotate passwords regularly
- Backup database daily

**DON'T**:
- Share credentials in chat/email
- Use weak passwords
- Expose PostgreSQL to internet
- Commit `.env` to version control

## 📈 Monitoring

### Check Database Size
```bash
docker exec docker-project-database psql -U root -d webapp_db -c "SELECT pg_size_pretty(pg_database_size('webapp_db'));"
```

### Check Table Sizes
```bash
docker exec docker-project-database psql -U root -d webapp_db -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
  FROM pg_tables
  WHERE schemaname NOT LIKE 'pg_%'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## 🔄 Backup & Restore

### Backup Database
```bash
docker exec docker-project-database pg_dump -U root webapp_db > backup.sql
```

### Restore Database
```bash
docker exec -i docker-project-database psql -U root webapp_db < backup.sql
```

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to database | Check PostgreSQL running, credentials correct |
| Permission denied | Verify user role, check access grants |
| Connection timeout | Check firewall, SSH tunnel active |
| Slow queries | Check indexes, see OPTIMIZATION.md |

---

*Last Updated: October 25, 2025*  
*For detailed database schema, see [ARCHITECTURE.md](../architecture/ARCHITECTURE.md)*
