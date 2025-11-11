# Database Migrations - Live Conversational Threads V2

This directory contains Alembic migrations for the Live Conversational Threads V2 data model.

## Setup

### Prerequisites
- PostgreSQL 12+ installed and running
- Python 3.11+
- All requirements installed: `pip install -r requirements.txt`

### Environment Variables
Set your database connection string:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/database_name"
```

## Migration Commands

### Run Migrations (Upgrade)
```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Apply one migration at a time
alembic upgrade +1
```

### Rollback Migrations (Downgrade)
```bash
# Rollback all migrations
alembic downgrade base

# Rollback to a specific revision
alembic downgrade <revision_id>

# Rollback one migration at a time
alembic downgrade -1
```

### Check Migration Status
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show SQL without applying
alembic upgrade head --sql
```

### Create New Migrations
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration template
alembic revision -m "Description of changes"
```

## Initial Schema (Revision: 732e0cd9a870)

The initial migration creates the following tables:

### 1. **conversations**
Top-level conversation container with metadata
- Speaker participant tracking
- Goals and progress tracking
- Source type (Google Meet, Slack, live audio, etc.)
- Full-text search support

### 2. **utterances**
Atomic units of speech/text
- Speaker attribution
- Temporal sequencing
- Platform-specific metadata (JSONB)
- Confidence scores

### 3. **nodes**
Analyzed conversational topics/segments
- Hierarchical structure (parent/children)
- Zoom level visibility
- Speaker info and transitions
- Canvas position for Obsidian export
- Temporal flow (predecessor/successor)

### 4. **relationships**
Edges/connections between nodes
- Multiple relationship types (temporal, contextual, etc.)
- Strength and confidence scores
- Supporting evidence (utterance IDs)

### 5. **clusters**
Hierarchical grouping of nodes
- Multi-level clustering (topics, themes)
- Auto-generation metadata
- Clustering algorithm tracking

### 6. **edits_log**
Training data from user corrections
- Tracks all manual edits
- Export flag for training datasets
- User confidence scores

### 7. **api_calls_log**
LLM API call tracking and cost monitoring
- Token usage (prompt + completion)
- Cost in USD
- Latency tracking
- Status and error logging

## Database Schema Features

### PostgreSQL Extensions
- **uuid-ossp**: For UUID generation

### JSONB Columns
Multiple tables use JSONB for flexible structured data:
- `conversations.source_metadata`
- `conversations.participants`
- `utterances.platform_metadata`
- `nodes.speaker_info`
- `nodes.cluster_info`

### Full-Text Search
- `conversations.tsv_search` (TSVECTOR with GIN index)

### Indexes
Comprehensive indexing strategy:
- Foreign key indexes
- Composite indexes for common queries
- Partial indexes for filtered queries
- JSONB expression indexes
- GIN indexes for arrays and tsvectors

### Constraints
- Check constraints for enum-like values
- Foreign key constraints with CASCADE/SET NULL
- Timestamp validation constraints
- Numeric range constraints

## Migration Best Practices

### Before Migration
1. **Backup your database**:
   ```bash
   pg_dump -U user database_name > backup.sql
   ```

2. **Test on development first**:
   ```bash
   # Dev environment
   export DATABASE_URL="postgresql://localhost/lct_dev"
   alembic upgrade head
   ```

3. **Review migration SQL**:
   ```bash
   alembic upgrade head --sql > migration.sql
   # Review migration.sql before applying
   ```

### After Migration
1. **Verify tables created**:
   ```sql
   \dt -- List all tables
   \d+ table_name -- Describe table
   ```

2. **Check indexes**:
   ```sql
   SELECT * FROM pg_indexes WHERE schemaname = 'public';
   ```

3. **Test rollback** (in dev):
   ```bash
   alembic downgrade -1
   alembic upgrade +1
   ```

## Troubleshooting

### Migration Fails with "relation already exists"
```bash
# Check current revision
alembic current

# Stamp database with current state (dangerous!)
alembic stamp head

# Or drop all tables and re-run
alembic downgrade base
alembic upgrade head
```

### Database URL Not Set
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
# Or set in .env file
```

### Permission Errors
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE database_name TO user;
GRANT ALL ON SCHEMA public TO user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user;
```

### UUID Extension Not Found
```sql
-- Manually enable if migration fails
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

## Development Workflow

### 1. Modify models.py
```python
# Add/modify SQLAlchemy models in models.py
class NewTable(Base):
    __tablename__ = "new_table"
    # ...
```

### 2. Generate migration
```bash
alembic revision --autogenerate -m "Add new_table"
```

### 3. Review generated migration
```bash
# Check alembic/versions/<revision>_add_new_table.py
# Manually adjust if needed
```

### 4. Test migration
```bash
# Apply
alembic upgrade head

# Test rollback
alembic downgrade -1
alembic upgrade head
```

### 5. Commit migration
```bash
git add alembic/versions/*.py models.py
git commit -m "Add new_table migration"
```

## Production Deployment

### Pre-deployment Checklist
- [ ] Backup production database
- [ ] Test migration on staging
- [ ] Review generated SQL
- [ ] Plan downtime window (if needed)
- [ ] Prepare rollback plan

### Deployment Steps
```bash
# 1. Backup
pg_dump -U prod_user prod_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migration
export DATABASE_URL="postgresql://prod_user:pass@prod-host:5432/prod_db"
alembic upgrade head

# 3. Verify
psql $DATABASE_URL -c "\dt"

# 4. If issues, rollback
alembic downgrade <previous_revision>
```

## Files Structure

```
lct_python_backend/
├── alembic/                    # Alembic configuration
│   ├── versions/              # Migration scripts
│   │   └── 732e0cd9a870_*.py # Initial schema migration
│   ├── env.py                 # Alembic environment config
│   ├── README                 # Auto-generated README
│   └── script.py.mako        # Migration template
├── alembic.ini                # Alembic settings
├── models.py                  # SQLAlchemy models (source of truth)
├── db.py                      # Database connection
└── DATABASE_MIGRATIONS.md    # This file
```

## Useful SQL Queries

### Check migration history
```sql
SELECT * FROM alembic_version;
```

### Count rows in all tables
```sql
SELECT
    schemaname,
    tablename,
    n_tup_ins - n_tup_del AS row_count
FROM pg_stat_user_tables
ORDER BY row_count DESC;
```

### Find largest tables
```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check index usage
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [DATA_MODEL_V2.md](../docs/DATA_MODEL_V2.md) - Complete data model specification
