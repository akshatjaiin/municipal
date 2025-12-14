import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check custom_user table structure
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'custom_user'
    ORDER BY ordinal_position
""")
columns = cursor.fetchall()

print("=" * 50)
print("custom_user table columns:")
print("=" * 50)
for col, dtype in columns:
    print(f"  {col}: {dtype}")

# Check if auth_user exists
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'auth_user'
    ORDER BY ordinal_position
""")
auth_columns = cursor.fetchall()

print("\n" + "=" * 50)
print("auth_user table columns:")
print("=" * 50)
if auth_columns:
    for col, dtype in auth_columns:
        print(f"  {col}: {dtype}")
else:
    print("  Table does not exist!")
