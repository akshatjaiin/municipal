"""
Fix custom_user table - make extra columns nullable so Django's User model works.
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

print("Fixing custom_user table constraints...")

# Make the extra columns nullable
alter_statements = [
    "ALTER TABLE custom_user ALTER COLUMN user_type DROP NOT NULL",
    "ALTER TABLE custom_user ALTER COLUMN phone DROP NOT NULL", 
    "ALTER TABLE custom_user ALTER COLUMN city DROP NOT NULL",
    "ALTER TABLE custom_user ALTER COLUMN state DROP NOT NULL",
]

for stmt in alter_statements:
    try:
        cursor.execute(stmt)
        print(f"✅ {stmt}")
    except Exception as e:
        print(f"⚠️ {stmt} - {e}")

# Set default values for user_type
cursor.execute("UPDATE custom_user SET user_type = 'citizen' WHERE user_type IS NULL")
print("✅ Set default user_type='citizen' for existing null values")

# Also ensure the auth_user view exists
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
print("✅ auth_user view created/updated")

print("\n🎉 Database fix complete!")
