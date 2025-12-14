"""
Sync database tables with Django models
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

print("=" * 60)
print("SYNCING DATABASE WITH MODELS")
print("=" * 60)

# Fix civic_saathi_facility table
print("\n🔧 Fixing civic_saathi_facility table...")

# Drop and recreate with correct schema
try:
    # First check if columns need renaming
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'civic_saathi_facility'
    """)
    columns = [row[0] for row in cursor.fetchall()]
    print(f"  Current columns: {columns}")
    
    # If latitude exists but location_lat doesn't, rename
    if 'latitude' in columns and 'location_lat' not in columns:
        cursor.execute("ALTER TABLE civic_saathi_facility RENAME COLUMN latitude TO location_lat")
        print("  ✅ Renamed latitude -> location_lat")
    
    if 'longitude' in columns and 'location_lng' not in columns:
        cursor.execute("ALTER TABLE civic_saathi_facility RENAME COLUMN longitude TO location_lng")
        print("  ✅ Renamed longitude -> location_lng")
    
    # Add missing columns
    needed_columns = {
        'assigned_worker_id': 'BIGINT REFERENCES civic_saathi_worker(id) ON DELETE SET NULL',
        'location_lat': 'DECIMAL(9,6)',
        'location_lng': 'DECIMAL(9,6)',
    }
    
    for col, dtype in needed_columns.items():
        if col not in columns:
            try:
                cursor.execute(f"ALTER TABLE civic_saathi_facility ADD COLUMN {col} {dtype}")
                print(f"  ✅ Added column {col}")
            except Exception as e:
                print(f"  ⚠️ {col}: {e}")

    # Drop columns that shouldn't exist
    extra_columns = ['contact_number', 'email', 'opening_time', 'closing_time', 'is_open_24x7', 
                     'image', 'rating', 'total_ratings', 'updated_at']
    for col in extra_columns:
        if col in columns:
            try:
                cursor.execute(f"ALTER TABLE civic_saathi_facility DROP COLUMN {col}")
                print(f"  ✅ Dropped extra column {col}")
            except Exception as e:
                print(f"  ⚠️ Dropping {col}: {e}")

except Exception as e:
    print(f"  ❌ Error: {e}")

# Fix civic_saathi_facilityrating table
print("\n🔧 Fixing civic_saathi_facilityrating table...")
try:
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'civic_saathi_facilityrating'
    """)
    columns = [row[0] for row in cursor.fetchall()]
    print(f"  Current columns: {columns}")
    
    # The model expects cleanliness_rating, toilet_availability, facilities_condition, overall_feedback
    needed = {
        'cleanliness_rating': 'INTEGER DEFAULT 3',
        'toilet_availability': 'BOOLEAN DEFAULT TRUE',
        'facilities_condition': 'VARCHAR(20)',
        'overall_feedback': 'TEXT',
    }
    
    for col, dtype in needed.items():
        if col not in columns:
            try:
                cursor.execute(f"ALTER TABLE civic_saathi_facilityrating ADD COLUMN {col} {dtype}")
                print(f"  ✅ Added column {col}")
            except Exception as e:
                print(f"  ⚠️ {col}: {e}")
    
    # Rename rating to cleanliness_rating if needed
    if 'rating' in columns and 'cleanliness_rating' not in columns:
        cursor.execute("ALTER TABLE civic_saathi_facilityrating RENAME COLUMN rating TO cleanliness_rating")
        print("  ✅ Renamed rating -> cleanliness_rating")
    
    # Drop old columns
    if 'comment' in columns:
        try:
            cursor.execute("ALTER TABLE civic_saathi_facilityrating DROP COLUMN comment")
            print("  ✅ Dropped comment column")
        except:
            pass

except Exception as e:
    print(f"  ❌ Error: {e}")

# Fix civic_saathi_streetlight table  
print("\n🔧 Fixing civic_saathi_streetlight table...")
try:
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'civic_saathi_streetlight'
    """)
    columns = [row[0] for row in cursor.fetchall()]
    print(f"  Current columns: {columns}")
    
    # Model expects: pole_id, location_lat, location_lng, zone, ward, installation_date, last_maintenance, status, department
    renames = [
        ('pole_number', 'pole_id'),
        ('location', 'zone'),
        ('latitude', 'location_lat'),
        ('longitude', 'location_lng'),
    ]
    
    for old, new in renames:
        if old in columns and new not in columns:
            try:
                cursor.execute(f"ALTER TABLE civic_saathi_streetlight RENAME COLUMN {old} TO {new}")
                print(f"  ✅ Renamed {old} -> {new}")
            except Exception as e:
                print(f"  ⚠️ Renaming {old}: {e}")
    
    # Add missing columns
    needed = {
        'ward': "VARCHAR(50)",
        'location_lat': 'DECIMAL(9,6)',
        'location_lng': 'DECIMAL(9,6)',
        'zone': 'VARCHAR(100)',
        'pole_id': 'VARCHAR(50)',
    }
    
    for col, dtype in needed.items():
        if col not in columns:
            try:
                cursor.execute(f"ALTER TABLE civic_saathi_streetlight ADD COLUMN {col} {dtype}")
                print(f"  ✅ Added column {col}")
            except Exception as e:
                print(f"  ⚠️ {col}: {e}")

    # Drop extra columns
    extras = ['wattage']
    for col in extras:
        if col in columns:
            try:
                cursor.execute(f"ALTER TABLE civic_saathi_streetlight DROP COLUMN {col}")
                print(f"  ✅ Dropped {col}")
            except:
                pass

except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Database sync complete!")
print("=" * 60)
