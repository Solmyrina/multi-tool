# Architecture & System Design

Technical documentation for system design, data models, and API structure.

## 📖 Available Documents

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - High-level system design and service overview
- **[API_ENDPOINTS.md](./API_ENDPOINTS.md)** - Complete REST API reference with examples
- **[DATABASE.md](./DATABASE.md)** - PostgreSQL schema and data models
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - API quick lookup and common queries

## 🏗️ System Layers

```
┌────────────────────────────────────────┐
│      Presentation Layer                │
│   (Flask Web App + Templates)          │
└────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────┐
│        API Layer                       │
│   (Flask REST API + SSE Streaming)     │
└────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────┐
│      Business Logic Layer              │
│   (Backtesting, Analysis, Services)    │
└────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────┐
│       Data Access Layer                │
│   (psycopg3, SQLAlchemy, Caching)      │
└────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────┐
│      Data Storage Layer                │
│  (PostgreSQL + TimescaleDB + Redis)    │
└────────────────────────────────────────┘
```

## 🎯 Quick Links

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design, service communication |
| [API_ENDPOINTS.md](./API_ENDPOINTS.md) | All REST endpoints, parameters, examples |
| [DATABASE.md](./DATABASE.md) | Table schemas, relationships, indexing |
| [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) | Common endpoints, curl examples |
