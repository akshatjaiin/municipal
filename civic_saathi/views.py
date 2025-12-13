from rest_framework import generics, permissions
from .models import Complaint, ComplaintLog
from .serializers import (
    ComplaintSerializer,
    ComplaintCreateSerializer,
    ComplaintLogSerializer
)

# ---------------------------
# User creates a complaint
# POST /api/complaints/create/
# ---------------------------
class ComplaintCreateView(generics.CreateAPIView):
    serializer_class = ComplaintCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)   # auto-attach user


# ---------------------------
# User sees ALL his complaints
# GET /api/complaints/my/
# ---------------------------
class MyComplaintsView(generics.ListAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Complaint.objects.filter(user=self.request.user)


# ---------------------------
# Complaint detail + progress
# GET /api/complaints/<id>/
# ---------------------------
class ComplaintDetailView(generics.RetrieveAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]


# ---------------------------
# Logs for tracking progress
# GET /api/complaints/<id>/logs/
# ---------------------------
class ComplaintLogsView(generics.ListAPIView):
    serializer_class = ComplaintLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ComplaintLog.objects.filter(
            complaint_id=self.kwargs["pk"]
        ).order_by("-timestamp")


# ---------------------------
# Admin View: Mark Attendance
# ---------------------------
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from .models import Worker, WorkerAttendance, Department, Officer

@staff_member_required
def mark_attendance_view(request):
    """
    Simple view for Officers to mark attendance for their workers.
    """
    today = timezone.now().date()
    
    # Determine the department of the logged-in user
    user = request.user
    department = None
    
    if hasattr(user, 'officer'):
        department = user.officer.department
    
    # Filter workers
    workers = Worker.objects.filter(is_active=True)
    if department:
        workers = workers.filter(department=department)
        
    if request.method == "POST":
        # Process the form
        for worker in workers:
            status_key = f"status_{worker.id}"
            notes_key = f"notes_{worker.id}"
            
            status = request.POST.get(status_key)
            notes = request.POST.get(notes_key, "")
            
            if status:
                WorkerAttendance.objects.update_or_create(
                    worker=worker,
                    date=today,
                    defaults={
                        'status': status,
                        'notes': notes,
                        'marked_by': user
                    }
                )
        messages.success(request, f"Attendance marked for {today}")
        return redirect('admin:index')

    # Get existing attendance for today to pre-fill
    existing_attendance = WorkerAttendance.objects.filter(date=today, worker__in=workers)
    attendance_map = {att.worker_id: att for att in existing_attendance}
    
    context = {
        'workers': workers,
        'today': today,
        'department': department,
        'attendance_map': attendance_map,
        'title': 'Mark Daily Attendance',
        'site_header': 'Civic Saathi Admin',
        'site_title': 'Civic Saathi Admin',
    }
    return render(request, 'admin/mark_attendance.html', context)

