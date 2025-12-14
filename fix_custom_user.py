"""
Fix database schema - make columns nullable, create views, and sync with Django models.
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

print("=" * 60)
print("FIXING DATABASE SCHEMA")
print("=" * 60)

# All columns that should be nullable
nullable_columns = [
    # custom_user
    ("custom_user", "user_type"),
    ("custom_user", "phone"),
    ("custom_user", "city"),
    ("custom_user", "state"),
    # civic_saathi_complaint
    ("civic_saathi_complaint", "completion_note"),
    ("civic_saathi_complaint", "latitude"),
    ("civic_saathi_complaint", "is_genuine"),
    ("civic_saathi_complaint", "longitude"),
    ("civic_saathi_complaint", "sorted"),
    ("civic_saathi_complaint", "filter_reason"),
    ("civic_saathi_complaint", "city"),
    ("civic_saathi_complaint", "assigned"),
    ("civic_saathi_complaint", "completed_at"),
    ("civic_saathi_complaint", "filter_checked"),
    ("civic_saathi_complaint", "filter_passed"),
    ("civic_saathi_complaint", "state"),
    ("civic_saathi_complaint", "upvote_count"),
    ("civic_saathi_complaint", "completion_image"),
    ("civic_saathi_complaint", "downvote_count"),
    # civic_saathi_department
    ("civic_saathi_department", "sub_admin_category_id"),
    # civic_saathi_worker
    ("civic_saathi_worker", "city"),
    ("civic_saathi_worker", "state"),
]

print("\n🔧 Making columns nullable...")
for table, column in nullable_columns:
    try:
        cursor.execute(f'ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL')
        print(f"  ✅ {table}.{column}")
    except Exception as e:
        if "does not exist" in str(e):
            pass  # Column doesn't exist, skip silently
        elif "already" in str(e).lower():
            pass  # Already nullable
        else:
            print(f"  ⚠️ {table}.{column}: {e}")

# Set defaults
print("\n🔧 Setting defaults...")
try:
    cursor.execute("UPDATE custom_user SET user_type = 'citizen' WHERE user_type IS NULL")
    cursor.execute("ALTER TABLE civic_saathi_complaint ALTER COLUMN upvote_count SET DEFAULT 0")
    cursor.execute("ALTER TABLE civic_saathi_complaint ALTER COLUMN downvote_count SET DEFAULT 0")
    print("  ✅ Defaults set")
except Exception as e:
    print(f"  ⚠️ {e}")

# Create auth_user view
print("\n🔧 Creating auth_user view...")
cursor.execute("""
    CREATE OR REPLACE VIEW auth_user AS 
    SELECT 
        id,
        password,
        last_login,
        is_superuser,
        username,
        first_name,
        last_name,
        email,
        is_staff,
        is_active,
        date_joined
    FROM custom_user
""")
print("  ✅ auth_user view created")

# Create auth_user_groups table if not exists
print("\n🔧 Creating auth_user helper tables...")
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_user_groups (
            id BIGSERIAL PRIMARY KEY, 
            user_id BIGINT NOT NULL REFERENCES custom_user(id) ON DELETE CASCADE, 
            group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE, 
            UNIQUE(user_id, group_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_user_user_permissions (
            id BIGSERIAL PRIMARY KEY, 
            user_id BIGINT NOT NULL REFERENCES custom_user(id) ON DELETE CASCADE, 
            permission_id INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE, 
            UNIQUE(user_id, permission_id)
        )
    ''')
    print("  ✅ Helper tables created")
except Exception as e:
    print(f"  ⚠️ {e}")

print("\n" + "=" * 60)
print("✅ DATABASE SCHEMA FIX COMPLETE!")
print("=" * 60)
