from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import (
    Student, Staff, ClearanceDept, ClearanceRequest,
    DeptClearanceStatus, Notification
)
from .serializers import (
    StudentProfileSerializer, StaffSerializer, StaffCreateSerializer,
    ClearanceStatusSerializer, DeptClearanceStatusSerializer,
    NotificationSerializer, StaffQueueItemSerializer,
    AdminRequestSerializer
)
from .permissions import IsStudent, IsStaff, IsAdminStaff
from .authentication import CombinedTokenAuthentication
from .token_store import create_student_token, create_staff_token, delete_student_token, delete_staff_token
from .emails import send_request_submitted_email


# ── Override DRF auth for all views ──────────────────────────────────────────
class BaseView(APIView):
    authentication_classes = [CombinedTokenAuthentication]
    permission_classes = []


# ─── AUTH VIEWS ──────────────────────────────────────────────────────────────

class StudentLoginView(BaseView):
    """POST /api/auth/student/login/"""

    def post(self, request):
        reg_number = request.data.get('reg_number', '').strip()
        password = request.data.get('password', '')

        if not reg_number or not password:
            return Response({'error': 'Registration number and password are required.'}, status=400)

        try:
            student = Student.objects.select_related('programme__faculty').get(reg_number=reg_number)
        except Student.DoesNotExist:
            return Response({'error': 'Invalid registration number or password.'}, status=401)

        if not student.check_password(password):
            return Response({'error': 'Invalid registration number or password.'}, status=401)

        token = create_student_token(student)
        return Response({
            'token': token,
            'reg_number': student.reg_number,
            'name': student.full_name,
            'student_id': student.pk,
        })


class StaffLoginView(BaseView):
    """POST /api/auth/staff/login/"""

    def post(self, request):
        staff_number = request.data.get('staff_number', '').strip()
        password = request.data.get('password', '')

        if not staff_number or not password:
            return Response({'error': 'Staff number and password are required.'}, status=400)

        try:
            staff = Staff.objects.select_related('department').get(staff_number=staff_number, is_active=True)
        except Staff.DoesNotExist:
            return Response({'error': 'Invalid staff number or password.'}, status=401)

        if not staff.check_password(password):
            return Response({'error': 'Invalid staff number or password.'}, status=401)

        token = create_staff_token(staff)
        return Response({
            'token': token,
            'staff_number': staff.staff_number,
            'name': staff.full_name,
            'department': staff.department.name,
            'department_code': staff.department.code,
            'role': staff.role,
            'staff_id': staff.pk,
        })


class LogoutView(BaseView):
    """POST /api/auth/logout/"""

    def post(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token = auth_header.split(' ', 1)[1].strip()
            delete_student_token(token)
            delete_staff_token(token)
        return Response({'message': 'Logged out successfully.'})


# ─── STUDENT VIEWS ────────────────────────────────────────────────────────────

class StudentProfileView(BaseView):
    """GET /api/student/profile/"""
    permission_classes = []

    def get(self, request):
        student = getattr(request, 'student', None)
        if not student:
            return Response({'error': 'Authentication required.'}, status=401)
        return Response(StudentProfileSerializer(student).data)


class StudentClearanceStatusView(BaseView):
    """GET /api/student/clearance/status/"""
    permission_classes = []

    def get(self, request):
        student = getattr(request, 'student', None)
        if not student:
            return Response({'error': 'Authentication required.'}, status=401)
        try:
            clearance_req = ClearanceRequest.objects.prefetch_related(
                'dept_statuses__department',
                'dept_statuses__cleared_by'
            ).get(student=student)
            serializer = ClearanceStatusSerializer(clearance_req, context={'request': request})
            return Response(serializer.data)
        except ClearanceRequest.DoesNotExist:
            return Response({'has_request': False, 'message': 'No clearance request found.'}, status=404)


class StudentClearanceSubmitView(BaseView):
    """POST /api/student/clearance/submit/"""
    permission_classes = []

    def post(self, request):
        student = getattr(request, 'student', None)
        if not student:
            return Response({'error': 'Authentication required.'}, status=401)

        # Check for existing request
        if ClearanceRequest.objects.filter(student=student).exists():
            return Response(
                {'error': 'A clearance request already exists for this student.'},
                status=400
            )

        # Determine academic year
        today = timezone.now().date()
        year = today.year
        if today.month >= 9:
            academic_year = f"{year}/{year + 1}"
        else:
            academic_year = f"{year - 1}/{year}"

        academic_year = request.data.get('academic_year', academic_year)

        # Create clearance request
        clearance_req = ClearanceRequest.objects.create(
            student=student,
            academic_year=academic_year,
            overall_status='PENDING',
        )

        # Bulk-create 6 dept_clearance_status rows (parallel processing — Objective ii)
        depts = ClearanceDept.objects.all()
        DeptClearanceStatus.objects.bulk_create([
            DeptClearanceStatus(
                request=clearance_req,
                department=dept,
                status='PENDING',
            )
            for dept in depts
        ])

        # Send submission email (Objective iii)
        send_request_submitted_email(student, clearance_req)

        clearance_req.refresh_from_db()
        clearance_req_data = ClearanceRequest.objects.prefetch_related(
            'dept_statuses__department', 'dept_statuses__cleared_by'
        ).get(pk=clearance_req.pk)
        serializer = ClearanceStatusSerializer(clearance_req_data, context={'request': request})
        return Response(serializer.data, status=201)


class StudentCertificateView(BaseView):
    """GET /api/student/clearance/certificate/"""
    permission_classes = [IsStudent]

    def get(self, request):
        try:
            clearance_req = ClearanceRequest.objects.prefetch_related(
                'dept_statuses__department',
                'dept_statuses__cleared_by'
            ).get(student=request.student)
        except ClearanceRequest.DoesNotExist:
            return Response({'error': 'No clearance request found.'}, status=404)

        if clearance_req.overall_status != 'COMPLETED':
            return Response({'error': 'Clearance not yet completed.'}, status=403)

        serializer = ClearanceStatusSerializer(clearance_req, context={'request': request})
        return Response(serializer.data)


class StudentNotificationsView(BaseView):
    """GET /api/student/notifications/"""
    permission_classes = []

    def get(self, request):
        student = getattr(request, 'student', None)
        if not student:
            return Response({'error': 'Authentication required.'}, status=401)
        notifications = Notification.objects.filter(
            student=student
        ).order_by('-sent_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


# ─── STAFF VIEWS ──────────────────────────────────────────────────────────────

class StaffQueueView(BaseView):
    """GET /api/staff/queue/"""
    permission_classes = []

    def get(self, request):
        staff = getattr(request, 'staff', None)
        if not staff:
            return Response({'error': 'Authentication required.'}, status=401)
        filter_status = request.query_params.get('status', None)
        qs = DeptClearanceStatus.objects.filter(
            department=staff.department
        ).select_related(
            'request__student__programme__faculty',
            'department', 'cleared_by'
        ).order_by('-request__initiated_date')

        if filter_status:
            qs = qs.filter(status=filter_status.upper())

        serializer = StaffQueueItemSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class StaffQueueDetailView(BaseView):
    """GET /api/staff/queue/<request_id>/"""
    permission_classes = []

    def get(self, request, request_id):
        staff = getattr(request, 'staff', None)
        if not staff:
            return Response({'error': 'Authentication required.'}, status=401)
        try:
            dept_status = DeptClearanceStatus.objects.select_related(
                'request__student__programme__faculty',
                'department', 'cleared_by'
            ).get(
                request_id=request_id,
                department=staff.department
            )
        except DeptClearanceStatus.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        serializer = StaffQueueItemSerializer(dept_status, context={'request': request})
        return Response(serializer.data)


class StaffActionView(BaseView):
    """POST /api/staff/queue/<request_id>/action/"""
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, request_id):
        staff = getattr(request, 'staff', None)
        if not staff:
            return Response({'error': 'Authentication required.'}, status=401)

        try:
            dept_status = DeptClearanceStatus.objects.select_related(
                'request__student', 'department'
            ).get(request_id=request_id, department=staff.department)
        except DeptClearanceStatus.DoesNotExist:
            return Response({'error': 'Not found or not your department.'}, status=404)

        action = str(request.data.get('status', '') or '').strip().upper()
        remarks = str(request.data.get('remarks', '') or '').strip()
        document = request.FILES.get('document', None)

        if action not in ('CLEARED', 'REJECTED'):
            return Response({'error': 'status must be CLEARED or REJECTED. Got: ' + repr(action)}, status=400)

        if not remarks:
            return Response({'error': 'remarks are required.'}, status=400)

        dept_status.status = action
        dept_status.remarks = remarks
        dept_status.cleared_by = staff
        if document:
            dept_status.document = document
        dept_status.save()

        serializer = StaffQueueItemSerializer(dept_status, context={'request': request})
        return Response(serializer.data)


class StaffHistoryView(BaseView):
    """GET /api/staff/history/"""
    permission_classes = []

    def get(self, request):
        staff = getattr(request, 'staff', None)
        if not staff:
            return Response({'error': 'Authentication required.'}, status=401)
        qs = DeptClearanceStatus.objects.filter(
            cleared_by=staff
        ).select_related(
            'request__student__programme__faculty',
            'department', 'cleared_by'
        ).order_by('-updated_at')

        serializer = StaffQueueItemSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


# ─── ADMIN VIEWS ──────────────────────────────────────────────────────────────

class AdminRequestsView(BaseView):
    """GET /api/admin/requests/"""
    permission_classes = [IsAdminStaff]

    def get(self, request):
        qs = ClearanceRequest.objects.prefetch_related(
            'dept_statuses__department', 'dept_statuses__cleared_by',
            'student__programme__faculty'
        ).all().order_by('-initiated_date')

        # Filters
        overall_status = request.query_params.get('status')
        if overall_status:
            qs = qs.filter(overall_status=overall_status.upper())

        serializer = AdminRequestSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class AdminRequestDetailView(BaseView):
    """GET /api/admin/requests/<id>/"""
    permission_classes = [IsAdminStaff]

    def get(self, request, pk):
        try:
            req = ClearanceRequest.objects.prefetch_related(
                'dept_statuses__department', 'dept_statuses__cleared_by',
                'student__programme__faculty'
            ).get(pk=pk)
        except ClearanceRequest.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        serializer = AdminRequestSerializer(req, context={'request': request})
        return Response(serializer.data)


class AdminStaffView(BaseView):
    """GET/POST /api/admin/staff/"""
    permission_classes = [IsAdminStaff]

    def get(self, request):
        staff_qs = Staff.objects.select_related('department').all().order_by('department__code', 'staff_number')
        serializer = StaffSerializer(staff_qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StaffCreateSerializer(data=request.data)
        if serializer.is_valid():
            staff = serializer.save()
            return Response(StaffSerializer(staff).data, status=201)
        return Response(serializer.errors, status=400)


class AdminStaffDetailView(BaseView):
    """PUT /api/admin/staff/<id>/"""
    permission_classes = [IsAdminStaff]

    def get(self, request, pk):
        try:
            staff = Staff.objects.select_related('department').get(pk=pk)
        except Staff.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)
        return Response(StaffSerializer(staff).data)

    def put(self, request, pk):
        try:
            staff = Staff.objects.select_related('department').get(pk=pk)
        except Staff.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        serializer = StaffSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class AdminReportsSummaryView(BaseView):
    """GET /api/admin/reports/summary/"""
    permission_classes = [IsAdminStaff]

    def get(self, request):
        total = ClearanceRequest.objects.count()
        pending = ClearanceRequest.objects.filter(overall_status='PENDING').count()
        in_progress = ClearanceRequest.objects.filter(overall_status='IN_PROGRESS').count()
        completed = ClearanceRequest.objects.filter(overall_status='COMPLETED').count()
        rejected = ClearanceRequest.objects.filter(overall_status='REJECTED').count()

        depts = ClearanceDept.objects.all()
        by_department = []
        for dept in depts:
            d_pending = DeptClearanceStatus.objects.filter(department=dept, status='PENDING').count()
            d_cleared = DeptClearanceStatus.objects.filter(department=dept, status='CLEARED').count()
            d_rejected = DeptClearanceStatus.objects.filter(department=dept, status='REJECTED').count()
            by_department.append({
                'department': dept.name,
                'code': dept.code,
                'pending': d_pending,
                'cleared': d_cleared,
                'rejected': d_rejected,
            })

        return Response({
            'total_requests': total,
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed,
            'rejected': rejected,
            'by_department': by_department,
        })


class StudentForgotPasswordView(BaseView):
    """POST /api/auth/student/forgot-password/"""

    def post(self, request):
        import secrets, string
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email address is required.'}, status=400)
        try:
            student = Student.objects.get(email__iexact=email)
        except Student.DoesNotExist:
            # Security: don't reveal if email exists or not
            return Response({'message': 'If an account with that email exists, a password reset link has been sent.'})
        # Generate temp password
        temp_pw = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
        student.set_password(temp_pw)
        student.save(update_fields=['password_hash'])
        # Send email
        from django.core.mail import send_mail
        from django.conf import settings
        try:
            send_mail(
                subject='MMU Clearance — Password Reset',
                message=f"""Dear {student.full_name},

Your password has been reset as requested.

Temporary Password: {temp_pw}

Please log in and change your password immediately.

Login at: https://mmu-student-clearance-system-sm2r.vercel.app/login/

Best regards,
MMU Clearance System
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({'error': 'Could not send email. Please contact the clearance office.'}, status=500)
        return Response({'message': f'A temporary password has been sent to {email}. Please check your inbox.'})


class StaffForgotPasswordView(BaseView):
    """POST /api/auth/staff/forgot-password/"""

    def post(self, request):
        import secrets, string
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email address is required.'}, status=400)
        try:
            staff = Staff.objects.get(email__iexact=email)
        except Staff.DoesNotExist:
            return Response({'message': 'If an account with that email exists, a password reset link has been sent.'})
        temp_pw = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
        staff.set_password(temp_pw)
        staff.save(update_fields=['password_hash'])
        from django.core.mail import send_mail
        from django.conf import settings
        try:
            send_mail(
                subject='MMU Clearance — Staff Password Reset',
                message=f"""Dear {staff.full_name},

Your staff portal password has been reset.

Temporary Password: {temp_pw}

Please log in and inform the system administrator to update your password.

Login at: https://mmu-student-clearance-system-sm2r.vercel.app/staff/login/

Best regards,
MMU Clearance System
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff.email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({'error': 'Could not send email. Please contact the system administrator.'}, status=500)
        return Response({'message': f'A temporary password has been sent to {email}. Please check your inbox.'})


class StudentClearanceResubmitView(BaseView):
    """POST /api/student/clearance/resubmit/ — resubmit after rejection with proof"""
    permission_classes = [IsStudent]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        student = request.student
        try:
            clearance_req = ClearanceRequest.objects.get(student=student)
        except ClearanceRequest.DoesNotExist:
            return Response({'error': 'No clearance request found.'}, status=404)

        if clearance_req.overall_status != 'REJECTED':
            return Response({'error': 'Only rejected clearance requests can be resubmitted.'}, status=400)

        proof_document = request.FILES.get('proof_document', None)
        note = request.data.get('note', '').strip()

        if not proof_document:
            return Response({'error': 'Proof of resolution document is required.'}, status=400)

        # Reset all REJECTED dept statuses back to PENDING, attach proof to rejected ones
        rejected_depts = clearance_req.dept_statuses.filter(status='REJECTED')
        for ds in rejected_depts:
            ds.status = 'PENDING'
            ds.document = proof_document
            ds.remarks = f'[RESUBMITTED] {note}' if note else '[Student resubmitted with proof of resolution]'
            ds.cleared_by = None
            ds.save()

        # Reset overall status
        clearance_req.overall_status = 'IN_PROGRESS'
        clearance_req.completed_date = None
        clearance_req.save(update_fields=['overall_status', 'completed_date'])

        # Notify student
        from .emails import _send_and_log
        _send_and_log(
            student=student,
            clearance_request=clearance_req,
            subject='Clearance Resubmitted — MMU',
            message=f"""Dear {student.full_name},

Your clearance request has been resubmitted successfully.

The departments that previously rejected your request have been notified and will review your proof of resolution.

Registration Number: {student.reg_number}
Status: IN PROGRESS

You can track your status at your clearance dashboard.

Best regards,
MMU Clearance System
""",
            notif_type='REQUEST_SUBMITTED',
        )

        clearance_req.refresh_from_db()
        data = ClearanceRequest.objects.prefetch_related(
            'dept_statuses__department', 'dept_statuses__cleared_by'
        ).get(pk=clearance_req.pk)
        serializer = ClearanceStatusSerializer(data, context={'request': request})
        return Response(serializer.data)
