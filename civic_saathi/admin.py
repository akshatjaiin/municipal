from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from .models import (
    Department, Officer, Worker,
    Complaint, ComplaintLog, Assignment, ComplaintCategory,
    ComplaintEscalation, WorkerAttendance, Facility, FacilityInspection,
    SLAConfig, Streetlight
)
# Email notification service
from .email_service import (
    send_complaint_registered_email,
    send_worker_assignment_email,
    send_status_update_email,
    send_escalation_email
)

# Use custom admin site for dashboard stats
from .admin_site import municipal_admin

# Override default admin site
admin.site = municipal_admin
admin.sites.site = municipal_admin

admin.site.site_header = "🏛️ Municipal Governance Panel"
admin.site.site_title = "Municipal Admin"
admin.site.index_title = "Dashboard"


# -----------------------------
# Base class for department filtering
# -----------------------------
class DepartmentFilteredAdmin(admin.ModelAdmin):
    """Base admin that filters queryset by user's department"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Check if user is an officer
        if hasattr(request.user, 'officer'):
            return qs.filter(department=request.user.officer.department)
        # Check if user is a worker
        if hasattr(request.user, 'worker'):
            return qs.filter(department=request.user.worker.department)
        return qs.none()


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
        "old_assignee", "new_assignee",
        "timestamp"
    )

    def has_add_permission(self, request, obj=None):
        return False


# -----------------------------
# Inline Assignments
# -----------------------------
class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    readonly_fields = ("assigned_by_officer", "timestamp")


# -----------------------------
# Inline Escalations
# -----------------------------
class EscalationInline(admin.TabularInline):
    model = ComplaintEscalation
    extra = 0
    readonly_fields = ("escalated_from", "escalated_to", "reason", "escalated_at")

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser or hasattr(request.user, 'officer')


# -----------------------------
# Department
# -----------------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "officer_count", "worker_count", "open_complaints")
    search_fields = ("name",)

    def officer_count(self, obj):
        return obj.officer_set.count()
    officer_count.short_description = "Officers"

    def worker_count(self, obj):
        return obj.worker_set.count()
    worker_count.short_description = "Workers"

    def open_complaints(self, obj):
        count = Complaint.objects.filter(department=obj, status__in=["pending", "in_progress"]).count()
        if count > 10:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return count
    open_complaints.short_description = "Open Issues"


# -----------------------------
# Complaint Category
# -----------------------------
@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "has_sla")
    list_filter = ("department",)
    search_fields = ("name",)

    def has_sla(self, obj):
        return hasattr(obj, 'sla')
    has_sla.boolean = True
    has_sla.short_description = "SLA Set"


# -----------------------------
# Officer
# -----------------------------
@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role", "assigned_complaints", "pending_escalations")
    list_filter = ("department", "role")
    search_fields = ("user__username", "user__email")

    def assigned_complaints(self, obj):
        return obj.complaints.filter(status__in=["pending", "in_progress"]).count()
    assigned_complaints.short_description = "Active Cases"

    def pending_escalations(self, obj):
        return ComplaintEscalation.objects.filter(escalated_to=obj).count()
    pending_escalations.short_description = "Escalations"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'officer'):
            return qs.filter(department=request.user.officer.department)
        return qs.none()


# -----------------------------
# Worker
# -----------------------------
@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role", "is_active", "today_attendance", "active_tasks")
    list_filter = ("department", "role", "is_active")
    search_fields = ("user__username",)
    list_editable = ("is_active",)

    def today_attendance(self, obj):
        today = timezone.now().date()
        att = obj.attendance_records.filter(date=today).first()
        if att:
            color = {"present": "green", "absent": "red", "half_day": "orange", "on_leave": "blue"}.get(att.status, "gray")
            return format_html('<span style="color: {};">{}</span>', color, att.get_status_display())
        return format_html('<span style="color: gray;">Not Marked</span>')
    today_attendance.short_description = "Today"

    def active_tasks(self, obj):
        return obj.assigned_work.filter(status__in=["pending", "in_progress"]).count()
    active_tasks.short_description = "Tasks"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'officer'):
            return qs.filter(department=request.user.officer.department)
        if hasattr(request.user, 'worker'):
            return qs.filter(id=request.user.worker.id)
        return qs.none()


# -----------------------------
# Worker Attendance
# -----------------------------
@admin.register(WorkerAttendance)
class WorkerAttendanceAdmin(admin.ModelAdmin):
    list_display = ("worker", "date", "status_colored", "check_in", "check_out", "marked_by")
    list_filter = ("status", "date", "worker__department")
    search_fields = ("worker__user__username",)
    date_hierarchy = "date"
    list_per_page = 50

    fieldsets = (
        ("Attendance Info", {
            "fields": ("worker", "date", "status")
        }),
        ("Time Tracking", {
            "fields": ("check_in", "check_out")
        }),
        ("Location (Optional)", {
            "fields": ("location_lat", "location_lng"),
            "classes": ("collapse",)
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
    )

    def status_colored(self, obj):
        colors = {"present": "green", "absent": "red", "half_day": "orange", "on_leave": "blue"}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, "gray"),
            obj.get_status_display()
        )
    status_colored.short_description = "Status"

    def save_model(self, request, obj, form, change):
        if not obj.marked_by:
            obj.marked_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'officer'):
            return qs.filter(worker__department=request.user.officer.department)
        if hasattr(request.user, 'worker'):
            return qs.filter(worker=request.user.worker)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "worker" and not request.user.is_superuser:
            if hasattr(request.user, 'officer'):
                kwargs["queryset"] = Worker.objects.filter(department=request.user.officer.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# -----------------------------
# Complaint (CORE VIEW)
# -----------------------------
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "department",
        "priority_badge", "status_badge",
        "current_worker", "sla_status", "created_at"
    )

    list_filter = (
        "department", "status",
        "priority", "category", "is_deleted", "is_spam"
    )

    search_fields = ("title", "description", "user__username", "location")

    ordering = ("-priority", "-created_at")

    inlines = [AssignmentInline, EscalationInline, ComplaintLogInline]

    list_per_page = 25

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Complaint Info", {
            "fields": ("user", "title", "description", "location", "image", "category")
        }),
        ("Routing & Priority", {
            "fields": ("department", "priority", "status")
        }),
        ("Assignment", {
            "fields": ("current_officer", "current_worker")
        }),
        ("Flags", {
            "fields": ("is_deleted", "is_spam"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    actions = ["mark_resolved", "mark_in_progress", "escalate_to_senior"]

    def priority_badge(self, obj):
        colors = {1: "#28a745", 2: "#ffc107", 3: "#dc3545"}
        labels = {1: "Normal", 2: "High", 3: "Critical"}
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.priority, "#6c757d"),
            labels.get(obj.priority, "Unknown")
        )
    priority_badge.short_description = "Priority"

    def status_badge(self, obj):
        colors = {
            "pending": "#ffc107",
            "in_progress": "#17a2b8",
            "resolved": "#28a745",
            "closed": "#6c757d",
            "escalated": "#dc3545"
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.status.replace("_", " ").title()
        )
    status_badge.short_description = "Status"

    def sla_status(self, obj):
        if not obj.category or not hasattr(obj.category, 'sla'):
            return "-"
        sla = obj.category.sla
        elapsed = timezone.now() - obj.created_at
        hours_elapsed = elapsed.total_seconds() / 3600
        if obj.status in ["resolved", "closed"]:
            return format_html('<span style="color: green;">✓ Done</span>')
        if hours_elapsed > sla.escalation_hours:
            return format_html('<span style="color: red; font-weight: bold;">⚠ OVERDUE</span>')
        if hours_elapsed > sla.resolution_hours:
            return format_html('<span style="color: orange;">⏰ Escalate</span>')
        remaining = sla.resolution_hours - hours_elapsed
        return format_html('<span style="color: green;">{}h left</span>', int(remaining))
    sla_status.short_description = "SLA"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'officer'):
            return qs.filter(department=request.user.officer.department)
        if hasattr(request.user, 'worker'):
            return qs.filter(current_worker=request.user.worker)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and hasattr(request.user, 'officer'):
            dept = request.user.officer.department
            if db_field.name == "current_worker":
                kwargs["queryset"] = Worker.objects.filter(department=dept)
            if db_field.name == "current_officer":
                kwargs["queryset"] = Officer.objects.filter(department=dept)
            if db_field.name == "category":
                kwargs["queryset"] = ComplaintCategory.objects.filter(department=dept)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        is_new = not change
        old_status = None
        old_worker = None
        
        if change:
            # Get old values before save
            old_obj = Complaint.objects.get(pk=obj.pk)
            old_status = old_obj.status
            old_worker = old_obj.current_worker
            
            if old_obj.status != obj.status or old_obj.current_worker != obj.current_worker:
                ComplaintLog.objects.create(
                    complaint=obj,
                    action_by=request.user,
                    old_status=old_obj.status,
                    new_status=obj.status,
                    old_assignee=str(old_obj.current_worker) if old_obj.current_worker else "",
                    new_assignee=str(obj.current_worker) if obj.current_worker else "",
                    note=f"Updated by {request.user.username}"
                )
        
        super().save_model(request, obj, form, change)
        
        # Send email notifications
        try:
            if is_new:
                # New complaint registered
                if send_complaint_registered_email(obj):
                    messages.success(request, f"📧 Email notification sent for new complaint #{obj.id}")
            else:
                # Worker assignment changed
                if obj.current_worker and obj.current_worker != old_worker:
                    results = send_worker_assignment_email(obj, obj.current_worker, request.user)
                    if results:
                        messages.success(request, f"📧 Worker assignment emails sent for complaint #{obj.id}")
                
                # Status changed
                if old_status and old_status != obj.status:
                    if send_status_update_email(obj, old_status, obj.status, request.user):
                        messages.success(request, f"📧 Status update email sent for complaint #{obj.id}")
        except Exception as e:
            messages.warning(request, f"⚠️ Could not send email notification: {str(e)}")

    @admin.action(description="Mark selected as Resolved")
    def mark_resolved(self, request, queryset):
        count = 0
        for complaint in queryset:
            old_status = complaint.status
            complaint.status = "resolved"
            complaint.save()
            count += 1
            try:
                send_status_update_email(complaint, old_status, "resolved", request.user)
            except Exception:
                pass
        messages.success(request, f"✅ {count} complaint(s) marked as resolved. Email notifications sent.")

    @admin.action(description="Mark selected as In Progress")
    def mark_in_progress(self, request, queryset):
        count = 0
        for complaint in queryset:
            old_status = complaint.status
            complaint.status = "in_progress"
            complaint.save()
            count += 1
            try:
                send_status_update_email(complaint, old_status, "in_progress", request.user)
            except Exception:
                pass
        messages.success(request, f"🔄 {count} complaint(s) marked as in progress. Email notifications sent.")

    @admin.action(description="Escalate to Senior Officer")
    def escalate_to_senior(self, request, queryset):
        count = 0
        for complaint in queryset:
            complaint.status = "escalated"
            complaint.priority = 3
            complaint.save()
            count += 1
            if hasattr(request.user, 'officer'):
                escalation = ComplaintEscalation.objects.create(
                    complaint=complaint,
                    escalated_from=request.user.officer,
                    reason="Bulk escalation by officer"
                )
                try:
                    send_escalation_email(complaint, escalation)
                except Exception:
                    pass
        messages.success(request, f"⚠️ {count} complaint(s) escalated. Notifications sent to senior officers.")


# -----------------------------
# Escalation Admin
# -----------------------------
@admin.register(ComplaintEscalation)
class ComplaintEscalationAdmin(admin.ModelAdmin):
    list_display = ("complaint", "escalated_from", "escalated_to", "reason", "escalated_at")
    list_filter = ("escalated_at",)
    search_fields = ("complaint__title", "reason")
    readonly_fields = ("escalated_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'officer'):
            return qs.filter(complaint__department=request.user.officer.department)
        return qs.none()


# -----------------------------
# Facility Admin
# -----------------------------
@admin.register(Facility)
class FacilityAdmin(DepartmentFilteredAdmin):
    list_display = ("name", "facility_type", "department", "assigned_worker", "is_active", "last_inspection")
    list_filter = ("facility_type", "department", "is_active")
    search_fields = ("name", "address")

    def last_inspection(self, obj):
        insp = obj.inspections.first()
        if insp:
            return insp.inspection_date.date()
        return "-"
    last_inspection.short_description = "Last Checked"


# -----------------------------
# Facility Inspection
# -----------------------------
@admin.register(FacilityInspection)
class FacilityInspectionAdmin(admin.ModelAdmin):
    list_display = ("facility", "inspected_by", "inspection_date", "rating_stars", "functional_status")
    list_filter = ("cleanliness_rating", "functional_status", "facility__facility_type")
    search_fields = ("facility__name",)
    date_hierarchy = "inspection_date"

    def rating_stars(self, obj):
        stars = "★" * obj.cleanliness_rating + "☆" * (5 - obj.cleanliness_rating)
        colors = {1: "red", 2: "orange", 3: "gold", 4: "yellowgreen", 5: "green"}
        return format_html('<span style="color: {};">{}</span>', colors.get(obj.cleanliness_rating), stars)
    rating_stars.short_description = "Cleanliness"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'officer'):
            return qs.filter(facility__department=request.user.officer.department)
        if hasattr(request.user, 'worker'):
            return qs.filter(inspected_by=request.user.worker)
        return qs.none()


# -----------------------------
# SLA Config
# -----------------------------
@admin.register(SLAConfig)
class SLAConfigAdmin(admin.ModelAdmin):
    list_display = ("category", "resolution_hours", "escalation_hours")
    list_filter = ("category__department",)


# -----------------------------
# Streetlight Admin
# -----------------------------
@admin.register(Streetlight)
class StreetlightAdmin(DepartmentFilteredAdmin):
    list_display = ("pole_id", "location", "ward", "status_badge", "assigned_worker", "last_maintenance")
    list_filter = ("status", "department", "ward")
    search_fields = ("pole_id", "location")
    list_editable = ("assigned_worker",)

    def status_badge(self, obj):
        colors = {"functional": "green", "non_functional": "red", "under_repair": "orange"}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, "gray"),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"


# -----------------------------
# Hide raw logs from main menu
# -----------------------------
@admin.register(ComplaintLog)
class ComplaintLogAdmin(admin.ModelAdmin):
    list_display = ("complaint", "action_by", "old_status", "new_status", "timestamp")
    list_filter = ("timestamp",)
    readonly_fields = ("complaint", "action_by", "old_status", "new_status", "old_dept", "new_dept", "timestamp")

    def has_module_permission(self, request):
        return request.user.is_superuser  # Only superusers see logs in menu

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
