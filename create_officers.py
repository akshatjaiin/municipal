"""
Create 5 Department Officers with unique credentials.
Each officer can only access their own department's data.

Run: python manage.py shell < create_officers.py
Or:  python manage.py runscript create_officers (if using django-extensions)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'municipal.settings')
django.setup()

from django.contrib.auth.models import User
from civic_saathi.models import Department, Officer

# Define 5 departments with their officers
OFFICERS_DATA = [
    {
        "department": "Roads & Infrastructure",
        "username": "roads_officer",
        "email": "roads.officer@municipal.gov.in",
        "password": "Roads@2024",
        "first_name": "Rajesh",
        "last_name": "Kumar",
        "role": "Department Head"
    },
    {
        "department": "Sanitation & Waste",
        "username": "sanitation_officer",
        "email": "sanitation.officer@municipal.gov.in",
        "password": "Sanitation@2024",
        "first_name": "Priya",
        "last_name": "Sharma",
        "role": "Department Head"
    },
    {
        "department": "Water Supply",
        "username": "water_officer",
        "email": "water.officer@municipal.gov.in",
        "password": "Water@2024",
        "first_name": "Amit",
        "last_name": "Patel",
        "role": "Department Head"
    },
    {
        "department": "Electricity & Streetlights",
        "username": "electricity_officer",
        "email": "electricity.officer@municipal.gov.in",
        "password": "Electric@2024",
        "first_name": "Sunita",
        "last_name": "Verma",
        "role": "Department Head"
    },
    {
        "department": "Parks & Recreation",
        "username": "parks_officer",
        "email": "parks.officer@municipal.gov.in",
        "password": "Parks@2024",
        "first_name": "Vikram",
        "last_name": "Singh",
        "role": "Department Head"
    },
]

print("\n" + "="*60)
print("🏛️  CREATING DEPARTMENT OFFICERS")
print("="*60)

created_officers = []

for data in OFFICERS_DATA:
    # Get or create department
    dept, dept_created = Department.objects.get_or_create(
        name=data["department"],
        defaults={"description": f"Handles all {data['department'].lower()} related issues"}
    )
    if dept_created:
        print(f"\n✅ Created Department: {dept.name}")
    else:
        print(f"\n📁 Department exists: {dept.name}")
    
    # Check if user already exists
    if User.objects.filter(username=data["username"]).exists():
        user = User.objects.get(username=data["username"])
        print(f"   👤 User exists: {data['username']}")
    else:
        # Create user
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            is_staff=True  # Allow admin access
        )
        print(f"   ✅ Created User: {data['username']}")
    
    # Create or update officer
    officer, off_created = Officer.objects.get_or_create(
        user=user,
        defaults={
            "department": dept,
            "role": data["role"]
        }
    )
    if not off_created:
        officer.department = dept
        officer.role = data["role"]
        officer.save()
    
    created_officers.append({
        "department": dept.name,
        "username": data["username"],
        "email": data["email"],
        "password": data["password"]
    })

print("\n" + "="*60)
print("📋 LOGIN CREDENTIALS")
print("="*60)
print("\n| Department | Username | Email | Password |")
print("|------------|----------|-------|----------|")

for off in created_officers:
    print(f"| {off['department'][:20]:20} | {off['username']:18} | {off['email']:35} | {off['password']:15} |")

print("\n" + "="*60)
print("🔐 CREDENTIALS SUMMARY (Copy this!)")
print("="*60)

for off in created_officers:
    print(f"""
📁 {off['department']}
   Username: {off['username']}
   Email:    {off['email']}
   Password: {off['password']}
   Login:    /admin/""")

print("\n✅ All officers created! They can now login at /admin/")
print("   Each officer will ONLY see data from their own department.")
print("="*60 + "\n")
