import os
import django
import random
from faker import Faker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "municipal.settings")
django.setup()
from django.contrib.auth.models import User
from civic_saathi.models import Department, Officer, Worker, Complaint, ComplaintLog, Assignment
from faker import Faker
import random

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

departments = []
for (name, desc) in dept_data:
    d, _ = Department.objects.get_or_create(name=name, description=desc)
    departments.append(d)

print("✔ Departments created")


# --------------------------
# Create Officers
# --------------------------
officers = []
for i in range(6):
    user = User.objects.create_user(
        username=f"officer{i}",
        email=f"officer{i}@gov.in",
        password="1234",
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )
    officer = Officer.objects.create(
        user=user,
        department=random.choice(departments),
        role=random.choice(["Supervisor", "Dept Head", "Zonal Officer"])
    )
    officers.append(officer)

print("✔ Officers created")


# --------------------------
# Create Workers
# --------------------------
roles = ["Electrician", "Plumber", "Sweeper", "Road Repair Agent", "Drain Cleaner", "Field Worker"]
workers = []

for i in range(20):
    user = User.objects.create_user(
        username=f"worker{i}",
        email=f"worker{i}@gov.in",
        password="1234",
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )
    worker = Worker.objects.create(
        user=user,
        department=random.choice(departments),
        role=random.choice(roles),
        address=fake.address(),
        joining_date=fake.date_this_decade(),
        is_active=True
    )
    workers.append(worker)

print("✔ Workers created")


# --------------------------
# Create Citizens
# --------------------------
citizens = []
for i in range(30):
    user = User.objects.create_user(
        username=f"citizen{i}",
        email=f"citizen{i}@mail.com",
        password="1234",
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )
    citizens.append(user)

print("✔ Citizens created")


# --------------------------
# Realistic Complaint Titles
# --------------------------
complaint_titles = [
    "Streetlight not working near my house",
    "Garbage not picked up for 3 days",
    "Major pothole near main road",
    "Water leakage from pipeline",
    "Dead dog on roadside",
    "Drain blocked causing overflow",
    "Streetlight flickering for past week",
    "Broken manhole cover",
    "Garbage dump overflowing",
    "Water tanker not supplied today",
]

statuses = ["pending", "in_progress", "resolved"]


# --------------------------
# Create Complaints
# --------------------------
for i in range(50):
    citizen = random.choice(citizens)
    dept = random.choice(departments)
    assigned_officer = random.choice(officers)
    assigned_worker = random.choice(workers)

    title = random.choice(complaint_titles)

    complaint = Complaint.objects.create(
        user=citizen,
        department=dept,
        title=title,
        description=fake.paragraph(nb_sentences=3),
        status=random.choice(statuses),
        location=fake.address(),
        current_officer=assigned_officer,
        current_worker=assigned_worker,
    )

    # Log entry
    ComplaintLog.objects.create(
        complaint=complaint,
        action_by=assigned_officer.user,
        note="Auto-assigned during demo data generation.",
        old_status="pending",
        new_status=complaint.status,
        old_dept=None,
        new_dept=dept,
        old_assignee="None",
        new_assignee=assigned_worker.user.username,
    )

    # Assignment history
    Assignment.objects.create(
        complaint=complaint,
        assigned_to_worker=assigned_worker,
        assigned_by_officer=assigned_officer,
        status="assigned"
    )

print("✔ Complaints + Logs + Assignments created")
print("🎉 DEMO DATA LOADED SUCCESSFULLY — Refresh Admin Panel!")
