"""
Token store backed by the database — works reliably on Vercel serverless.
Each token is stored as a row in the AuthToken table.
"""
import secrets
from django.utils import timezone
from datetime import timedelta


def generate_token():
    return secrets.token_hex(32)


def create_student_token(student):
    from .models import AuthToken
    # Remove any existing tokens for this student
    AuthToken.objects.filter(student=student).delete()
    token = generate_token()
    AuthToken.objects.create(
        token=token,
        student=student,
        staff=None,
        expires_at=timezone.now() + timedelta(hours=24)
    )
    return token


def create_staff_token(staff):
    from .models import AuthToken
    AuthToken.objects.filter(staff=staff).delete()
    token = generate_token()
    AuthToken.objects.create(
        token=token,
        student=None,
        staff=staff,
        expires_at=timezone.now() + timedelta(hours=24)
    )
    return token


def get_student_by_token(token):
    from .models import AuthToken
    try:
        t = AuthToken.objects.select_related('student__programme__faculty').get(
            token=token,
            student__isnull=False,
            expires_at__gt=timezone.now()
        )
        return t.student
    except AuthToken.DoesNotExist:
        return None


def get_staff_by_token(token):
    from .models import AuthToken
    try:
        t = AuthToken.objects.select_related('staff__department').get(
            token=token,
            staff__isnull=False,
            expires_at__gt=timezone.now()
        )
        return t.staff if t.staff.is_active else None
    except AuthToken.DoesNotExist:
        return None


def delete_student_token(token):
    from .models import AuthToken
    AuthToken.objects.filter(token=token, student__isnull=False).delete()


def delete_staff_token(token):
    from .models import AuthToken
    AuthToken.objects.filter(token=token, staff__isnull=False).delete()
