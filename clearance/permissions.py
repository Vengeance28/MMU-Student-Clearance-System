from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """Allows access only to authenticated students."""
    message = 'Access restricted to students only.'

    def has_permission(self, request, view):
        return bool(
            request.auth and
            hasattr(request, 'student') and
            request.student is not None
        )


class IsStaff(BasePermission):
    """Allows access only to authenticated staff (officer or admin)."""
    message = 'Access restricted to staff only.'

    def has_permission(self, request, view):
        return bool(
            request.auth and
            hasattr(request, 'staff') and
            request.staff is not None
        )


class IsAdminStaff(BasePermission):
    """Allows access only to admin staff."""
    message = 'Access restricted to admin staff only.'

    def has_permission(self, request, view):
        return bool(
            request.auth and
            hasattr(request, 'staff') and
            request.staff is not None and
            request.staff.role == 'admin'
        )
