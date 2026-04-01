from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='clearance.DeptClearanceStatus')
def on_dept_clearance_status_save(sender, instance, created, **kwargs):
    """
    Fires after every DeptClearanceStatus save.
    1. Recalculates overall_status on the parent ClearanceRequest.
    2. Sends appropriate email notification to the student.
    """
    from .emails import (
        send_dept_cleared_email,
        send_dept_rejected_email,
        send_clearance_complete_email,
    )

    if created:
        # New row created (bulk-create at submission) — no email needed here
        return

    clearance_request = instance.request
    student = clearance_request.student
    old_overall_status = clearance_request.overall_status

    # Recalculate overall status
    clearance_request.recalculate_status()
    clearance_request.refresh_from_db()

    # Send appropriate notification
    if instance.status == 'CLEARED':
        if clearance_request.overall_status == 'COMPLETED':
            send_clearance_complete_email(student, clearance_request)
        else:
            send_dept_cleared_email(student, clearance_request, instance)
    elif instance.status == 'REJECTED':
        send_dept_rejected_email(student, clearance_request, instance)
