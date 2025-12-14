from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import (
    Complaint, ComplaintLog, ComplaintCategory, Department,
    Worker, WorkerAttendance, Facility, FacilityRating
)
from .serializers import (
    UserSerializer, RegisterSerializer, ProfileSerializer,
    ComplaintSerializer, ComplaintCreateSerializer, ComplaintLogSerializer,
    CategorySerializer, DepartmentSerializer,
    FacilitySerializer, FacilityRatingSerializer,
)

import random
import string


# ========================
# Home Page View
# ========================

def home_view(request):
    """Render the beautiful home page with stats"""
    context = {
        'total_complaints': Complaint.objects.count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_facilities': Facility.objects.count(),
        'resolved_complaints': Complaint.objects.filter(status='resolved').count(),
    }
    return render(request, 'home.html', context)


# ========================
# OTP Storage (In production, use Redis or DB)
# ========================
otp_storage = {}


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


# ========================
# Authentication Views
# ========================

class RegisterView(APIView):
    """Register a new citizen user."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                "success": True,
                "message": "Registration successful!",
                "data": {
                    "user": UserSerializer(user).data,
                    "token": token.key
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "message": "Registration failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Login with email/username and password."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email_or_username = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')
        
        if not email_or_username or not password:
            return Response({
                "success": False,
                "message": "Email/Username and password are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find user by email or username
        user = None
        if '@' in email_or_username:
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(username=email_or_username, password=password)
        
        if user:
            if not user.is_active:
                return Response({
                    "success": False,
                    "message": "Account is disabled. Please contact support."
                }, status=status.HTTP_403_FORBIDDEN)
            
            token, _ = Token.objects.get_or_create(user=user)
            
            # Check if user is officer or worker
            user_type = "citizen"
            department = None
            
            if hasattr(user, 'officer'):
                user_type = "officer"
                department = user.officer.department.name
            elif hasattr(user, 'worker'):
                user_type = "worker"
                department = user.worker.department.name
            
            return Response({
                "success": True,
                "message": "Login successful!",
                "data": {
                    "user": UserSerializer(user).data,
                    "token": token.key,
                    "user_type": user_type,
                    "department": department
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "message": "Invalid credentials"
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """Logout - Invalidate the auth token."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({
                "success": True,
                "message": "Logged out successfully"
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                "success": False,
                "message": "Something went wrong"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(APIView):
    """Get or update user profile."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user stats
        total_complaints = Complaint.objects.filter(user=user).count()
        resolved_complaints = Complaint.objects.filter(user=user, status='resolved').count()
        pending_complaints = Complaint.objects.filter(
            user=user, status__in=['pending', 'assigned', 'in_progress']
        ).count()
        
        # Check user type
        user_type = "citizen"
        department = None
        role = None
        
        if hasattr(user, 'officer'):
            user_type = "officer"
            department = user.officer.department.name
            role = user.officer.role
        elif hasattr(user, 'worker'):
            user_type = "worker"
            department = user.worker.department.name
            role = user.worker.role
        
        return Response({
            "success": True,
            "data": {
                "user": UserSerializer(user).data,
                "user_type": user_type,
                "department": department,
                "role": role,
                "stats": {
                    "total_complaints": total_complaints,
                    "resolved_complaints": resolved_complaints,
                    "pending_complaints": pending_complaints
                }
            }
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Profile updated successfully",
                "data": {"user": UserSerializer(user).data}
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "message": "Update failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change password for logged-in user."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return Response({
                "success": False,
                "message": "All fields are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                "success": False,
                "message": "New passwords do not match"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(old_password):
            return Response({
                "success": False,
                "message": "Current password is incorrect"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 6:
            return Response({
                "success": False,
                "message": "Password must be at least 6 characters"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        # Delete old token and create new one
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        return Response({
            "success": True,
            "message": "Password changed successfully",
            "data": {"token": token.key}
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """Send OTP to email for password reset."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                "success": False,
                "message": "Email is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "success": True,
                "message": "If this email exists, you will receive an OTP"
            }, status=status.HTTP_200_OK)
        
        # Generate and store OTP
        otp = generate_otp()
        otp_storage[email] = {
            'otp': otp,
            'created_at': timezone.now(),
            'user_id': user.id
        }
        
        # Send OTP email
        try:
            send_mail(
                subject='🔐 Password Reset OTP - Nagar Nigam Jaipur',
                message=f'''
Hello {user.first_name or user.username},

Your OTP for password reset is: {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.

Regards,
Nagar Nigam Jaipur
Civic Saathi Portal
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email send error: {e}")
        
        return Response({
            "success": True,
            "message": "OTP sent to your email"
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """Verify OTP for password reset."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({
                "success": False,
                "message": "Email and OTP are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        stored_data = otp_storage.get(email)
        
        if not stored_data:
            return Response({
                "success": False,
                "message": "OTP expired or not found. Please request a new one."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if OTP is expired (10 minutes)
        time_diff = (timezone.now() - stored_data['created_at']).seconds
        if time_diff > 600:
            del otp_storage[email]
            return Response({
                "success": False,
                "message": "OTP has expired. Please request a new one."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if stored_data['otp'] != otp:
            return Response({
                "success": False,
                "message": "Invalid OTP"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark OTP as verified
        otp_storage[email]['verified'] = True
        
        return Response({
            "success": True,
            "message": "OTP verified successfully"
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """Reset password after OTP verification."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([email, otp, new_password, confirm_password]):
            return Response({
                "success": False,
                "message": "All fields are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                "success": False,
                "message": "Passwords do not match"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 6:
            return Response({
                "success": False,
                "message": "Password must be at least 6 characters"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        stored_data = otp_storage.get(email)
        
        if not stored_data or stored_data['otp'] != otp:
            return Response({
                "success": False,
                "message": "Invalid or expired OTP"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not stored_data.get('verified'):
            return Response({
                "success": False,
                "message": "Please verify OTP first"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=stored_data['user_id'])
            user.set_password(new_password)
            user.save()
            
            # Clear OTP storage
            del otp_storage[email]
            
            # Delete old tokens
            Token.objects.filter(user=user).delete()
            
            return Response({
                "success": True,
                "message": "Password reset successfully. Please login with your new password."
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)


# ========================
# Category & Department Views
# ========================

class CategoryListView(APIView):
    """List all complaint categories."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        categories = ComplaintCategory.objects.select_related('department').all()
        serializer = CategorySerializer(categories, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class DepartmentListView(APIView):
    """List all departments."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


# ========================
# Complaint Views
# ========================

class ComplaintCreateView(APIView):
    """Create a new complaint."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ComplaintCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            complaint = serializer.save(user=request.user)
            
            # Create initial log
            ComplaintLog.objects.create(
                complaint=complaint,
                action_by=request.user,
                note="Complaint registered via mobile app",
                old_status="",
                new_status="pending"
            )
            
            return Response({
                "success": True,
                "message": "Complaint submitted successfully!",
                "data": ComplaintSerializer(complaint).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "message": "Failed to submit complaint",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MyComplaintsView(APIView):
    """List all complaints by the logged-in user."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        complaints = Complaint.objects.filter(
            user=request.user,
            is_deleted=False
        ).select_related('category', 'department', 'current_officer', 'current_worker')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            complaints = complaints.filter(status=status_filter)
        
        complaints = complaints.order_by('-created_at')
        serializer = ComplaintSerializer(complaints, many=True)
        
        # Get stats
        total = Complaint.objects.filter(user=request.user, is_deleted=False).count()
        pending = Complaint.objects.filter(
            user=request.user, is_deleted=False, status__in=['pending', 'assigned']
        ).count()
        in_progress = Complaint.objects.filter(
            user=request.user, is_deleted=False, status='in_progress'
        ).count()
        resolved = Complaint.objects.filter(
            user=request.user, is_deleted=False, status='resolved'
        ).count()
        
        return Response({
            "success": True,
            "data": {
                "complaints": serializer.data,
                "stats": {
                    "total": total,
                    "pending": pending,
                    "in_progress": in_progress,
                    "resolved": resolved
                }
            }
        }, status=status.HTTP_200_OK)


class ComplaintDetailView(APIView):
    """Get complaint details."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            complaint = Complaint.objects.select_related(
                'category', 'department', 'current_officer__user', 'current_worker__user'
            ).get(pk=pk, user=request.user, is_deleted=False)
        except Complaint.DoesNotExist:
            return Response({
                "success": False,
                "message": "Complaint not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ComplaintSerializer(complaint)
        
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ComplaintLogsView(APIView):
    """Get complaint timeline/logs."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk, user=request.user, is_deleted=False)
        except Complaint.DoesNotExist:
            return Response({
                "success": False,
                "message": "Complaint not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        logs = ComplaintLog.objects.filter(complaint=complaint).order_by('-timestamp')
        serializer = ComplaintLogSerializer(logs, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


# ========================
# Facility Views
# ========================

class FacilityListView(APIView):
    """List all public facilities."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        facilities = Facility.objects.filter(is_active=True)
        
        # Filter by type if provided
        facility_type = request.query_params.get('type')
        if facility_type:
            facilities = facilities.filter(facility_type=facility_type)
        
        serializer = FacilitySerializer(facilities, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class FacilityDetailView(APIView):
    """Get facility details with ratings."""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            facility = Facility.objects.get(pk=pk, is_active=True)
        except Facility.DoesNotExist:
            return Response({
                "success": False,
                "message": "Facility not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get recent ratings
        ratings = FacilityRating.objects.filter(facility=facility).order_by('-created_at')[:10]
        
        serializer = FacilitySerializer(facility)
        rating_serializer = FacilityRatingSerializer(ratings, many=True)
        
        return Response({
            "success": True,
            "data": {
                "facility": serializer.data,
                "recent_ratings": rating_serializer.data
            }
        }, status=status.HTTP_200_OK)


class FacilityRateView(APIView):
    """Rate a facility's cleanliness."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            facility = Facility.objects.get(pk=pk, is_active=True)
        except Facility.DoesNotExist:
            return Response({
                "success": False,
                "message": "Facility not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        rating_value = request.data.get('cleanliness_rating')
        comment = request.data.get('comment', '')
        is_anonymous = request.data.get('is_anonymous', False)
        
        if not rating_value or rating_value not in [1, 2, 3, 4, 5]:
            return Response({
                "success": False,
                "message": "Rating must be between 1 and 5"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        rating = FacilityRating.objects.create(
            facility=facility,
            user=None if is_anonymous else request.user,
            cleanliness_rating=rating_value,
            comment=comment,
            is_anonymous=is_anonymous,
            ip_address=ip
        )
        
        serializer = FacilityRatingSerializer(rating)
        
        return Response({
            "success": True,
            "message": "Thank you for your rating!",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class NearbyFacilitiesView(APIView):
    """Get facilities near a location."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', 5)  # default 5km
        
        if not lat or not lng:
            return Response({
                "success": False,
                "message": "Latitude and longitude are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid coordinates"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simple distance filter (for production, use PostGIS)
        lat_range = radius / 111  # 1 degree ≈ 111 km
        lng_range = radius / (111 * abs(lat) if lat != 0 else 111)
        
        facilities = Facility.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__gte=lat - lat_range,
            latitude__lte=lat + lat_range,
            longitude__gte=lng - lng_range,
            longitude__lte=lng + lng_range
        )
        
        serializer = FacilitySerializer(facilities, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


# ========================
# Admin Tools
# ========================

@login_required
def mark_attendance_view(request):
    """Admin view for marking worker attendance"""
    user = request.user
    
    # Get officer's department
    workers = Worker.objects.none()
    
    if hasattr(user, 'officer'):
        officer = user.officer
        workers = Worker.objects.filter(department=officer.department, is_active=True)
    elif user.is_superuser:
        workers = Worker.objects.filter(is_active=True)
    
    today = timezone.now().date()
    
    if request.method == 'POST':
        for worker in workers:
            status_value = request.POST.get(f'status_{worker.id}')
            if status_value:
                WorkerAttendance.objects.update_or_create(
                    worker=worker,
                    date=today,
                    defaults={
                        'status': status_value,
                        'marked_by': user
                    }
                )
        return render(request, 'admin/mark_attendance.html', {
            'workers': workers,
            'today': today,
            'success': True
        })
    
    # Get today's attendance
    attendance_dict = {}
    for att in WorkerAttendance.objects.filter(worker__in=workers, date=today):
        attendance_dict[att.worker_id] = att.status
    
    return render(request, 'admin/mark_attendance.html', {
        'workers': workers,
        'today': today,
        'attendance': attendance_dict
    })

