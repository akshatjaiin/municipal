from django.urls import path
from .views import (
    # Home Page
    home_view,
    
    # Complaint Views
    ComplaintCreateView,
    MyComplaintsView,
    ComplaintDetailView,
    ComplaintLogsView,
    mark_attendance_view,
    
    # Auth Views
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    ForgotPasswordView,
    VerifyOTPView,
    ResetPasswordView,
    
    # Category Views
    CategoryListView,
    DepartmentListView,
    
    # Facility Views
    FacilityListView,
    FacilityDetailView,
    FacilityRateView,
    NearbyFacilitiesView,
)

urlpatterns = [
    # ========================
    # Home Page
    # ========================
    path("", home_view, name="home"),
    
    # ========================
    # Authentication Routes
    # ========================
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    
    # ========================
    # Complaint Routes
    # ========================
    path("complaints/", MyComplaintsView.as_view(), name="my_complaints"),
    path("complaints/create/", ComplaintCreateView.as_view(), name="create_complaint"),
    path("complaints/<int:pk>/", ComplaintDetailView.as_view(), name="complaint_detail"),
    path("complaints/<int:pk>/logs/", ComplaintLogsView.as_view(), name="complaint_logs"),
    
    # ========================
    # Category & Department Routes
    # ========================
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("departments/", DepartmentListView.as_view(), name="departments"),
    
    # ========================
    # Facility Routes
    # ========================
    path("facilities/", FacilityListView.as_view(), name="facilities"),
    path("facilities/nearby/", NearbyFacilitiesView.as_view(), name="nearby_facilities"),
    path("facilities/<int:pk>/", FacilityDetailView.as_view(), name="facility_detail"),
    path("facilities/<int:pk>/rate/", FacilityRateView.as_view(), name="rate_facility"),
    
    # ========================
    # Admin Tools
    # ========================
    path("admin-tools/mark-attendance/", mark_attendance_view, name="mark_attendance"),
]