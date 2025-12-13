"""
Django Signals for Civic Saathi
Handles automatic email notifications on model events.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Complaint, ComplaintEscalation
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Complaint)
def complaint_post_save(sender, instance, created, **kwargs):
    """
    Send email notification when a complaint is created via API.
    Note: Admin creates are handled in admin.py save_model()
    """
    # Skip if this is an admin save (handled separately)
    # We use a flag to check if it's from admin
    if getattr(instance, '_from_admin', False):
        return
    
    if created:
        try:
            from .email_service import send_complaint_registered_email
            send_complaint_registered_email(instance)
            logger.info(f"Signal: Email sent for new complaint #{instance.id}")
        except Exception as e:
            logger.error(f"Signal: Failed to send email for complaint #{instance.id}: {e}")


@receiver(post_save, sender=ComplaintEscalation)
def escalation_post_save(sender, instance, created, **kwargs):
    """
    Send email notification when a complaint is escalated via API.
    """
    if getattr(instance, '_from_admin', False):
        return
        
    if created:
        try:
            from .email_service import send_escalation_email
            send_escalation_email(instance.complaint, instance)
            logger.info(f"Signal: Escalation email sent for complaint #{instance.complaint_id}")
        except Exception as e:
            logger.error(f"Signal: Failed to send escalation email: {e}")
