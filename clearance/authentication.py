from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone


class StudentTokenAuthentication(BaseAuthentication):
    """
    Authenticates students using a simple token stored in-memory / Django cache.
    Since we're not using Django's User model, we keep tokens in a simple dict-based
    approach backed by Django's cache framework for simplicity.
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        from .token_store import get_student_by_token
        student = get_student_by_token(token)
        if student:
            request.student = student
            request.staff = None
            return (student, token)

        return None


class StaffTokenAuthentication(BaseAuthentication):
    """Authenticates staff using token store."""

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        from .token_store import get_staff_by_token
        staff = get_staff_by_token(token)
        if staff:
            request.staff = staff
            request.student = None
            return (staff, token)

        return None


class CombinedTokenAuthentication(BaseAuthentication):
    """Tries student token first, then staff token."""

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        from .token_store import get_student_by_token, get_staff_by_token

        student = get_student_by_token(token)
        if student:
            request.student = student
            request.staff = None
            return (student, token)

        staff = get_staff_by_token(token)
        if staff:
            request.staff = staff
            request.student = None
            return (staff, token)

        return None
