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
# Officers (Municipal Staff)
# -------------------------
class Officer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, default="officer")

    def __str__(self):
        return self.user.username


# -------------------------
# Workers (Ground Staff)
# -------------------------
class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
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
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50, default="pending")
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to="complaints/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)

    # current assignee
    current_officer = models.ForeignKey(
        Officer, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_complaints"
    )
    current_worker = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name="working_on"
    )

    def __str__(self):
        return f"{self.title} ({self.status})"


# -------------------------
# Assignment (History of Assignment)
# -------------------------
class Assignment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    assigned_to_worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_by_officer = models.ForeignKey(Officer, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50, default="assigned")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment for {self.complaint.id} at {self.timestamp}"


# -------------------------
# Complaint Logs (Blockchain-like History)
# -------------------------
class ComplaintLog(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="logs")

    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)

    old_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)

    old_dept = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="old_dept_logs"
    )
    new_dept = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="new_dept_logs"
    )

    old_assignee = models.CharField(max_length=200, blank=True)
    new_assignee = models.CharField(max_length=200, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log #{self.id} for Complaint {self.complaint.id}"
