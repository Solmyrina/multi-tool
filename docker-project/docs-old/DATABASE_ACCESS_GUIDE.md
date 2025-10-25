# 🔒 Secure Database Access Guide

## Overview
The PostgreSQL database is now secured and only accessible from within the Docker network. External access has been removed for security.

## For Applications
- ✅ **Internal Access**: All containers (webapp, api) can access the database using hostname `database:5432`
- ✅ **No Changes Required**: Existing application code continues to work

## For Database Administration

### Method 1: SSH Tunnel (Recommended)
Use SSH tunnel to securely access the database from your local machine:

```bash
# From your local machine
ssh -L 5432:localhost:5432 user@your-server-ip

# Then connect from another terminal
psql -h localhost -p 5432 -U root webapp_db
```

### Method 2: Docker Exec (Direct Container Access)
Access the database directly through the container:

```bash
# Connect to database container
docker exec -it docker-project-database psql -U root webapp_db

# Or run single commands
docker exec docker-project-database psql -U root webapp_db -c "SELECT version();"
```

### Method 3: pgAdmin Web Interface
Access pgAdmin through the secure web interface:

1. Navigate to: `https://your-server/pgadmin/`
2. Login with:
   - Email: `admin@dockerproject.com`
   - Password: `530NWC0Gm3pt4O`

### Method 4: Temporary Access (Emergency Only)
If you need temporary direct access (NOT recommended for production):

```bash
# Temporarily expose the port (EMERGENCY ONLY)
cd /home/one_control/docker-project
docker run -d --name temp-db-access --network docker-project-network -p 5432:5432 alpine/socat TCP-LISTEN:5432,fork TCP:database:5432

# Use the database, then IMMEDIATELY remove:
docker stop temp-db-access && docker rm temp-db-access
```

## Security Benefits
- ✅ **Network Isolation**: Database only accessible within Docker network
- ✅ **Firewall Protection**: UFW blocks external access to port 5432
- ✅ **Encrypted Transit**: All web access through HTTPS
- ✅ **Authentication Required**: Web interface requires login

## Database Connection Details
- **Internal Hostname**: `database`
- **Port**: `5432` (internal only)
- **Database**: `webapp_db`
- **Username**: `root`
- **Password**: `530NWC0Gm3pt4O`

## Firewall Configuration
Current UFW rules:
```
22/tcp  (SSH)    - ALLOW
80      (HTTP)   - ALLOW  
443     (HTTPS)  - ALLOW
5432    (PostgreSQL) - DENY (blocked from internet)
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if database container is running
docker ps | grep database

# Check database health
docker exec docker-project-database pg_isready -U root

# View database logs
docker logs docker-project-database

# Test connection from webapp container
docker exec docker-project-webapp python3 -c "
import psycopg2
conn = psycopg2.connect(host='database', database='webapp_db', user='root', password='530NWC0Gm3pt4O')
print('Connection successful')
conn.close()
"
```

### Application Issues
```bash
# Restart services if needed
docker compose restart webapp api

# Check logs
docker logs docker-project-webapp
docker logs docker-project-api
```

---
*Last updated: September 19, 2025*
*Security implementation: Database network isolation + UFW firewall*