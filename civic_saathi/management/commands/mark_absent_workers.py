"""
Management command to mark workers absent if no attendance recorded by cutoff time.
Run via: python manage.py mark_absent_workers
Schedule to run daily at end of shift (e.g., 6 PM).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from civic_saathi.models import Worker, WorkerAttendance


class Command(BaseCommand):
    help = "Mark active workers as absent if no attendance recorded today"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be marked without making changes',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        dry_run = options['dry_run']

        # Get all active workers
        active_workers = Worker.objects.filter(is_active=True)
        marked_count = 0

        for worker in active_workers:
            # Check if attendance exists for today
            attendance_exists = WorkerAttendance.objects.filter(
                worker=worker,
                date=today
            ).exists()

            if not attendance_exists:
                if dry_run:
                    self.stdout.write(f"Would mark absent: {worker.user.username}")
                else:
                    WorkerAttendance.objects.create(
                        worker=worker,
                        date=today,
                        status="absent",
                        notes="Auto-marked absent (no check-in recorded)"
                    )
                    self.stdout.write(
                        self.style.WARNING(f"Marked absent: {worker.user.username}")
                    )
                marked_count += 1

        action = "Would mark" if dry_run else "Marked"
        self.stdout.write(
            self.style.SUCCESS(f"\n{action} {marked_count} workers as absent for {today}")
        )
