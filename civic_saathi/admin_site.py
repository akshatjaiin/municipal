from django.contrib.admin import AdminSite
from django.utils import timezone
from datetime import timedelta


class MunicipalAdminSite(AdminSite):
    site_header = "🏛️ Municipal Governance"
    site_title = "Municipal Admin"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        from civic_saathi.models import (
            Department, Complaint, Worker, Officer,
            WorkerAttendance, ComplaintEscalation
        )

        extra_context = extra_context or {}

        # Get user's department if they're an officer
        user_department = None
        if hasattr(request.user, 'officer'):
            user_department = request.user.officer.department

        # Stats - filtered by department if user is officer
        complaints_qs = Complaint.objects.all()
        if user_department:
            complaints_qs = complaints_qs.filter(department=user_department)

        today = timezone.now().date()
        
        extra_context['total_complaints'] = complaints_qs.count()
        extra_context['pending_complaints'] = complaints_qs.filter(status='pending').count()
        extra_context['resolved_complaints'] = complaints_qs.filter(
            status='resolved',
            updated_at__date=today
        ).count()

        # Calculate overdue (SLA breached)
        overdue_count = 0
        for complaint in complaints_qs.filter(status__in=['pending', 'in_progress']):
            if complaint.category and hasattr(complaint.category, 'sla'):
                elapsed = (timezone.now() - complaint.created_at).total_seconds() / 3600
                if elapsed > complaint.category.sla.resolution_hours:
                    overdue_count += 1
        extra_context['overdue_complaints'] = overdue_count

        extra_context['user_department'] = user_department

        # Department icons
        dept_icons = {
            'Sanitation': '🧹',
            'Roads': '🛤️',
            'Electricity': '💡',
            'Water Supply': '💧',
            'Sewage': '🚰',
            'Public Health': '🏥',
        }

        # Build complaint flow trees for each department
        dept_flows = []
        dept_qs = Department.objects.all()
        if user_department:
            dept_qs = dept_qs.filter(id=user_department.id)

        for dept in dept_qs:
            dept_complaints = Complaint.objects.filter(department=dept)
            
            # Pending - no worker assigned yet (with officer)
            pending = dept_complaints.filter(
                status='pending',
                current_worker__isnull=True
            ).order_by('-priority', '-created_at')[:5]
            
            # At Officer - has officer but reviewing/assigning
            at_officer = dept_complaints.filter(
                status='pending',
                current_officer__isnull=False,
                current_worker__isnull=True
            ).order_by('-priority', '-created_at')[:5]
            
            # At Worker - in progress with worker
            at_worker = dept_complaints.filter(
                status='in_progress',
                current_worker__isnull=False
            ).order_by('-priority', '-created_at')[:5]
            
            # Resolved today
            resolved = dept_complaints.filter(
                status='resolved',
                updated_at__date=today
            ).order_by('-updated_at')[:5]
            
            # Escalated
            escalated = dept_complaints.filter(
                status='escalated'
            ).order_by('-priority', '-created_at')[:5]
            
            # Calculate SLA breached count
            sla_breached = 0
            for c in dept_complaints.filter(status__in=['pending', 'in_progress']):
                if c.category and hasattr(c.category, 'sla'):
                    elapsed = (timezone.now() - c.created_at).total_seconds() / 3600
                    if elapsed > c.category.sla.resolution_hours:
                        sla_breached += 1

            dept_flows.append({
                'name': dept.name,
                'icon': dept_icons.get(dept.name, '🏢'),
                # Pending complaints
                'pending_complaints': [
                    {'id': c.id, 'title': c.title, 'priority': c.priority}
                    for c in pending
                ],
                'pending_count': pending.count(),
                # At officer level
                'at_officer_complaints': [
                    {'id': c.id, 'title': c.title, 'priority': c.priority,
                     'officer_name': c.current_officer.user.get_full_name() or c.current_officer.user.username if c.current_officer else '-'}
                    for c in at_officer
                ],
                'at_officer_count': at_officer.count(),
                # At worker level
                'at_worker_complaints': [
                    {'id': c.id, 'title': c.title, 'priority': c.priority,
                     'worker_name': c.current_worker.user.get_full_name() or c.current_worker.user.username if c.current_worker else '-'}
                    for c in at_worker
                ],
                'at_worker_count': at_worker.count(),
                # Resolved
                'resolved_complaints': [
                    {'id': c.id, 'title': c.title, 'priority': c.priority}
                    for c in resolved
                ],
                'resolved_count': resolved.count(),
                # Escalated
                'escalated_complaints': [
                    {'id': c.id, 'title': c.title, 'priority': c.priority}
                    for c in escalated
                ],
                'escalated_count': escalated.count(),
                # Summary
                'total_open': dept_complaints.filter(status__in=['pending', 'in_progress', 'escalated']).count(),
                'sla_breached': sla_breached,
            })

        extra_context['dept_flows'] = dept_flows

        return super().index(request, extra_context=extra_context)


# Create instance
municipal_admin = MunicipalAdminSite(name='municipal_admin')
