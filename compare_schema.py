"""
Compare model fields to database columns and fix mismatches
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection
from civic_saathi.models import Complaint

cursor = connection.cursor()

# Get model fields
model_fields = set(f.column for f in Complaint._meta.get_fields() if hasattr(f, 'column'))
print("Model fields:")
print(model_fields)

# Get database columns
cursor.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'civic_saathi_complaint'
""")
db_columns = set(row[0] for row in cursor.fetchall())
print("\nDB columns:")
print(db_columns)

# Extra columns in DB
extra = db_columns - model_fields
print(f"\n⚠️ Extra columns in DB (not in model): {extra}")

# Set defaults for extra NOT NULL columns
for col in extra:
    try:
        # Try to make nullable
        cursor.execute(f"ALTER TABLE civic_saathi_complaint ALTER COLUMN {col} DROP NOT NULL")
        print(f"  ✅ Made {col} nullable")
    except Exception as e:
        print(f"  ⚠️ {col}: {e}")
