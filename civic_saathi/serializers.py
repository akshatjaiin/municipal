from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Department, ComplaintCategory, Complaint, ComplaintLog,
    Officer, Worker, Facility, FacilityRating
)


# ========================
# User Serializers
# ========================

class UserSerializer(serializers.ModelSerializer):
    """Serialize user data for responses"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """Serialize user registration data"""
    
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 'phone']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('phone', None)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serialize login credentials"""
    
    email = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    """Serialize profile update data"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def validate_email(self, value):
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serialize password change data"""
    
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField()


# ========================
# Department & Category Serializers
# ========================

class DepartmentSerializer(serializers.ModelSerializer):
    """Serialize department data"""
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description']


class CategorySerializer(serializers.ModelSerializer):
    """Serialize complaint category data"""
    
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name', 'department', 'department_id']


# ========================
# Officer & Worker Serializers
# ========================

class OfficerSerializer(serializers.ModelSerializer):
    """Serialize officer data"""
    
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Officer
        fields = ['id', 'name', 'username', 'email', 'role', 'department_name']


class WorkerSerializer(serializers.ModelSerializer):
    """Serialize worker data"""
    
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    phone = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Worker
        fields = ['id', 'name', 'username', 'phone', 'role', 'department_name']
    
    def get_phone(self, obj):
        return "Contact via department"


# ========================
# Complaint Serializers
# ========================

class ComplaintSerializer(serializers.ModelSerializer):
    """Serialize complaint data for list/detail views"""
    
    category = CategorySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    current_officer = OfficerSerializer(read_only=True)
    current_worker = WorkerSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    tracking_id = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()
    created_at_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'tracking_id', 'title', 'description',
            'category', 'department',
            'location', 'latitude', 'longitude',
            'image', 'priority', 'priority_display',
            'status', 'status_display',
            'current_officer', 'current_worker',
            'user_name', 'created_at', 'created_at_display', 'updated_at'
        ]
    
    def get_tracking_id(self, obj):
        return f"CMP-{obj.created_at.year}-{str(obj.id).zfill(5)}"
    
    def get_status_display(self, obj):
        status_map = {
            'pending': 'Pending',
            'assigned': 'Assigned',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'escalated': 'Escalated',
            'closed': 'Closed'
        }
        return status_map.get(obj.status, obj.status.title())
    
    def get_priority_display(self, obj):
        priority_map = {1: 'Normal', 2: 'High', 3: 'Critical'}
        return priority_map.get(obj.priority, 'Normal')
    
    def get_created_at_display(self, obj):
        return obj.created_at.strftime("%b %d, %Y at %I:%M %p")


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Serialize complaint creation data"""
    
    category = serializers.PrimaryKeyRelatedField(
        queryset=ComplaintCategory.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Complaint
        fields = [
            'title', 'description', 'category',
            'location', 'latitude', 'longitude',
            'image', 'priority'
        ]
    
    def validate_title(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Title must be at least 10 characters")
        return value
    
    def validate_description(self, value):
        if len(value) < 20:
            raise serializers.ValidationError("Description must be at least 20 characters")
        return value


class ComplaintLogSerializer(serializers.ModelSerializer):
    """Serialize complaint log/timeline data"""
    
    action_by_name = serializers.SerializerMethodField()
    timestamp_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplaintLog
        fields = [
            'id', 'note', 'old_status', 'new_status',
            'old_assignee', 'new_assignee',
            'action_by_name', 'timestamp', 'timestamp_display'
        ]
    
    def get_action_by_name(self, obj):
        if obj.action_by:
            return obj.action_by.get_full_name() or obj.action_by.username
        return "System"
    
    def get_timestamp_display(self, obj):
        return obj.timestamp.strftime("%b %d, %Y at %I:%M %p")


# ========================
# Facility Serializers
# ========================

class FacilitySerializer(serializers.ModelSerializer):
    """Serialize facility data"""
    
    facility_type_display = serializers.CharField(source='get_facility_type_display', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_ratings = serializers.IntegerField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'facility_type', 'facility_type_display',
            'address', 'latitude', 'longitude',
            'average_rating', 'total_ratings',
            'department_name', 'is_active', 'created_at'
        ]


class FacilityRatingSerializer(serializers.ModelSerializer):
    """Serialize facility rating data"""
    
    user_name = serializers.SerializerMethodField()
    rating_display = serializers.SerializerMethodField()
    created_at_display = serializers.SerializerMethodField()
    
    class Meta:
        model = FacilityRating
        fields = [
            'id', 'cleanliness_rating', 'rating_display',
            'comment', 'photo', 'is_anonymous',
            'user_name', 'created_at', 'created_at_display'
        ]
    
    def get_user_name(self, obj):
        if obj.is_anonymous or not obj.user:
            return "Anonymous"
        return obj.user.get_full_name() or obj.user.username
    
    def get_rating_display(self, obj):
        return "⭐" * obj.cleanliness_rating
    
    def get_created_at_display(self, obj):
        return obj.created_at.strftime("%b %d, %Y")