"""
Fix officer permissions - Give them full model access with department-filtered data.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'municipal.settings')
django.setup()

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from civic_saathi.models import (
    Department, Officer, Worker, Complaint, ComplaintCategory,
    ComplaintLog, ComplaintEscalation, Assignment, WorkerAttendance,
    Facility, FacilityInspection, SLAConfig, Streetlight
)

# Models that officers should have FULL access to
FULL_ACCESS_MODELS = [
    Complaint,
    ComplaintCategory, 
    ComplaintLog,
    ComplaintEscalation,
    Assignment,
    Worker,
    WorkerAttendance,
    Facility,
    FacilityInspection,
    Streetlight,
]

# Models officers can VIEW only
VIEW_ONLY_MODELS = [
    Department,
    Officer,
    SLAConfig,
]

print("\n" + "="*60)
print("🔐 SETTING UP OFFICER PERMISSIONS")
print("="*60)

# Get all officers
officers = Officer.objects.all()
print(f"\nFound {officers.count()} officers")

for officer in officers:
    user = officer.user
    print(f"\n👤 {user.username} ({officer.department.name})")
    
    # Clear existing permissions
    user.user_permissions.clear()
    
    permissions_added = []
    
    # Add FULL permissions for main models
    for model in FULL_ACCESS_MODELS:
        ct = ContentType.objects.get_for_model(model)
        for action in ['add', 'change', 'delete', 'view']:
            codename = f"{action}_{model._meta.model_name}"
            try:
                perm = Permission.objects.get(content_type=ct, codename=codename)
                user.user_permissions.add(perm)
                permissions_added.append(codename)
            except Permission.DoesNotExist:
                print(f"   ⚠️ Permission not found: {codename}")
    
    # Add VIEW permissions for admin models
    for model in VIEW_ONLY_MODELS:
        ct = ContentType.objects.get_for_model(model)
        codename = f"view_{model._meta.model_name}"
        try:
            perm = Permission.objects.get(content_type=ct, codename=codename)
            user.user_permissions.add(perm)
            permissions_added.append(codename)
        except Permission.DoesNotExist:
            print(f"   ⚠️ Permission not found: {codename}")
    
    # Also add User view permission (to see citizens who filed complaints)
    ct = ContentType.objects.get_for_model(User)
    perm = Permission.objects.get(content_type=ct, codename='view_user')
    user.user_permissions.add(perm)
    
    user.save()
    print(f"   ✅ Added {len(permissions_added)} permissions")

print("\n" + "="*60)
print("✅ ALL OFFICERS NOW HAVE FULL UI ACCESS!")
print("="*60)
print("""
Officers can now:
✅ See full admin UI (same as superuser)
✅ Add/Edit/Delete Complaints (only their department)
✅ Manage Workers (only their department)
✅ Mark Attendance (only their workers)
✅ Manage Facilities (only their department)
✅ View Departments and SLA configs

Data is still FILTERED by department - they only see their own data!
""")
