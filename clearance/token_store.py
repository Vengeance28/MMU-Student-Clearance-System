"""
Simple token store backed by Django's cache.
Tokens are 40-char hex strings, valid for 24 hours.
"""
import secrets
from django.core.cache import cache

STUDENT_TOKEN_PREFIX = 'student_token:'
STAFF_TOKEN_PREFIX = 'staff_token:'
TOKEN_TTL = 86400  # 24 hours


def generate_token():
    return secrets.token_hex(20)


def create_student_token(student):
    token = generate_token()
    cache.set(f"{STUDENT_TOKEN_PREFIX}{token}", student.pk, TOKEN_TTL)
    return token


def create_staff_token(staff):
    token = generate_token()
    cache.set(f"{STAFF_TOKEN_PREFIX}{token}", staff.pk, TOKEN_TTL)
    return token


def get_student_by_token(token):
    from .models import Student
    student_id = cache.get(f"{STUDENT_TOKEN_PREFIX}{token}")
    if student_id is None:
        return None
    try:
        return Student.objects.select_related('programme__faculty').get(pk=student_id)
    except Student.DoesNotExist:
        return None


def get_staff_by_token(token):
    from .models import Staff
    staff_id = cache.get(f"{STAFF_TOKEN_PREFIX}{token}")
    if staff_id is None:
        return None
    try:
        return Staff.objects.select_related('department').get(pk=staff_id, is_active=True)
    except Staff.DoesNotExist:
        return None


def delete_student_token(token):
    cache.delete(f"{STUDENT_TOKEN_PREFIX}{token}")


def delete_staff_token(token):
    cache.delete(f"{STAFF_TOKEN_PREFIX}{token}")
