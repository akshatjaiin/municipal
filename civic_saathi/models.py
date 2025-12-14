from django.db import models
from django.contrib.auth.models import User


# -------------------------
# Departments
# -------------------------
class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# -------------------------
# Complaint Categories
# (maps problem → department)
# -------------------------
class ComplaintCategory(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.department.name})"


# -------------------------
# Officers (Dept Admins)
# -------------------------
class Officer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default="officer")

    def __str__(self):
        return self.user.username


# -------------------------
# Workers (Ground Staff)
# -------------------------
class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# -------------------------
# Complaint (Current State)
# -------------------------
class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # citizen

    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True  # Made optional - can file complaint without selecting category
    )
    
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to="complaints/", blank=True, null=True)

    # ✅ ADD THIS
    priority = models.PositiveSmallIntegerField(
        default=1,
        help_text="1=Normal, 2=High, 3=Critical"
    )

    status = models.CharField(max_length=50, default="pending")

    current_officer = models.ForeignKey(
        Officer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints"
    )

    current_worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_work"
    )

    is_deleted = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.category and not self.department:
            self.department = self.category.department
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.status})"
        

# -------------------------
# Assignment History
# -------------------------
class Assignment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    assigned_to_worker = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_by_officer = models.ForeignKey(
        Officer, on_delete=models.SET_NULL, null=True
    )
    status = models.CharField(max_length=50, default="assigned")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment for Complaint {self.complaint.id}"


# -------------------------
# Complaint Logs (Immutable History)
# -------------------------
class ComplaintLog(models.Model):
    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE, related_name="logs"
    )

    action_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )

    note = models.TextField(blank=True)

    old_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)

    old_dept = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="old_logs"
    )

    new_dept = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="new_logs"
    )

    old_assignee = models.CharField(max_length=200, blank=True)
    new_assignee = models.CharField(max_length=200, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id} - Complaint {self.complaint.id}"
    

class ComplaintEscalation(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    escalated_from = models.ForeignKey(
        Officer, on_delete=models.SET_NULL, null=True, related_name="escalated_from"
    )
    escalated_to = models.ForeignKey(
        Officer, on_delete=models.SET_NULL, null=True, related_name="escalated_to"
    )
    reason = models.CharField(max_length=255)
    escalated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Escalation #{self.id} - Complaint {self.complaint_id}"


# -------------------------
# Worker Attendance
# -------------------------
class WorkerAttendance(models.Model):
    ATTENDANCE_STATUS = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("half_day", "Half Day"),
        ("on_leave", "On Leave"),
    ]

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default="present")
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("worker", "date")
        ordering = ["-date"]
        verbose_name_plural = "Worker Attendance"

    def __str__(self):
        return f"{self.worker.user.username} - {self.date} ({self.status})"


# -------------------------
# Facility (Toilets, Buildings, etc.)
# -------------------------
class Facility(models.Model):
    FACILITY_TYPES = [
        ("public_toilet", "Public Toilet"),
        ("govt_building", "Government Building"),
        ("park", "Park"),
        ("bus_stop", "Bus Stop"),
        ("streetlight_zone", "Streetlight Zone"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200)
    facility_type = models.CharField(max_length=50, choices=FACILITY_TYPES)
    address = models.TextField()
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="facilities")
    assigned_worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name="facilities")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Facilities"

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"
    
    @property
    def average_rating(self):
        """Get average cleanliness rating from public reviews"""
        ratings = self.public_ratings.all()
        if not ratings.exists():
            return None
        return round(sum(r.cleanliness_rating for r in ratings) / ratings.count(), 1)
    
    @property
    def total_ratings(self):
        return self.public_ratings.count()


# -------------------------
# Public Facility Rating (by Citizens)
# -------------------------
class FacilityRating(models.Model):
    """
    Citizens can rate cleanliness of public facilities.
    This is separate from staff inspections.
    """
    RATING_CHOICES = [
        (1, "⭐ Very Poor"),
        (2, "⭐⭐ Poor"),
        (3, "⭐⭐⭐ Average"),
        (4, "⭐⭐⭐⭐ Good"),
        (5, "⭐⭐⭐⭐⭐ Excellent"),
    ]
    
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="public_ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Can be anonymous
    cleanliness_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, help_text="Optional feedback")
    photo = models.ImageField(upload_to="facility_ratings/", blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For verification
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_verified = models.BooleanField(default=False, help_text="Verified by staff")
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Public Rating"
        verbose_name_plural = "Public Ratings"
    
    def __str__(self):
        return f"{self.facility.name} - {'⭐' * self.cleanliness_rating} by {self.user or 'Anonymous'}"


# -------------------------
# Facility Inspection Log (Staff)
# -------------------------
class FacilityInspection(models.Model):
    CLEANLINESS_RATING = [
        (1, "Very Poor"),
        (2, "Poor"),
        (3, "Average"),
        (4, "Good"),
        (5, "Excellent"),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="inspections")
    inspected_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True)
    inspection_date = models.DateTimeField(auto_now_add=True)
    cleanliness_rating = models.PositiveSmallIntegerField(choices=CLEANLINESS_RATING, default=3)
    functional_status = models.BooleanField(default=True, help_text="Is facility functional?")
    issues_found = models.TextField(blank=True)
    photo = models.ImageField(upload_to="inspections/", blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-inspection_date"]

    def __str__(self):
        return f"Inspection of {self.facility.name} on {self.inspection_date.date()}"


# -------------------------
# SLA Configuration (per category)
# -------------------------
class SLAConfig(models.Model):
    category = models.OneToOneField(ComplaintCategory, on_delete=models.CASCADE, related_name="sla")
    resolution_hours = models.PositiveIntegerField(default=48, help_text="Hours to resolve before escalation")
    escalation_hours = models.PositiveIntegerField(default=72, help_text="Hours before escalating to senior officer")

    def __str__(self):
        return f"SLA for {self.category.name}: {self.resolution_hours}h"


# -------------------------
# Streetlight specific tracking
# -------------------------
class Streetlight(models.Model):
    STATUS_CHOICES = [
        ("functional", "Functional"),
        ("non_functional", "Non-Functional"),
        ("under_repair", "Under Repair"),
    ]

    pole_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    ward = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="functional")
    last_maintenance = models.DateField(null=True, blank=True)
    assigned_worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="streetlights")

    def __str__(self):
        return f"Pole {self.pole_id} - {self.status}"
