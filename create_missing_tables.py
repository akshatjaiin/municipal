"""
Create missing tables directly using raw SQL
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

# Get existing tables
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
existing = set(row[0] for row in cursor.fetchall())

print("Creating missing tables...")

# Create missing tables
tables_sql = {
    'civic_saathi_streetlight': """
        CREATE TABLE IF NOT EXISTS civic_saathi_streetlight (
            id BIGSERIAL PRIMARY KEY,
            pole_number VARCHAR(50) UNIQUE NOT NULL,
            location VARCHAR(255) NOT NULL,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            status VARCHAR(20) DEFAULT 'working',
            wattage INTEGER,
            installation_date DATE,
            last_maintenance DATE,
            department_id BIGINT REFERENCES civic_saathi_department(id) ON DELETE SET NULL
        )
    """,
    'civic_saathi_facility': """
        CREATE TABLE IF NOT EXISTS civic_saathi_facility (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            facility_type VARCHAR(50) NOT NULL,
            description TEXT,
            address VARCHAR(500),
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            contact_number VARCHAR(20),
            email VARCHAR(254),
            opening_time TIME,
            closing_time TIME,
            is_open_24x7 BOOLEAN DEFAULT FALSE,
            image VARCHAR(100),
            rating DOUBLE PRECISION DEFAULT 0,
            total_ratings INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            department_id BIGINT REFERENCES civic_saathi_department(id) ON DELETE SET NULL
        )
    """,
    'civic_saathi_facilityinspection': """
        CREATE TABLE IF NOT EXISTS civic_saathi_facilityinspection (
            id BIGSERIAL PRIMARY KEY,
            inspection_date DATE NOT NULL,
            notes TEXT,
            status VARCHAR(20) DEFAULT 'scheduled',
            facility_id BIGINT NOT NULL REFERENCES civic_saathi_facility(id) ON DELETE CASCADE,
            inspector_id BIGINT REFERENCES civic_saathi_officer(id) ON DELETE SET NULL
        )
    """,
    'civic_saathi_facilityrating': """
        CREATE TABLE IF NOT EXISTS civic_saathi_facilityrating (
            id BIGSERIAL PRIMARY KEY,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            facility_id BIGINT NOT NULL REFERENCES civic_saathi_facility(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES custom_user(id) ON DELETE CASCADE,
            UNIQUE (facility_id, user_id)
        )
    """,
    'civic_saathi_slaconfig': """
        CREATE TABLE IF NOT EXISTS civic_saathi_slaconfig (
            id BIGSERIAL PRIMARY KEY,
            priority INTEGER NOT NULL,
            resolution_hours INTEGER NOT NULL,
            escalation_hours INTEGER NOT NULL,
            category_id BIGINT UNIQUE REFERENCES civic_saathi_complaintcategory(id) ON DELETE CASCADE
        )
    """
}

for table_name, sql in tables_sql.items():
    if table_name not in existing:
        try:
            cursor.execute(sql)
            print(f"  ✅ Created {table_name}")
        except Exception as e:
            print(f"  ⚠️ {table_name}: {e}")
    else:
        print(f"  ✓ {table_name} already exists")

# Now fake remaining migrations
print("\n✅ Tables created. Now faking remaining migrations...")
