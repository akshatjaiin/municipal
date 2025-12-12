from django.contrib import admin

from .models import (
    Department, Officer, Worker,
    Complaint, ComplaintLog, Assignment
)

admin.site.site_header = "Municipal Admin Panel"
admin.site.site_title = "Municipal Admin"


# -----------------------------
# Department
# -----------------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


# -----------------------------
# Officer
# -----------------------------
@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "department", "role")
    list_filter = ("department", "role")
    search_fields = ("user__username", "user__first_name", "user__last_name")


# -----------------------------
# Worker
# -----------------------------
@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "department", "role", "is_active", "joining_date")
    list_filter = ("department", "role", "is_active")
    search_fields = ("user__username", "role")


# -----------------------------
# Complaint
# -----------------------------
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "user", "department",
        "status", "current_officer", "current_worker",
        "created_at", "updated_at"
    )
    list_filter = ("department", "status")
    search_fields = ("title", "description", "user__username")
    list_per_page = 20


# -----------------------------
# Assignment (History)
# -----------------------------
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "complaint", "assigned_to_worker",
        "assigned_by_officer", "status", "timestamp"
    )
    list_filter = ("status", "assigned_by_officer", "assigned_to_worker")
    search_fields = ("complaint__title",)


# -----------------------------
# Complaint Logs (Blockchain-like)
# -----------------------------
@admin.register(ComplaintLog)
class ComplaintLogAdmin(admin.ModelAdmin):
    list_display = (
        "id", "complaint", "action_by", "note",
        "old_status", "new_status", "old_dept",
        "new_dept", "timestamp"
    )
    list_filter = ("new_status", "new_dept")
    search_fields = ("complaint__title", "action_by__username")
    list_per_page = 30
