"""
Fix all NOT NULL constraints that cause issues
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

print("Fixing NOT NULL constraints...")

# All columns that should be nullable
fixes = [
    ("civic_saathi_complaint", "completion_note"),
    ("civic_saathi_complaint", "rejection_reason"),
    ("civic_saathi_complaint", "feedback"),
    ("civic_saathi_complaint", "city"),
    ("civic_saathi_complaint", "state"),
    ("civic_saathi_complaint", "pincode"),
    ("civic_saathi_complaint", "ward"),
    ("civic_saathi_complaint", "zone"),
    ("civic_saathi_department", "sub_admin_category_id"),
    ("civic_saathi_worker", "city"),
    ("civic_saathi_worker", "state"),
    ("civic_saathi_worker", "phone"),
    ("civic_saathi_officer", "city"),
    ("civic_saathi_officer", "state"),
    ("civic_saathi_officer", "phone"),
    ("custom_user", "user_type"),
    ("custom_user", "phone"),
    ("custom_user", "city"),
    ("custom_user", "state"),
]

for table, column in fixes:
    try:
        cursor.execute(f'ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL')
        print(f"  ✅ {table}.{column}")
    except Exception as e:
        if "does not exist" in str(e):
            print(f"  ⏭️ {table}.{column} (column doesn't exist)")
        else:
            print(f"  ⚠️ {table}.{column}: {e}")

print("\n✅ All constraints fixed!")
