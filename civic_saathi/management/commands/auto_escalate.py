"""
Management command to auto-escalate overdue complaints.
Run via: python manage.py auto_escalate
Schedule with cron or Windows Task Scheduler for periodic execution.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from civic_saathi.models import Complaint, ComplaintEscalation, ComplaintLog, Officer


class Command(BaseCommand):
    help = "Auto-escalate complaints that exceed SLA thresholds"

    def handle(self, *args, **options):
        now = timezone.now()
        escalated_count = 0
        notified_count = 0

        # Get all pending/in_progress complaints
        complaints = Complaint.objects.filter(
            status__in=["pending", "in_progress"],
            is_deleted=False,
            is_spam=False
        ).select_related("category", "current_officer", "department")

        for complaint in complaints:
            # Skip if no SLA configured
            if not complaint.category or not hasattr(complaint.category, 'sla'):
                continue

            sla = complaint.category.sla
            elapsed_hours = (now - complaint.created_at).total_seconds() / 3600

            # Check if complaint exceeds escalation threshold
            if elapsed_hours > sla.escalation_hours:
                # Check if already escalated recently
                recent_escalation = ComplaintEscalation.objects.filter(
                    complaint=complaint,
                    escalated_at__gte=now - timezone.timedelta(hours=24)
                ).exists()

                if not recent_escalation:
                    # Find senior officer in same department
                    senior_officer = Officer.objects.filter(
                        department=complaint.department,
                        role__icontains="senior"
                    ).first()

                    if not senior_officer:
                        senior_officer = Officer.objects.filter(
                            department=complaint.department
                        ).exclude(id=complaint.current_officer_id if complaint.current_officer else 0).first()

                    # Create escalation record
                    ComplaintEscalation.objects.create(
                        complaint=complaint,
                        escalated_from=complaint.current_officer,
                        escalated_to=senior_officer,
                        reason=f"Auto-escalated: Exceeded {sla.escalation_hours}h SLA threshold"
                    )

                    # Update complaint
                    old_status = complaint.status
                    complaint.status = "escalated"
                    complaint.priority = 3  # Critical
                    if senior_officer:
                        complaint.current_officer = senior_officer
                    complaint.save()

                    # Log the change
                    ComplaintLog.objects.create(
                        complaint=complaint,
                        note=f"Auto-escalated after {int(elapsed_hours)}h (SLA: {sla.escalation_hours}h)",
                        old_status=old_status,
                        new_status="escalated"
                    )

                    escalated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"Escalated: Complaint #{complaint.id} - {complaint.title}")
                    )

            # Check if approaching SLA (for notifications)
            elif elapsed_hours > sla.resolution_hours:
                notified_count += 1
                self.stdout.write(
                    self.style.NOTICE(f"Warning: Complaint #{complaint.id} approaching escalation threshold")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {escalated_count} escalated, {notified_count} warnings"
            )
        )
