"""
Fix database by creating auth_user view pointing to custom_user table.
This allows Django's default User model to work with the existing custom_user data.
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'municipal.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()

print("Creating auth_user view pointing to custom_user table...")

# Create a view that maps custom_user to auth_user
# This way Django's User model will read/write to custom_user
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

print("✅ auth_user view created successfully!")

# Verify it works
cursor.execute("SELECT COUNT(*) FROM auth_user")
count = cursor.fetchone()[0]
print(f"✅ auth_user now has {count} users")

# Test a query like Django would make
cursor.execute("SELECT id, username, is_active FROM auth_user LIMIT 5")
users = cursor.fetchall()
print("\nSample users:")
for u in users:
    print(f"  ID: {u[0]}, Username: {u[1]}, Active: {u[2]}")

print("\n🎉 Database fix complete!")
