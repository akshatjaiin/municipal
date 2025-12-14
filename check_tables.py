"""
Check which tables exist vs what models expect
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection
from django.apps import apps

cursor = connection.cursor()

# Get all existing tables
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
existing_tables = set(row[0] for row in cursor.fetchall())

print("=" * 60)
print("EXISTING TABLES:")
print("=" * 60)
for t in sorted(existing_tables):
    print(f"  ✓ {t}")

# Get expected tables from civic_saathi models
print("\n" + "=" * 60)
print("EXPECTED civic_saathi TABLES (from models):")
print("=" * 60)

app_models = apps.get_app_config('civic_saathi').get_models()
missing_tables = []

for model in app_models:
    table_name = model._meta.db_table
    exists = table_name in existing_tables
    status = "✓" if exists else "✗ MISSING"
    print(f"  {status} {table_name}")
    if not exists:
        missing_tables.append(table_name)

if missing_tables:
    print("\n" + "=" * 60)
    print(f"⚠️  {len(missing_tables)} MISSING TABLES - Need to create!")
    print("=" * 60)
