from django.contrib import admin
from .models import (
    Department, Officer, Worker,
    Complaint, ComplaintLog, Assignment
)

admin.site.site_header = "Municipal Governance Panel"
admin.site.site_title = "Municipal Admin"


# -----------------------------
# Inline Logs (READ-ONLY)
# -----------------------------
class ComplaintLogInline(admin.TabularInline):
    model = ComplaintLog
    extra = 0
    can_delete = False
    readonly_fields = (
        "action_by", "note",
        "old_status", "new_status",
        "old_dept", "new_dept",
        "timestamp"
    )


# -----------------------------
# Inline Assignments
# -----------------------------
class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    readonly_fields = ("assigned_by_officer", "timestamp")


# -----------------------------
# Department
# -----------------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


# -----------------------------
# Officer
# -----------------------------
@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role")
    list_filter = ("department", "role")
    search_fields = ("user__username",)


# -----------------------------
# Worker
# -----------------------------
@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role", "is_active")
    list_filter = ("department", "role", "is_active")
    search_fields = ("user__username",)


# -----------------------------
# Complaint (CORE VIEW)
# -----------------------------
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "department",
        "priority", "status",
        "current_worker", "created_at"
    )

    list_filter = (
        "department", "status",
        "priority", "is_deleted", "is_spam"
    )

    search_fields = ("title", "description", "user__username")

    ordering = ("-priority", "-created_at")

    inlines = [AssignmentInline, ComplaintLogInline]

    list_per_page = 25

    fieldsets = (
        ("Complaint Info", {
            "fields": ("user", "title", "description", "location", "image")
        }),
        ("Routing & Priority", {
            "fields": ("department", "priority", "status")
        }),
        ("Assignment", {
            "fields": ("current_officer", "current_worker")
        }),
        ("Flags", {
            "fields": ("is_deleted", "is_spam")
        }),
    )

    # 🔐 Department-wise admin visibility
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            return qs.filter(department=request.user.officer.department)
        except:
            return qs.none()


# -----------------------------
# Hide raw logs from main menu
# -----------------------------
@admin.register(ComplaintLog)
class ComplaintLogAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False
