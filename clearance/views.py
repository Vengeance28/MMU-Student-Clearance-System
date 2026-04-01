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
    permission_classes = [IsStudent]

    def get(self, request):
        return Response(StudentProfileSerializer(request.student).data)


class StudentClearanceStatusView(BaseView):
    """GET /api/student/clearance/status/"""
    permission_classes = [IsStudent]

    def get(self, request):
        try:
            clearance_req = ClearanceRequest.objects.prefetch_related(
                'dept_statuses__department',
                'dept_statuses__cleared_by'
            ).get(student=request.student)
            serializer = ClearanceStatusSerializer(clearance_req, context={'request': request})
            return Response(serializer.data)
        except ClearanceRequest.DoesNotExist:
            return Response({'has_request': False, 'message': 'No clearance request found.'}, status=404)


class StudentClearanceSubmitView(BaseView):
    """POST /api/student/clearance/submit/"""
    permission_classes = [IsStudent]

    def post(self, request):
        student = request.student

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
    permission_classes = [IsStudent]

    def get(self, request):
        notifications = Notification.objects.filter(
            student=request.student
        ).order_by('-sent_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


# ─── STAFF VIEWS ──────────────────────────────────────────────────────────────

class StaffQueueView(BaseView):
    """GET /api/staff/queue/"""
    permission_classes = [IsStaff]

    def get(self, request):
        filter_status = request.query_params.get('status', None)
        qs = DeptClearanceStatus.objects.filter(
            department=request.staff.department
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
    permission_classes = [IsStaff]

    def get(self, request, request_id):
        try:
            dept_status = DeptClearanceStatus.objects.select_related(
                'request__student__programme__faculty',
                'department', 'cleared_by'
            ).get(
                request_id=request_id,
                department=request.staff.department
            )
        except DeptClearanceStatus.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        serializer = StaffQueueItemSerializer(dept_status, context={'request': request})
        return Response(serializer.data)


class StaffActionView(BaseView):
    """POST /api/staff/queue/<request_id>/action/"""
    permission_classes = [IsStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, request_id):
        try:
            dept_status = DeptClearanceStatus.objects.select_related(
                'request__student', 'department'
            ).get(
                request_id=request_id,
                department=request.staff.department
            )
        except DeptClearanceStatus.DoesNotExist:
            return Response({'error': 'Not found or not your department.'}, status=404)

        action = request.data.get('status', '').upper()
        remarks = request.data.get('remarks', '').strip()
        document = request.FILES.get('document', None)

        if action not in ('CLEARED', 'REJECTED'):
            return Response({'error': 'status must be CLEARED or REJECTED.'}, status=400)

        if not remarks:
            return Response({'error': 'remarks are required.'}, status=400)

        dept_status.status = action
        dept_status.remarks = remarks
        dept_status.cleared_by = request.staff
        if document:
            dept_status.document = document
        dept_status.save()  # Triggers post_save signal → recalculate + email

        serializer = StaffQueueItemSerializer(dept_status, context={'request': request})
        return Response(serializer.data)


class StaffHistoryView(BaseView):
    """GET /api/staff/history/"""
    permission_classes = [IsStaff]

    def get(self, request):
        qs = DeptClearanceStatus.objects.filter(
            cleared_by=request.staff
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
