from rest_framework import serializers
from .models import (
    Faculty, Programme, Student, ClearanceDept, Staff,
    ClearanceRequest, DeptClearanceStatus, LibraryRecord,
    FinanceRecord, HostelRecord, Notification
)


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = '__all__'


class ProgrammeSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    faculty_code = serializers.CharField(source='faculty.faculty_code', read_only=True)

    class Meta:
        model = Programme
        fields = ['id', 'programme_code', 'name', 'level', 'faculty_id', 'faculty_name', 'faculty_code']


class StudentProfileSerializer(serializers.ModelSerializer):
    programme_name = serializers.CharField(source='programme.name', read_only=True)
    programme_code = serializers.CharField(source='programme.programme_code', read_only=True)
    faculty_name = serializers.CharField(source='programme.faculty.name', read_only=True)
    faculty_code = serializers.CharField(source='programme.faculty.faculty_code', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'reg_number', 'first_name', 'last_name', 'email', 'phone',
            'admission_year', 'cohort_number', 'programme_id',
            'programme_name', 'programme_code', 'faculty_name', 'faculty_code'
        ]


class ClearanceDeptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClearanceDept
        fields = '__all__'


class StaffSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id', 'staff_number', 'first_name', 'last_name', 'email',
            'role', 'department_id', 'department_name', 'department_code', 'is_active'
        ]


class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Staff
        fields = [
            'staff_number', 'first_name', 'last_name', 'email',
            'role', 'department_id', 'is_active', 'password'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        staff = Staff(**validated_data)
        staff.set_password(password)
        staff.save()
        return staff


class DeptClearanceStatusSerializer(serializers.ModelSerializer):
    department_code = serializers.CharField(source='department.code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    cleared_by_name = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = DeptClearanceStatus
        fields = [
            'id', 'request_id', 'department_id', 'department_code', 'department_name',
            'status', 'remarks', 'document', 'document_url', 'updated_at',
            'cleared_by', 'cleared_by_name'
        ]

    def get_cleared_by_name(self, obj):
        if obj.cleared_by:
            return obj.cleared_by.full_name
        return None

    def get_document_url(self, obj):
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None


class ClearanceStatusSerializer(serializers.ModelSerializer):
    """Full dashboard data for student — includes all dept statuses."""
    dept_statuses = DeptClearanceStatusSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    reg_number = serializers.CharField(source='student.reg_number', read_only=True)
    cleared_count = serializers.SerializerMethodField()

    class Meta:
        model = ClearanceRequest
        fields = [
            'id', 'student_id', 'student_name', 'reg_number',
            'initiated_date', 'completed_date', 'academic_year',
            'overall_status', 'dept_statuses', 'cleared_count'
        ]

    def get_cleared_count(self, obj):
        return obj.dept_statuses.filter(status='CLEARED').count()


class LibraryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryRecord
        fields = '__all__'


class FinanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceRecord
        fields = '__all__'


class HostelRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelRecord
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class StaffQueueItemSerializer(serializers.ModelSerializer):
    """For staff queue — shows student info alongside dept status."""
    student = StudentProfileSerializer(source='request.student', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    request_id = serializers.IntegerField(source='request.id', read_only=True)
    academic_year = serializers.CharField(source='request.academic_year', read_only=True)
    initiated_date = serializers.DateField(source='request.initiated_date', read_only=True)
    cleared_by_name = serializers.SerializerMethodField()
    library_record = serializers.SerializerMethodField()
    finance_record = serializers.SerializerMethodField()
    hostel_record = serializers.SerializerMethodField()

    class Meta:
        model = DeptClearanceStatus
        fields = [
            'id', 'request_id', 'student', 'department_name',
            'status', 'remarks', 'document', 'updated_at',
            'cleared_by', 'cleared_by_name',
            'academic_year', 'initiated_date',
            'library_record', 'finance_record', 'hostel_record'
        ]

    def get_cleared_by_name(self, obj):
        if obj.cleared_by:
            return obj.cleared_by.full_name
        return None

    def get_library_record(self, obj):
        try:
            rec = obj.request.student.library_record
            return LibraryRecordSerializer(rec).data
        except Exception:
            return None

    def get_finance_record(self, obj):
        try:
            rec = obj.request.student.finance_record
            return FinanceRecordSerializer(rec).data
        except Exception:
            return None

    def get_hostel_record(self, obj):
        try:
            rec = obj.request.student.hostel_record
            return HostelRecordSerializer(rec).data
        except Exception:
            return None


class AdminRequestSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)
    dept_statuses = DeptClearanceStatusSerializer(many=True, read_only=True)
    cleared_count = serializers.SerializerMethodField()

    class Meta:
        model = ClearanceRequest
        fields = '__all__'
        extra_fields = ['student', 'dept_statuses', 'cleared_count']

    def get_cleared_count(self, obj):
        return obj.dept_statuses.filter(status='CLEARED').count()


class AdminSummarySerializer(serializers.Serializer):
    total_requests = serializers.IntegerField()
    pending = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    completed = serializers.IntegerField()
    rejected = serializers.IntegerField()
    by_department = serializers.ListField()
