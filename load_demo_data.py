import os
import django
import random
from datetime import datetime, timedelta, date, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "municipal.settings")
django.setup()

from django.contrib.auth.models import User
from civic_saathi.models import (
    Department, Officer, Worker, Complaint, ComplaintLog, Assignment,
    ComplaintCategory, ComplaintEscalation, WorkerAttendance, 
    Facility, FacilityInspection, SLAConfig, Streetlight
)
from faker import Faker

fake = Faker(['en_IN'])  # Indian data


# --------------------------
# Create Departments
# --------------------------
dept_data = [
    ("Sanitation", "Garbage, Sweeping, Public Cleanliness"),
    ("Roads", "Potholes, Road Maintenance, Footpaths"),
    ("Electricity", "Streetlights, Electrical Faults"),
    ("Water Supply", "Water Leakage, Pipeline Repair"),
    ("Sewage", "Drainage Blockage, Overflow"),
    ("Public Health", "Dead Animals, Mosquito Fogging"),
]

departments = {}
for (name, desc) in dept_data:
    d, _ = Department.objects.get_or_create(name=name, description=desc)
    departments[name] = d

print("✔ Departments created")


# --------------------------
# Create Complaint Categories (mapped to departments)
# --------------------------
category_data = [
    ("Garbage Collection", "Sanitation"),
    ("Street Sweeping", "Sanitation"),
    ("Overflowing Dustbin", "Sanitation"),
    ("Pothole Repair", "Roads"),
    ("Road Damage", "Roads"),
    ("Footpath Repair", "Roads"),
    ("Streetlight Not Working", "Electricity"),
    ("Electrical Fault", "Electricity"),
    ("Flickering Light", "Electricity"),
    ("Water Leakage", "Water Supply"),
    ("No Water Supply", "Water Supply"),
    ("Pipeline Burst", "Water Supply"),
    ("Drain Blockage", "Sewage"),
    ("Sewage Overflow", "Sewage"),
    ("Manhole Issue", "Sewage"),
    ("Dead Animal Removal", "Public Health"),
    ("Mosquito Fogging", "Public Health"),
    ("Stray Animal", "Public Health"),
]

categories = {}
for (cat_name, dept_name) in category_data:
    cat, _ = ComplaintCategory.objects.get_or_create(
        name=cat_name,
        department=departments[dept_name]
    )
    categories[cat_name] = cat

print("✔ Complaint Categories created")


# --------------------------
# Create SLA Configurations
# --------------------------
sla_configs = {
    "Garbage Collection": (24, 48),
    "Street Sweeping": (24, 48),
    "Overflowing Dustbin": (12, 24),
    "Pothole Repair": (72, 120),
    "Road Damage": (48, 96),
    "Footpath Repair": (72, 120),
    "Streetlight Not Working": (24, 48),
    "Electrical Fault": (12, 24),
    "Flickering Light": (24, 48),
    "Water Leakage": (12, 24),
    "No Water Supply": (6, 12),
    "Pipeline Burst": (6, 12),
    "Drain Blockage": (24, 48),
    "Sewage Overflow": (12, 24),
    "Manhole Issue": (24, 48),
    "Dead Animal Removal": (12, 24),
    "Mosquito Fogging": (48, 96),
    "Stray Animal": (24, 48),
}

for cat_name, (resolution_hrs, escalation_hrs) in sla_configs.items():
    if cat_name in categories:
        SLAConfig.objects.get_or_create(
            category=categories[cat_name],
            defaults={
                "resolution_hours": resolution_hrs,
                "escalation_hours": escalation_hrs
            }
        )

print("✔ SLA Configurations created")


# --------------------------
# Create Officers (with hierarchy)
# --------------------------
officer_roles_by_dept = {
    "Sanitation": ["Sanitation Head", "Zonal Sanitation Officer", "Ward Supervisor"],
    "Roads": ["Roads Head", "Zonal Roads Officer", "Site Supervisor"],
    "Electricity": ["Electrical Head", "Zonal Electrical Officer", "Line Supervisor"],
    "Water Supply": ["Water Dept Head", "Zonal Water Officer", "Pipeline Supervisor"],
    "Sewage": ["Sewage Head", "Zonal Sewage Officer", "Drain Supervisor"],
    "Public Health": ["Health Dept Head", "Zonal Health Officer", "Field Supervisor"],
}

officers = []
officer_counter = 0
for dept_name, roles in officer_roles_by_dept.items():
    dept = departments[dept_name]
    for role in roles:
        username = f"officer{officer_counter}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@gov.in",
                "first_name": fake.first_name(),
                "last_name": fake.last_name()
            }
        )
        if created:
            user.set_password("1234")
            user.save()
        
        officer, _ = Officer.objects.get_or_create(
            user=user,
            defaults={
                "department": dept,
                "role": role
            }
        )
        officers.append(officer)
        officer_counter += 1

print("✔ Officers created (18 officers, 3 per department)")


# --------------------------
# Create Workers (proper roles per dept)
# --------------------------
worker_roles_by_dept = {
    "Sanitation": ["Sweeper", "Garbage Collector", "Cleaning Staff"],
    "Roads": ["Road Repair Worker", "Pothole Filler", "Construction Worker"],
    "Electricity": ["Electrician", "Line Technician", "Pole Climber"],
    "Water Supply": ["Plumber", "Pipeline Worker", "Valve Operator"],
    "Sewage": ["Drain Cleaner", "Sewer Worker", "Pump Operator"],
    "Public Health": ["Field Worker", "Fogging Operator", "Sanitation Inspector"],
}

workers = []
workers_by_dept = {dept_name: [] for dept_name in departments.keys()}
worker_counter = 0

for dept_name, roles in worker_roles_by_dept.items():
    dept = departments[dept_name]
    # Create 4 workers per department
    for _ in range(4):
        role = random.choice(roles)
        username = f"worker{worker_counter}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@gov.in",
                "first_name": fake.first_name(),
                "last_name": fake.last_name()
            }
        )
        if created:
            user.set_password("1234")
            user.save()
        
        worker, _ = Worker.objects.get_or_create(
            user=user,
            defaults={
                "department": dept,
                "role": role,
                "address": fake.address(),
                "joining_date": fake.date_between(start_date="-3y", end_date="-1m"),
                "is_active": True
            }
        )
        workers.append(worker)
        workers_by_dept[dept_name].append(worker)
        worker_counter += 1

print(f"✔ Workers created ({len(workers)} workers, ~4 per department)")


# --------------------------
# Create Citizens
# --------------------------
citizens = []
for i in range(30):
    username = f"citizen{i}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@mail.com",
            "first_name": fake.first_name(),
            "last_name": fake.last_name()
        }
    )
    if created:
        user.set_password("1234")
        user.save()
    citizens.append(user)

print("✔ Citizens created")


# --------------------------
# Create Worker Attendance (last 30 days)
# --------------------------
today = date.today()
attendance_statuses = ["present", "present", "present", "present", "absent", "half_day", "on_leave"]

for worker in workers:
    for day_offset in range(30):
        attendance_date = today - timedelta(days=day_offset)
        # Skip weekends (optional - more realistic)
        if attendance_date.weekday() in [6]:  # Sunday off
            continue
        
        status = random.choice(attendance_statuses)
        check_in_time = None
        check_out_time = None
        
        if status == "present":
            check_in_time = time(hour=random.randint(8, 9), minute=random.randint(0, 59))
            check_out_time = time(hour=random.randint(17, 18), minute=random.randint(0, 59))
        elif status == "half_day":
            check_in_time = time(hour=random.randint(8, 10), minute=random.randint(0, 59))
            check_out_time = time(hour=random.randint(12, 14), minute=random.randint(0, 59))
        
        # Random location around Bangalore area
        lat = round(12.9716 + random.uniform(-0.1, 0.1), 6)
        lng = round(77.5946 + random.uniform(-0.1, 0.1), 6)
        
        WorkerAttendance.objects.get_or_create(
            worker=worker,
            date=attendance_date,
            defaults={
                "status": status,
                "check_in": check_in_time,
                "check_out": check_out_time,
                "location_lat": lat if status in ["present", "half_day"] else None,
                "location_lng": lng if status in ["present", "half_day"] else None,
                "notes": "" if status == "present" else f"Auto-generated {status} record",
            }
        )

print("✔ Worker Attendance created (last 30 days for all workers)")


# --------------------------
# Realistic Complaint Titles per Category
# --------------------------
complaint_titles_by_category = {
    "Garbage Collection": [
        "Garbage not collected for 3 days",
        "No garbage pickup in our area",
        "Waste truck not coming regularly",
    ],
    "Street Sweeping": [
        "Street not swept for a week",
        "Leaves piling up on road",
        "Dusty road needs sweeping",
    ],
    "Overflowing Dustbin": [
        "Community dustbin overflowing",
        "Garbage spilling onto road",
        "Dustbin full, needs emptying urgently",
    ],
    "Pothole Repair": [
        "Dangerous pothole on main road",
        "Deep pothole causing accidents",
        "Multiple potholes need repair",
    ],
    "Road Damage": [
        "Road badly damaged after rain",
        "Road surface breaking apart",
        "Cracks appearing on newly laid road",
    ],
    "Footpath Repair": [
        "Broken tiles on footpath",
        "Footpath uneven, risk of tripping",
        "Footpath blocked by construction debris",
    ],
    "Streetlight Not Working": [
        "Streetlight not working near my house",
        "Dark street due to broken light",
        "3 streetlights not working in our lane",
    ],
    "Electrical Fault": [
        "Sparking from electrical pole",
        "Exposed wire on electric pole",
        "Transformer making buzzing sound",
    ],
    "Flickering Light": [
        "Streetlight flickering for past week",
        "Light turns on and off repeatedly",
        "Unstable streetlight needs repair",
    ],
    "Water Leakage": [
        "Water leaking from pipeline",
        "Continuous water leak from main",
        "Water wastage due to broken pipe",
    ],
    "No Water Supply": [
        "No water supply since morning",
        "Water tanker not supplied today",
        "Irregular water supply in our area",
    ],
    "Pipeline Burst": [
        "Main pipeline burst on road",
        "Water gushing from broken pipe",
        "Emergency - pipeline burst flooding area",
    ],
    "Drain Blockage": [
        "Drain blocked causing overflow",
        "Clogged drain near market",
        "Stormwater drain blocked",
    ],
    "Sewage Overflow": [
        "Sewage overflowing onto road",
        "Foul smell from blocked sewer",
        "Sewage line overflow in residential area",
    ],
    "Manhole Issue": [
        "Open manhole dangerous for pedestrians",
        "Broken manhole cover",
        "Missing manhole cover on main road",
    ],
    "Dead Animal Removal": [
        "Dead dog on roadside",
        "Dead cow blocking traffic",
        "Animal carcass needs removal",
    ],
    "Mosquito Fogging": [
        "Mosquito menace in our colony",
        "Request fogging for dengue prevention",
        "Stagnant water breeding mosquitoes",
    ],
    "Stray Animal": [
        "Aggressive stray dogs in area",
        "Stray cattle blocking road",
        "Stray dogs scaring children",
    ],
}

statuses = ["pending", "in_progress", "resolved"]
priorities = [1, 1, 1, 2, 2, 3]  # More normal, fewer high/critical


# --------------------------
# Create Complaints (with proper categories)
# --------------------------
complaints = []
for i in range(50):
    citizen = random.choice(citizens)
    cat_name = random.choice(list(categories.keys()))
    category = categories[cat_name]
    dept = category.department
    
    # Get officers and workers from the same department
    dept_officers = [o for o in officers if o.department == dept]
    dept_workers = [w for w in workers if w.department == dept]
    
    assigned_officer = random.choice(dept_officers) if dept_officers else random.choice(officers)
    assigned_worker = random.choice(dept_workers) if dept_workers else random.choice(workers)

    titles = complaint_titles_by_category.get(cat_name, ["General complaint"])
    title = random.choice(titles)
    
    # Create with varied dates (last 30 days)
    days_ago = random.randint(0, 30)
    created = datetime.now() - timedelta(days=days_ago)

    complaint = Complaint.objects.create(
        user=citizen,
        category=category,
        department=dept,
        title=title,
        description=fake.paragraph(nb_sentences=3),
        status=random.choice(statuses),
        priority=random.choice(priorities),
        location=fake.address(),
        current_officer=assigned_officer,
        current_worker=assigned_worker if random.random() > 0.3 else None,
    )
    complaint.created_at = created
    complaint.save(update_fields=['created_at'])
    complaints.append(complaint)

    # Log entry
    ComplaintLog.objects.create(
        complaint=complaint,
        action_by=assigned_officer.user,
        note="Complaint registered and auto-assigned.",
        old_status="pending",
        new_status=complaint.status,
        old_dept=None,
        new_dept=dept,
        old_assignee="None",
        new_assignee=assigned_worker.user.username if complaint.current_worker else "Unassigned",
    )

    # Assignment history (if worker assigned)
    if complaint.current_worker:
        Assignment.objects.create(
            complaint=complaint,
            assigned_to_worker=assigned_worker,
            assigned_by_officer=assigned_officer,
            status="assigned" if complaint.status == "pending" else "completed" if complaint.status == "resolved" else "in_progress"
        )

print(f"✔ Complaints created ({len(complaints)} complaints with logs)")


# --------------------------
# Create Escalations (for overdue complaints)
# --------------------------
pending_complaints = [c for c in complaints if c.status == "pending"]
for complaint in pending_complaints[:10]:  # Escalate 10 pending complaints
    dept_officers = [o for o in officers if o.department == complaint.department]
    if len(dept_officers) >= 2:
        from_officer = complaint.current_officer
        to_officer = random.choice([o for o in dept_officers if o != from_officer])
        
        ComplaintEscalation.objects.create(
            complaint=complaint,
            escalated_from=from_officer,
            escalated_to=to_officer,
            reason=random.choice([
                "No action taken for 48+ hours",
                "SLA breach - response time exceeded",
                "Citizen follow-up - urgent attention needed",
                "Worker unavailable - reassignment required",
            ])
        )
        
        # Update complaint
        complaint.current_officer = to_officer
        complaint.save()
        
        # Log the escalation
        ComplaintLog.objects.create(
            complaint=complaint,
            action_by=from_officer.user,
            note=f"Escalated to {to_officer.user.get_full_name() or to_officer.user.username}",
            old_status=complaint.status,
            new_status=complaint.status,
            old_assignee=from_officer.user.username,
            new_assignee=to_officer.user.username,
        )

print("✔ Complaint Escalations created")


# --------------------------
# Create Facilities
# --------------------------
facility_data = [
    ("Central Bus Stand Toilet", "public_toilet", "Main Bus Station, City Center"),
    ("Ward 5 Community Toilet", "public_toilet", "Near Market Area, Ward 5"),
    ("Railway Station Toilet Block", "public_toilet", "Platform 1, Railway Station"),
    ("Municipal Office", "govt_building", "City Hall Road, Block A"),
    ("Zonal Office - North", "govt_building", "North Zone Commercial Area"),
    ("Zonal Office - South", "govt_building", "South Zone, Ring Road"),
    ("Gandhi Park", "park", "MG Road, Near Central Library"),
    ("Children's Park - Ward 7", "park", "Residential Area, Ward 7"),
    ("Nehru Garden", "park", "Lake View Road, East Side"),
    ("Central Bus Stop", "bus_stop", "Main Road Junction"),
    ("Hospital Bus Stop", "bus_stop", "Near District Hospital"),
    ("Market Bus Stop", "bus_stop", "Old Market Area"),
    ("Zone A Streetlights", "streetlight_zone", "Industrial Area, Zone A"),
    ("Zone B Streetlights", "streetlight_zone", "Residential Area, Zone B"),
]

facilities = []
for name, ftype, address in facility_data:
    # Assign to appropriate department
    if ftype in ["public_toilet", "park"]:
        dept = departments["Sanitation"]
    elif ftype == "govt_building":
        dept = departments["Roads"]  # Roads dept often handles buildings
    elif ftype == "bus_stop":
        dept = departments["Roads"]
    else:  # streetlight_zone
        dept = departments["Electricity"]
    
    # Get a worker from the department
    dept_workers = workers_by_dept.get(dept.name, workers)
    assigned_worker = random.choice(dept_workers) if dept_workers else None
    
    lat = round(12.9716 + random.uniform(-0.05, 0.05), 6)
    lng = round(77.5946 + random.uniform(-0.05, 0.05), 6)
    
    facility, _ = Facility.objects.get_or_create(
        name=name,
        defaults={
            "facility_type": ftype,
            "address": address,
            "location_lat": lat,
            "location_lng": lng,
            "department": dept,
            "assigned_worker": assigned_worker,
            "is_active": True,
        }
    )
    facilities.append(facility)

print(f"✔ Facilities created ({len(facilities)} facilities)")


# --------------------------
# Create Facility Inspections
# --------------------------
for facility in facilities:
    # Create 3-5 inspections per facility over last 30 days
    num_inspections = random.randint(3, 5)
    dept_workers = [w for w in workers if w.department == facility.department]
    
    for i in range(num_inspections):
        inspection_date = datetime.now() - timedelta(days=random.randint(1, 30))
        inspector = random.choice(dept_workers) if dept_workers else random.choice(workers)
        
        FacilityInspection.objects.create(
            facility=facility,
            inspected_by=inspector,
            cleanliness_rating=random.randint(2, 5),
            functional_status=random.random() > 0.1,  # 90% functional
            issues_found=random.choice([
                "",
                "Minor cleaning required",
                "Water supply issue",
                "Electrical repair needed",
                "Structural damage observed",
                "Graffiti on walls",
                "Broken fixtures",
            ]) if random.random() > 0.5 else "",
            notes=fake.sentence() if random.random() > 0.7 else "",
        )

print("✔ Facility Inspections created")


# --------------------------
# Create Streetlights
# --------------------------
wards = ["Ward-1", "Ward-2", "Ward-3", "Ward-4", "Ward-5"]
statuses_sl = ["functional", "functional", "functional", "non_functional", "under_repair"]

electrical_dept = departments["Electricity"]
electrical_workers = workers_by_dept.get("Electricity", [])

for i in range(50):
    ward = random.choice(wards)
    lat = round(12.9716 + random.uniform(-0.08, 0.08), 6)
    lng = round(77.5946 + random.uniform(-0.08, 0.08), 6)
    
    last_maint = None
    status = random.choice(statuses_sl)
    if status == "functional":
        last_maint = date.today() - timedelta(days=random.randint(30, 180))
    
    Streetlight.objects.get_or_create(
        pole_id=f"SL-{ward[-1]}-{str(i+1).zfill(4)}",
        defaults={
            "location": f"{fake.street_name()}, {ward}",
            "location_lat": lat,
            "location_lng": lng,
            "ward": ward,
            "status": status,
            "last_maintenance": last_maint,
            "assigned_worker": random.choice(electrical_workers) if electrical_workers else None,
            "department": electrical_dept,
        }
    )

print("✔ Streetlights created (50 poles across 5 wards)")


# --------------------------
# Create Admin Superuser
# --------------------------
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email="admin@municipality.gov.in",
        password="admin123",
        first_name="System",
        last_name="Administrator"
    )
    print("✔ Admin superuser created (username: admin, password: admin123)")
else:
    print("✔ Admin superuser already exists")


print("\n" + "="*60)
print("🎉 DEMO DATA LOADED SUCCESSFULLY!")
print("="*60)
print("\n📊 Summary:")
print(f"   • {len(list(departments.values()))} Departments")
print(f"   • {len(list(categories.values()))} Complaint Categories")
print(f"   • {len(officers)} Officers (with hierarchy)")
print(f"   • {len(workers)} Workers")
print(f"   • {len(citizens)} Citizens")
print(f"   • {len(complaints)} Complaints")
print(f"   • {len(facilities)} Facilities")
print(f"   • 50 Streetlights")
print(f"   • ~{len(workers) * 26} Attendance Records (30 days)")
print("\n🔐 Login Credentials:")
print("   Admin:    admin / admin123")
print("   Officers: officer0-17 / 1234")
print("   Workers:  worker0-23 / 1234")
print("   Citizens: citizen0-29 / 1234")
print("\n➡️  Open Admin Panel: http://127.0.0.1:8000/admin/")
print("="*60)
