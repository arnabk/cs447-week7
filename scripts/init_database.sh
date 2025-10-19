#!/bin/bash

# Database initialization script
# This script sets up the database schema and ensures all tables are created

set -e

echo "🗄️  Initializing database schema..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until pg_isready -h $PGHOST -p $PGPORT -U $PGUSER; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "✅ Database is ready"

# Check if database exists
echo "🔍 Checking if database exists..."
if psql -h $PGHOST -U $PGUSER -lqt | cut -d \| -f 1 | grep -qw $PGDATABASE; then
    echo "✅ Database $PGDATABASE already exists"
else
    echo "📝 Creating database $PGDATABASE"
    createdb -h $PGHOST -U $PGUSER $PGDATABASE
fi

# Check if pgvector extension is available
echo "🔍 Checking pgvector extension..."
if psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" | grep -q 1; then
    echo "✅ pgvector extension already installed"
else
    echo "📦 Installing pgvector extension..."
    psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "CREATE EXTENSION IF NOT EXISTS vector;"
fi

# Run schema setup
echo "📋 Setting up database schema..."
psql -h $PGHOST -U $PGUSER -d $PGDATABASE -f /docker-entrypoint-initdb.d/schema.sql

# Verify tables were created
echo "🔍 Verifying tables..."
TABLES=$(psql -h $PGHOST -U $PGUSER -d $PGDATABASE -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';")

EXPECTED_TABLES=("extracted_themes" "survey_responses" "theme_assignments" "theme_evolution_log" "batch_metadata" "embedding_cache")

for table in "${EXPECTED_TABLES[@]}"; do
    if echo "$TABLES" | grep -q "$table"; then
        echo "✅ Table $table exists"
    else
        echo "❌ Table $table missing"
        exit 1
    fi
done

# Verify indexes were created
echo "🔍 Verifying indexes..."
INDEXES=$(psql -h $PGHOST -U $PGUSER -d $PGDATABASE -t -c "SELECT indexname FROM pg_indexes WHERE schemaname = 'public';")

EXPECTED_INDEXES=("idx_themes_embedding" "idx_responses_embedding" "idx_themes_status" "idx_responses_batch")

for index in "${EXPECTED_INDEXES[@]}"; do
    if echo "$INDEXES" | grep -q "$index"; then
        echo "✅ Index $index exists"
    else
        echo "❌ Index $index missing"
        exit 1
    fi
done

echo "🎉 Database initialization complete!"
echo "📊 Database statistics:"
psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
