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
        null=True
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
