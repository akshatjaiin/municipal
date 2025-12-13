"""
Email Service for Municipal Governance System
Handles all email notifications for complaints, assignments, and updates.
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_department_head_email(department):
    """
    Get the email of the department head (senior officer).
    Returns None if not found.
    """
    from .models import Officer
    head = Officer.objects.filter(department=department, role__icontains='head').first()
    if head and head.user.email:
        return head.user.email
    # Fallback: return any officer from dept
    officer = Officer.objects.filter(department=department).first()
    if officer and officer.user.email:
        return officer.user.email
    return None


def send_complaint_registered_email(complaint):
    """
    Send email notification when a new complaint is registered.
    Notifies: 1) Citizen who filed, 2) Department head
    """
    subject = f"🆕 Complaint Registered - #{complaint.id}: {complaint.title}"
    
    # Context for templates
    context = {
        'complaint': complaint,
        'complaint_id': complaint.id,
        'title': complaint.title,
        'description': complaint.description,
        'location': complaint.location,
        'category': complaint.category.name if complaint.category else 'General',
        'department': complaint.department.name if complaint.department else 'Pending Assignment',
        'priority': {1: 'Normal', 2: 'High', 3: 'Critical'}.get(complaint.priority, 'Normal'),
        'status': complaint.status.replace('_', ' ').title(),
        'created_at': complaint.created_at.strftime('%B %d, %Y at %I:%M %p'),
        'citizen_name': complaint.user.get_full_name() or complaint.user.username,
    }
    
    # HTML Email Content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
            .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
            .info-box {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #667eea; }}
            .label {{ font-weight: bold; color: #555; display: inline-block; width: 120px; }}
            .value {{ color: #333; }}
            .priority-high {{ color: #f39c12; font-weight: bold; }}
            .priority-critical {{ color: #e74c3c; font-weight: bold; }}
            .footer {{ text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 12px; }}
            .tracking-id {{ font-size: 24px; font-weight: bold; background: #fff; padding: 10px 20px; border-radius: 5px; display: inline-block; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🏛️ Municipal Governance Portal</h2>
                <p>Complaint Registration Confirmation</p>
            </div>
            <div class="content">
                <p>Dear <strong>{context['citizen_name']}</strong>,</p>
                <p>Your complaint has been successfully registered in our system. Below are the details:</p>
                
                <div style="text-align: center;">
                    <span class="tracking-id">Tracking ID: #{context['complaint_id']}</span>
                </div>
                
                <div class="info-box">
                    <p><span class="label">Title:</span> <span class="value">{context['title']}</span></p>
                    <p><span class="label">Category:</span> <span class="value">{context['category']}</span></p>
                    <p><span class="label">Location:</span> <span class="value">{context['location']}</span></p>
                    <p><span class="label">Department:</span> <span class="value">{context['department']}</span></p>
                    <p><span class="label">Priority:</span> <span class="value {'priority-high' if complaint.priority == 2 else 'priority-critical' if complaint.priority == 3 else ''}">{context['priority']}</span></p>
                    <p><span class="label">Status:</span> <span class="value">{context['status']}</span></p>
                    <p><span class="label">Registered:</span> <span class="value">{context['created_at']}</span></p>
                </div>
                
                <p><strong>Description:</strong></p>
                <p style="background: white; padding: 10px; border-radius: 5px;">{context['description']}</p>
                
                <p>You will receive updates via email as your complaint progresses through our system.</p>
                
                <div class="footer">
                    <p>This is an automated message from the Municipal Governance Portal.</p>
                    <p>Please save your Tracking ID for future reference.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_content)
    recipients = []
    
    # 1. Send to citizen
    if complaint.user.email:
        recipients.append(complaint.user.email)
    
    # 2. Send to department head
    if complaint.department:
        dept_head_email = get_department_head_email(complaint.department)
        if dept_head_email and dept_head_email not in recipients:
            recipients.append(dept_head_email)
    
    if not recipients:
        logger.warning(f"No recipients found for complaint #{complaint.id}")
        return False
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        logger.info(f"Complaint registration email sent for #{complaint.id} to {recipients}")
        return True
    except Exception as e:
        logger.error(f"Failed to send complaint registration email: {e}")
        return False


def send_worker_assignment_email(complaint, worker, assigned_by=None):
    """
    Send email notification when a worker is assigned to a complaint.
    Notifies: 1) Citizen, 2) Worker, 3) Department head
    """
    subject = f"👷 Worker Assigned - Complaint #{complaint.id}: {complaint.title}"
    
    context = {
        'complaint_id': complaint.id,
        'title': complaint.title,
        'location': complaint.location,
        'description': complaint.description[:200] + '...' if len(complaint.description) > 200 else complaint.description,
        'worker_name': worker.user.get_full_name() or worker.user.username,
        'worker_role': worker.role,
        'department': complaint.department.name if complaint.department else 'N/A',
        'assigned_by': assigned_by.get_full_name() if assigned_by else 'System',
        'assignment_date': complaint.updated_at.strftime('%B %d, %Y at %I:%M %p'),
        'citizen_name': complaint.user.get_full_name() or complaint.user.username,
    }
    
    # Email for Citizen
    citizen_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
            .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
            .worker-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .worker-avatar {{ width: 80px; height: 80px; background: #3498db; border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; font-size: 36px; color: white; }}
            .worker-name {{ font-size: 20px; font-weight: bold; color: #2c3e50; }}
            .worker-role {{ color: #7f8c8d; }}
            .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
            .footer {{ text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>👷 Worker Assigned to Your Complaint</h2>
                <p>Great news! Someone is on the way to resolve your issue.</p>
            </div>
            <div class="content">
                <p>Dear <strong>{context['citizen_name']}</strong>,</p>
                <p>A municipal worker has been assigned to address your complaint <strong>#{context['complaint_id']}</strong>.</p>
                
                <div class="worker-card">
                    <div class="worker-avatar">👷</div>
                    <div class="worker-name">{context['worker_name']}</div>
                    <div class="worker-role">{context['worker_role']}</div>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 8px;">
                    <div class="info-row">
                        <span><strong>Complaint:</strong></span>
                        <span>{context['title']}</span>
                    </div>
                    <div class="info-row">
                        <span><strong>Location:</strong></span>
                        <span>{context['location']}</span>
                    </div>
                    <div class="info-row">
                        <span><strong>Assigned On:</strong></span>
                        <span>{context['assignment_date']}</span>
                    </div>
                    <div class="info-row">
                        <span><strong>Assigned By:</strong></span>
                        <span>{context['assigned_by']}</span>
                    </div>
                </div>
                
                <p style="margin-top: 20px;">The worker will visit the location and resolve the issue. You will be notified once the work is completed.</p>
                
                <div class="footer">
                    <p>Thank you for using the Municipal Governance Portal.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Email for Worker
    worker_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
            .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
            .task-box {{ background: white; padding: 20px; border-radius: 10px; border-left: 5px solid #e74c3c; margin: 20px 0; }}
            .location-box {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📋 New Task Assigned</h2>
                <p>You have been assigned a new complaint.</p>
            </div>
            <div class="content">
                <p>Dear <strong>{context['worker_name']}</strong>,</p>
                <p>You have been assigned to resolve the following complaint:</p>
                
                <div class="task-box">
                    <h3>#{context['complaint_id']}: {context['title']}</h3>
                    <p>{context['description']}</p>
                </div>
                
                <div class="location-box">
                    <strong>📍 Location:</strong> {context['location']}
                </div>
                
                <p><strong>Assigned By:</strong> {context['assigned_by']}</p>
                <p><strong>Department:</strong> {context['department']}</p>
                
                <p style="margin-top: 20px; color: #e74c3c;">
                    <strong>⚠️ Please visit the location and update the status once resolved.</strong>
                </p>
                
                <div class="footer">
                    <p>Municipal Governance Portal - Task Assignment</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    results = []
    
    # Send to citizen
    if complaint.user.email:
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(citizen_html),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[complaint.user.email]
            )
            email.attach_alternative(citizen_html, "text/html")
            email.send(fail_silently=False)
            results.append(('citizen', True))
            logger.info(f"Worker assignment email sent to citizen {complaint.user.email}")
        except Exception as e:
            results.append(('citizen', False))
            logger.error(f"Failed to send to citizen: {e}")
    
    # Send to worker
    if worker.user.email:
        try:
            email = EmailMultiAlternatives(
                subject=f"📋 New Task - Complaint #{complaint.id}: {complaint.title}",
                body=strip_tags(worker_html),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[worker.user.email]
            )
            email.attach_alternative(worker_html, "text/html")
            email.send(fail_silently=False)
            results.append(('worker', True))
            logger.info(f"Task assignment email sent to worker {worker.user.email}")
        except Exception as e:
            results.append(('worker', False))
            logger.error(f"Failed to send to worker: {e}")
    
    # Send to department head
    if complaint.department:
        dept_head_email = get_department_head_email(complaint.department)
        if dept_head_email:
            try:
                send_mail(
                    subject=f"📊 Assignment Update - #{complaint.id} assigned to {context['worker_name']}",
                    message=f"Complaint #{complaint.id} ({complaint.title}) has been assigned to {context['worker_name']} ({worker.role}).",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[dept_head_email],
                    fail_silently=False
                )
                results.append(('dept_head', True))
            except Exception as e:
                results.append(('dept_head', False))
                logger.error(f"Failed to send to dept head: {e}")
    
    return results


def send_status_update_email(complaint, old_status, new_status, updated_by=None):
    """
    Send email notification when complaint status changes.
    """
    subject = f"📢 Status Update - Complaint #{complaint.id}: {new_status.replace('_', ' ').title()}"
    
    status_colors = {
        'pending': '#f39c12',
        'in_progress': '#3498db',
        'resolved': '#27ae60',
        'closed': '#95a5a6',
        'escalated': '#e74c3c'
    }
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {status_colors.get(new_status, '#667eea')}; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
            .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
            .status-change {{ display: flex; justify-content: center; align-items: center; gap: 20px; margin: 20px 0; }}
            .status-box {{ padding: 10px 20px; border-radius: 5px; font-weight: bold; }}
            .old-status {{ background: #eee; color: #666; }}
            .new-status {{ background: {status_colors.get(new_status, '#667eea')}; color: white; }}
            .arrow {{ font-size: 24px; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📢 Complaint Status Updated</h2>
            </div>
            <div class="content">
                <p>Your complaint <strong>#{complaint.id}: {complaint.title}</strong> has been updated.</p>
                
                <div class="status-change">
                    <span class="status-box old-status">{old_status.replace('_', ' ').title()}</span>
                    <span class="arrow">→</span>
                    <span class="status-box new-status">{new_status.replace('_', ' ').title()}</span>
                </div>
                
                <p><strong>Location:</strong> {complaint.location}</p>
                {'<p><strong>Worker:</strong> ' + (complaint.current_worker.user.get_full_name() if complaint.current_worker else 'Not assigned') + '</p>' if complaint.current_worker else ''}
                <p><strong>Updated By:</strong> {updated_by.get_full_name() if updated_by else 'System'}</p>
                
                {'<p style="color: #27ae60; font-weight: bold;">✅ Your issue has been resolved! Thank you for using our services.</p>' if new_status == 'resolved' else ''}
            </div>
        </div>
    </body>
    </html>
    """
    
    if complaint.user.email:
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[complaint.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Status update email sent for complaint #{complaint.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send status update email: {e}")
            return False
    return False


def send_escalation_email(complaint, escalation):
    """
    Send email notification when a complaint is escalated.
    """
    subject = f"⚠️ ESCALATION - Complaint #{complaint.id}: {complaint.title}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #e74c3c; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
            .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
            .warning-box {{ background: #fff3cd; border: 2px solid #e74c3c; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>⚠️ COMPLAINT ESCALATED</h2>
            </div>
            <div class="content">
                <div class="warning-box">
                    <p><strong>Complaint ID:</strong> #{complaint.id}</p>
                    <p><strong>Title:</strong> {complaint.title}</p>
                    <p><strong>Location:</strong> {complaint.location}</p>
                    <p><strong>Reason:</strong> {escalation.reason}</p>
                    <p><strong>Escalated From:</strong> {escalation.escalated_from.user.get_full_name() if escalation.escalated_from else 'N/A'}</p>
                    <p><strong>Escalated To:</strong> {escalation.escalated_to.user.get_full_name() if escalation.escalated_to else 'Department Head'}</p>
                </div>
                <p style="color: #e74c3c;"><strong>This complaint requires immediate attention.</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    recipients = []
    
    # Send to escalated_to officer
    if escalation.escalated_to and escalation.escalated_to.user.email:
        recipients.append(escalation.escalated_to.user.email)
    
    # Send to dept head
    if complaint.department:
        dept_head_email = get_department_head_email(complaint.department)
        if dept_head_email and dept_head_email not in recipients:
            recipients.append(dept_head_email)
    
    if recipients:
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Escalation email sent for complaint #{complaint.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send escalation email: {e}")
            return False
    return False
