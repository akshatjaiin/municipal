from rest_framework import serializers
from .models import Complaint, ComplaintLog

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = "__all__"
        read_only_fields = ("status", "current_worker", "current_officer")


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ("title", "description", "location", "department", "image")


class ComplaintLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintLog
        fields = "__all__"
