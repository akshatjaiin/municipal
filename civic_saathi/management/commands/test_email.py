"""
Test email configuration.
Usage: python manage.py test_email recipient@example.com
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            nargs='?',
            default=None,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient = options['recipient'] or settings.EMAIL_HOST_USER
        
        self.stdout.write(f"\n📧 Email Configuration:")
        self.stdout.write(f"   Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"   Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"   Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"   User: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"   From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"   TLS: {settings.EMAIL_USE_TLS}")
        
        if not settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  EMAIL_HOST_PASSWORD is empty!"
                "\n   For Gmail, you need to use an App Password."
                "\n   Set it via environment variable: EMAIL_HOST_PASSWORD=your_app_password"
                "\n"
                "\n   To generate Gmail App Password:"
                "\n   1. Go to https://myaccount.google.com/security"
                "\n   2. Enable 2-Step Verification"
                "\n   3. Go to 'App passwords'"
                "\n   4. Create new app password for 'Mail'"
                "\n   5. Copy the 16-character password"
            ))
            return
        
        self.stdout.write(f"\n📤 Sending test email to: {recipient}")
        
        try:
            send_mail(
                subject='🧪 Test Email from Municipal Portal',
                message='This is a test email from the Municipal Governance Portal.\n\nIf you received this, email is working correctly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'\n✅ Test email sent successfully to {recipient}!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Failed to send email: {e}'))
            self.stdout.write(self.style.WARNING(
                "\n   Common issues:"
                "\n   - Invalid App Password (use 16-char app password, not regular password)"
                "\n   - 2-Step Verification not enabled on Gmail"
                "\n   - Less secure app access blocked"
            ))
