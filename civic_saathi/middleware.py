"""
Middleware to auto-assign permissions to staff users.
Any user with is_staff=True gets full model access automatically.
Data filtering is handled at the admin queryset level.
"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class AutoStaffPermissionsMiddleware:
    """
    Automatically grants model permissions to staff users on login.
    This ensures all staff see the full admin UI.
    Data isolation is done via get_queryset() in admin classes.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._permissions_cache = None

    def __call__(self, request):
        # Only process for authenticated staff users accessing admin
        if (request.user.is_authenticated and 
            request.user.is_staff and 
            not request.user.is_superuser and
            request.path.startswith('/admin/')):
            
            # Check if user needs permissions (has very few)
            if request.user.user_permissions.count() < 10:
                self._assign_staff_permissions(request.user)
        
        response = self.get_response(request)
        return response
    
    def _get_all_permissions(self):
        """Cache and return all civic_saathi permissions"""
        if self._permissions_cache is None:
            from civic_saathi.models import (
                Complaint, ComplaintCategory, ComplaintLog, ComplaintEscalation,
                Assignment, Worker, WorkerAttendance, Facility, FacilityInspection,
                Streetlight, Department, Officer, SLAConfig, FacilityRating
            )
            
            # Full access models
            full_access = [
                Complaint, ComplaintCategory, ComplaintLog, ComplaintEscalation,
                Assignment, Worker, WorkerAttendance, Facility, FacilityInspection,
                Streetlight, FacilityRating
            ]
            
            # View only models
            view_only = [Department, Officer, SLAConfig]
            
            permissions = []
            
            for model in full_access:
                ct = ContentType.objects.get_for_model(model)
                for action in ['add', 'change', 'delete', 'view']:
                    try:
                        perm = Permission.objects.get(
                            content_type=ct, 
                            codename=f"{action}_{model._meta.model_name}"
                        )
                        permissions.append(perm)
                    except Permission.DoesNotExist:
                        pass
            
            for model in view_only:
                ct = ContentType.objects.get_for_model(model)
                try:
                    perm = Permission.objects.get(
                        content_type=ct,
                        codename=f"view_{model._meta.model_name}"
                    )
                    permissions.append(perm)
                except Permission.DoesNotExist:
                    pass
            
            # Add user view permission
            from django.contrib.auth.models import User
            ct = ContentType.objects.get_for_model(User)
            try:
                perm = Permission.objects.get(content_type=ct, codename='view_user')
                permissions.append(perm)
            except Permission.DoesNotExist:
                pass
            
            self._permissions_cache = permissions
        
        return self._permissions_cache
    
    def _assign_staff_permissions(self, user):
        """Assign all required permissions to a staff user"""
        permissions = self._get_all_permissions()
        user.user_permissions.add(*permissions)
