from django.core.mail import send_mail
from django.conf import settings


def send_request_submitted_email(student, clearance_request):
    subject = "Clearance Request Submitted – MMU"
    message = f"""Dear {student.full_name},

Your clearance request has been successfully submitted to Multimedia University of Kenya.

Details:
- Registration Number: {student.reg_number}
- Academic Year: {clearance_request.academic_year}
- Request Date: {clearance_request.initiated_date}

All 6 departments have been notified and will process your request simultaneously:
• Library
• Finance
• Hostels
• Faculty/School
• ICT Services
• Registry

You can track your clearance status in real-time at your student dashboard.

Best regards,
MMU Clearance System
Multimedia University of Kenya
"""
    return _send_and_log(
        student=student,
        clearance_request=clearance_request,
        subject=subject,
        message=message,
        notif_type='REQUEST_SUBMITTED',
    )


def send_dept_cleared_email(student, clearance_request, dept_status):
    dept_name = dept_status.department.name
    staff_name = dept_status.cleared_by.full_name if dept_status.cleared_by else "Staff"
    all_statuses = clearance_request.dept_statuses.all()
    remaining = sum(1 for s in all_statuses if s.status == 'PENDING')

    subject = f"{dept_name} Clearance Approved – MMU"
    message = f"""Dear {student.full_name},

Great news! Your clearance with {dept_name} has been approved.

Details:
- Department: {dept_name}
- Approved by: {staff_name}
- Remarks: {dept_status.remarks or 'No remarks'}
- Departments remaining: {remaining}

{'You are one step closer to completing your clearance!' if remaining > 0 else 'All departments have cleared you!'}

Check your dashboard for the latest status.

Best regards,
MMU Clearance System
"""
    return _send_and_log(
        student=student,
        clearance_request=clearance_request,
        subject=subject,
        message=message,
        notif_type='DEPT_CLEARED',
    )


def send_dept_rejected_email(student, clearance_request, dept_status):
    dept_name = dept_status.department.name
    subject = f"Action Required: {dept_name} Clearance – MMU"
    message = f"""Dear {student.full_name},

Your clearance request with {dept_name} requires attention.

Details:
- Department: {dept_name}
- Status: REJECTED
- Reason: {dept_status.remarks or 'Please contact the department for details'}

Action Required:
Please resolve the issues mentioned above and contact the {dept_name} department directly at {dept_status.department.contact_email or 'the department office'}.

Once you have resolved the issue, the department staff will update your clearance status.

Best regards,
MMU Clearance System
"""
    return _send_and_log(
        student=student,
        clearance_request=clearance_request,
        subject=subject,
        message=message,
        notif_type='DEPT_REJECTED',
    )


def send_clearance_complete_email(student, clearance_request):
    subject = "🎓 Clearance Complete – MMU"
    message = f"""Dear {student.full_name},

Congratulations! You have successfully completed all clearance requirements at Multimedia University of Kenya.

Clearance Summary:
- Registration Number: {student.reg_number}
- Academic Year: {clearance_request.academic_year}
- Completion Date: {clearance_request.completed_date}

All 6 departments have cleared you:
"""
    for ds in clearance_request.dept_statuses.all():
        staff_name = ds.cleared_by.full_name if ds.cleared_by else "N/A"
        message += f"  ✓ {ds.department.name} — Cleared by {staff_name}\n"

    message += f"""
Your official clearance certificate is now available for download from your student dashboard.

We wish you all the best in your future endeavors!

Best regards,
MMU Clearance System
Multimedia University of Kenya
"""
    return _send_and_log(
        student=student,
        clearance_request=clearance_request,
        subject=subject,
        message=message,
        notif_type='CLEARANCE_COMPLETE',
    )


def _send_and_log(student, clearance_request, subject, message, notif_type):
    """Send email and log to Notification table. Returns the Notification object."""
    from .models import Notification
    status = 'SENT'
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            fail_silently=False,
        )
    except Exception as e:
        status = 'FAILED'

    notification = Notification.objects.create(
        student=student,
        request=clearance_request,
        type=notif_type,
        message=message,
        status=status,
    )
    return notification
