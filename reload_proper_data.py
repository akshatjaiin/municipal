"""
Reset and reload proper demo data for Nagar Nigam Jaipur.
This fixes the scattered data issue where workers were assigned to wrong departments.

Run: python manage.py shell < reload_proper_data.py
"""
import os
import django
from datetime import date, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'municipal.settings')
django.setup()

from django.contrib.auth.models import User
from civic_saathi.models import (
    Department, Officer, Worker, Complaint, ComplaintCategory,
    WorkerAttendance, Facility, FacilityInspection, Streetlight, SLAConfig
)

print("\n" + "="*70)
print("🏛️  NAGAR NIGAM JAIPUR - PROPER DATA SETUP")
print("="*70)

# ============================================
# STEP 1: Clear existing messy data
# ============================================
print("\n🧹 Clearing existing data...")
Streetlight.objects.all().delete()
Facility.objects.all().delete()
FacilityInspection.objects.all().delete()
WorkerAttendance.objects.all().delete()
Complaint.objects.all().delete()
Worker.objects.filter(user__username__startswith='worker').delete()
Officer.objects.filter(user__username__startswith='officer').delete()
User.objects.filter(username__startswith='worker').delete()
User.objects.filter(username__startswith='officer').delete()
ComplaintCategory.objects.all().delete()
SLAConfig.objects.all().delete()
Department.objects.all().delete()
print("   ✅ Old data cleared")

# ============================================
# STEP 2: Create Jaipur-specific Departments
# ============================================
print("\n🏢 Creating Departments...")

DEPARTMENTS = {
    "Roads & Infrastructure": {
        "description": "Handles potholes, road repairs, footpath maintenance",
        "categories": ["Pothole", "Road Damage", "Footpath Broken", "Speed Breaker Issue"],
        "worker_roles": ["Road Repair Worker", "Mason", "JCB Operator", "Supervisor"],
        "sla_hours": 72
    },
    "Sanitation & Waste Management": {
        "description": "Garbage collection, street sweeping, animal carcass removal",
        "categories": ["Garbage Overflow", "Street Cleaning", "Animal Carcass", "Drain Blockage"],
        "worker_roles": ["Sweeper", "Garbage Collector", "Drain Cleaner", "Safai Karamchari"],
        "sla_hours": 24
    },
    "Water Supply": {
        "description": "Water pipeline leaks, supply issues, tanker requests",
        "categories": ["Water Leakage", "No Water Supply", "Pipeline Burst", "Water Tanker Request"],
        "worker_roles": ["Plumber", "Pipeline Fitter", "Valve Operator", "Tanker Driver"],
        "sla_hours": 48
    },
    "Electricity & Streetlights": {
        "description": "Streetlight repairs, electrical issues in public areas",
        "categories": ["Streetlight Not Working", "Electrical Hazard", "Transformer Issue", "Wire Hanging"],
        "worker_roles": ["Electrician", "Lineman", "Streetlight Technician", "Helper"],
        "sla_hours": 48
    },
    "Public Health & Sanitation": {
        "description": "Public toilets, health facilities, sanitation inspection",
        "categories": ["Toilet Not Clean", "Toilet Not Working", "Health Hazard", "Mosquito Breeding"],
        "worker_roles": ["Sanitation Inspector", "Toilet Attendant", "Health Worker", "Pest Control"],
        "sla_hours": 24
    },
    "Parks & Gardens": {
        "description": "Park maintenance, garden upkeep, tree trimming",
        "categories": ["Park Not Maintained", "Tree Fallen", "Broken Bench", "Playground Issue"],
        "worker_roles": ["Gardner", "Park Attendant", "Tree Cutter", "Maintenance Worker"],
        "sla_hours": 72
    }
}

departments = {}
for dept_name, config in DEPARTMENTS.items():
    dept = Department.objects.create(name=dept_name, description=config["description"])
    departments[dept_name] = dept
    print(f"   ✅ {dept_name}")

# ============================================
# STEP 3: Create Categories with SLAs
# ============================================
print("\n📋 Creating Complaint Categories...")

for dept_name, config in DEPARTMENTS.items():
    dept = departments[dept_name]
    for cat_name in config["categories"]:
        cat = ComplaintCategory.objects.create(name=cat_name, department=dept)
        SLAConfig.objects.create(
            category=cat,
            resolution_hours=config["sla_hours"],
            escalation_hours=config["sla_hours"] + 24
        )
        print(f"   📌 {cat_name} → {dept_name} (SLA: {config['sla_hours']}h)")

# ============================================
# STEP 4: Create Officers (1 per department)
# ============================================
print("\n👔 Creating Department Officers...")

officer_data = [
    ("roads_officer", "Roads & Infrastructure", "Rajesh", "Kumar", "Roads@2024"),
    ("sanitation_officer", "Sanitation & Waste Management", "Priya", "Sharma", "Sanitation@2024"),
    ("water_officer", "Water Supply", "Amit", "Patel", "Water@2024"),
    ("electricity_officer", "Electricity & Streetlights", "Sunita", "Verma", "Electric@2024"),
    ("health_officer", "Public Health & Sanitation", "Vikram", "Singh", "Health@2024"),
    ("parks_officer", "Parks & Gardens", "Neha", "Gupta", "Parks@2024"),
]

for username, dept_name, first, last, password in officer_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@nagarnigam.jaipur.gov.in",
            "first_name": first,
            "last_name": last,
            "is_staff": True
        }
    )
    if created:
        user.set_password(password)
        user.save()
    
    Officer.objects.get_or_create(
        user=user,
        defaults={"department": departments[dept_name], "role": "Department Head"}
    )
    print(f"   👤 {username} → {dept_name}")

# ============================================
# STEP 5: Create Workers (PROPER department assignment)
# ============================================
print("\n👷 Creating Workers (Properly Assigned)...")

worker_id = 1
for dept_name, config in DEPARTMENTS.items():
    dept = departments[dept_name]
    for role in config["worker_roles"]:
        for i in range(2):  # 2 workers per role
            username = f"worker_{dept_name[:3].lower()}_{worker_id}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@nagarnigam.jaipur.gov.in",
                password="Worker@123",
                first_name=random.choice(["Ram", "Shyam", "Mohan", "Sohan", "Raju", "Gita", "Sita", "Radha"]),
                last_name=random.choice(["Kumar", "Sharma", "Verma", "Singh", "Gupta", "Jain"]),
                is_staff=False
            )
            Worker.objects.create(
                user=user,
                department=dept,
                role=role,
                joining_date=date.today() - timedelta(days=random.randint(30, 365)),
                is_active=True
            )
            worker_id += 1
    print(f"   ✅ {dept_name}: {len(config['worker_roles']) * 2} workers")

# ============================================
# STEP 6: Create Streetlights (Only for Electricity Dept)
# ============================================
print("\n💡 Creating Streetlights...")

electricity_dept = departments["Electricity & Streetlights"]
electricity_workers = list(Worker.objects.filter(department=electricity_dept))

JAIPUR_AREAS = [
    "MI Road", "Raja Park", "Malviya Nagar", "Vaishali Nagar", "Mansarovar",
    "Jagatpura", "Sodala", "Tonk Road", "Ajmer Road", "C-Scheme"
]

for area in JAIPUR_AREAS:
    for i in range(5):
        status = random.choice(["functional", "functional", "functional", "non_functional", "under_repair"])
        Streetlight.objects.create(
            pole_id=f"JMC-{area[:3].upper()}-{i+1:04d}",
            location=f"{area}, Jaipur",
            ward=f"Ward-{random.randint(1, 10)}",
            status=status,
            department=electricity_dept,
            assigned_worker=random.choice(electricity_workers) if electricity_workers else None,
            last_maintenance=date.today() - timedelta(days=random.randint(0, 180)) if status == "functional" else None
        )
print(f"   ✅ Created {len(JAIPUR_AREAS) * 5} streetlights (All in Electricity dept)")

# ============================================
# STEP 7: Create Public Facilities
# ============================================
print("\n🚻 Creating Public Facilities...")

health_dept = departments["Public Health & Sanitation"]
health_workers = list(Worker.objects.filter(department=health_dept))

FACILITY_DATA = [
    ("public_toilet", "Sulabh Shauchalay - MI Road", "Near MI Road Bus Stop"),
    ("public_toilet", "Sulabh Shauchalay - Railway Station", "Jaipur Junction Platform 1"),
    ("public_toilet", "Public Toilet - Hawa Mahal", "Near Hawa Mahal Entry Gate"),
    ("public_toilet", "Public Toilet - Central Park", "Central Park Main Entry"),
    ("govt_building", "Zonal Office - Zone 1", "Mansarovar"),
    ("govt_building", "Ward Office - Ward 5", "Raja Park"),
    ("park", "Central Park", "C-Scheme"),
    ("park", "Jawahar Circle Garden", "Malviya Nagar"),
    ("bus_stop", "Bus Stop - Sindhi Camp", "Sindhi Camp"),
    ("bus_stop", "Bus Stop - Vaishali", "Vaishali Nagar"),
]

parks_dept = departments["Parks & Gardens"]
parks_workers = list(Worker.objects.filter(department=parks_dept))

for ftype, name, address in FACILITY_DATA:
    if ftype == "public_toilet":
        dept = health_dept
        workers = health_workers
    elif ftype == "park":
        dept = parks_dept
        workers = parks_workers
    else:
        dept = health_dept
        workers = health_workers
    
    Facility.objects.create(
        name=name,
        facility_type=ftype,
        address=address + ", Jaipur",
        department=dept,
        assigned_worker=random.choice(workers) if workers else None,
        is_active=True
    )
print(f"   ✅ Created {len(FACILITY_DATA)} facilities")

# ============================================
# STEP 8: Create Sample Complaints
# ============================================
print("\n📝 Creating Sample Complaints...")

# Create a citizen user
citizen, _ = User.objects.get_or_create(
    username="citizen_demo",
    defaults={
        "email": "citizen@demo.com",
        "first_name": "Rahul",
        "last_name": "Citizen"
    }
)

complaint_samples = [
    ("Pothole on MI Road", "Large pothole causing accidents", "MI Road near GPO", "Roads & Infrastructure", "Pothole"),
    ("Garbage not collected", "Garbage overflowing for 3 days", "Raja Park Colony", "Sanitation & Waste Management", "Garbage Overflow"),
    ("Streetlight not working", "Pole JMC-MI-0001 is not working", "MI Road, Jaipur", "Electricity & Streetlights", "Streetlight Not Working"),
    ("Water leakage", "Pipeline burst, water wasting", "Malviya Nagar Main Road", "Water Supply", "Water Leakage"),
    ("Public toilet dirty", "Sulabh at MI Road very dirty", "MI Road Bus Stop", "Public Health & Sanitation", "Toilet Not Clean"),
    ("Dead dog on road", "Animal carcass on main road", "Tonk Road near petrol pump", "Sanitation & Waste Management", "Animal Carcass"),
]

for title, desc, location, dept_name, cat_name in complaint_samples:
    dept = departments[dept_name]
    cat = ComplaintCategory.objects.get(name=cat_name, department=dept)
    workers = Worker.objects.filter(department=dept)
    
    Complaint.objects.create(
        user=citizen,
        title=title,
        description=desc,
        location=location,
        category=cat,
        department=dept,
        priority=random.choice([1, 1, 2, 3]),
        status=random.choice(["pending", "pending", "in_progress"]),
        current_worker=random.choice(list(workers)) if workers.exists() else None
    )
print(f"   ✅ Created {len(complaint_samples)} sample complaints")

# ============================================
# SUMMARY
# ============================================
print("\n" + "="*70)
print("✅ DATA SETUP COMPLETE!")
print("="*70)

print("\n📊 SUMMARY:")
print(f"   • Departments: {Department.objects.count()}")
print(f"   • Categories: {ComplaintCategory.objects.count()}")
print(f"   • Officers: {Officer.objects.count()}")
print(f"   • Workers: {Worker.objects.count()}")
print(f"   • Streetlights: {Streetlight.objects.count()}")
print(f"   • Facilities: {Facility.objects.count()}")
print(f"   • Complaints: {Complaint.objects.count()}")

print("\n🔐 OFFICER LOGINS:")
print("-"*50)
for username, dept_name, _, _, password in officer_data:
    print(f"   {dept_name[:30]:30} | {username:20} | {password}")

print("\n" + "="*70)
