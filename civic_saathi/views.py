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
