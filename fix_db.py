import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

# Get all existing tables
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
tables = [row[0] for row in cursor.fetchall()]

print("=" * 50)
print("Existing tables in database:")
print("=" * 50)
for t in sorted(tables):
    print(f"  - {t}")

print("\n" + "=" * 50)
print("Checking migration records:")
print("=" * 50)

cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
migrations = cursor.fetchall()
for app, name in migrations:
    print(f"  [{app}] {name}")

# Check which Django core tables are missing
core_tables = ['auth_user', 'auth_group', 'auth_permission', 'django_content_type', 'django_session', 'authtoken_token']
missing = [t for t in core_tables if t not in tables]

print("\n" + "=" * 50)
print("Missing core tables:")
print("=" * 50)
for t in missing:
    print(f"  - {t}")

if missing:
    print("\n" + "=" * 50)
    print("ACTION NEEDED: Run migrations for core Django apps")
    print("=" * 50)
