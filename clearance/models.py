from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password


class Faculty(models.Model):
    faculty_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=120)
    dean_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'faculty'
        verbose_name_plural = 'Faculties'

    def __str__(self):
        return f"{self.faculty_code} - {self.name}"


PROGRAMME_LEVEL_CHOICES = [
    ('Undergraduate', 'Undergraduate'),
    ('Postgraduate', 'Postgraduate'),
    ('Diploma', 'Diploma'),
    ('Certificate', 'Certificate'),
]


class Programme(models.Model):
    programme_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=150)
    level = models.CharField(max_length=30, choices=PROGRAMME_LEVEL_CHOICES)
    faculty = models.ForeignKey(Faculty, on_delete=models.RESTRICT, related_name='programmes')

    class Meta:
        db_table = 'programme'

    def __str__(self):
        return f"{self.programme_code} - {self.name}"


class Student(models.Model):
    reg_number = models.CharField(max_length=25, unique=True, blank=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    email = models.EmailField(max_length=120, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    admission_year = models.SmallIntegerField()
    cohort_number = models.SmallIntegerField()
    programme = models.ForeignKey(Programme, on_delete=models.RESTRICT, related_name='students')
    password_hash = models.CharField(max_length=255)

    class Meta:
        db_table = 'student'

    def __str__(self):
        return f"{self.reg_number} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def generate_reg_number(self):
        faculty_code = self.programme.faculty.faculty_code
        programme_code = self.programme.programme_code
        return f"{faculty_code}-{programme_code}-{self.cohort_number:03d}/{self.admission_year}"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password_hash)

    def save(self, *args, **kwargs):
        if not self.reg_number:
            self.reg_number = self.generate_reg_number()
        super().save(*args, **kwargs)


class ClearanceDept(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=80)
    contact_email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'clearance_dept'
        verbose_name = 'Clearance Department'
        verbose_name_plural = 'Clearance Departments'

    def __str__(self):
        return f"{self.code} - {self.name}"


STAFF_ROLE_CHOICES = [
    ('officer', 'Officer'),
    ('admin', 'Admin'),
]


class Staff(models.Model):
    staff_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    email = models.EmailField(max_length=120, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=STAFF_ROLE_CHOICES, default='officer')
    department = models.ForeignKey(ClearanceDept, on_delete=models.RESTRICT, related_name='staff_members')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'staff'
        verbose_name_plural = 'Staff'

    def __str__(self):
        return f"{self.staff_number} - {self.first_name} {self.last_name} ({self.department.code})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password_hash)


OVERALL_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('IN_PROGRESS', 'In Progress'),
    ('COMPLETED', 'Completed'),
    ('REJECTED', 'Rejected'),
]


class ClearanceRequest(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='clearance_request')
    initiated_date = models.DateField(auto_now_add=True)
    completed_date = models.DateField(null=True, blank=True)
    academic_year = models.CharField(max_length=12)
    overall_status = models.CharField(max_length=20, choices=OVERALL_STATUS_CHOICES, default='PENDING')

    class Meta:
        db_table = 'clearance_request'

    def __str__(self):
        return f"Request #{self.pk} - {self.student.reg_number} ({self.overall_status})"

    def recalculate_status(self):
        """Recalculate overall_status based on all department statuses."""
        dept_statuses = self.dept_statuses.all()
        if not dept_statuses.exists():
            return

        statuses = list(dept_statuses.values_list('status', flat=True))

        if 'REJECTED' in statuses:
            self.overall_status = 'REJECTED'
        elif all(s == 'CLEARED' for s in statuses):
            from django.utils import timezone
            self.overall_status = 'COMPLETED'
            self.completed_date = timezone.now().date()
        else:
            self.overall_status = 'IN_PROGRESS'

        self.save(update_fields=['overall_status', 'completed_date'])


DEPT_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('CLEARED', 'Cleared'),
    ('REJECTED', 'Rejected'),
]


class DeptClearanceStatus(models.Model):
    request = models.ForeignKey(ClearanceRequest, on_delete=models.CASCADE, related_name='dept_statuses')
    department = models.ForeignKey(ClearanceDept, on_delete=models.RESTRICT, related_name='clearance_statuses')
    cleared_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_taken')
    status = models.CharField(max_length=20, choices=DEPT_STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='clearance_docs/', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dept_clearance_status'
        unique_together = [('request', 'department')]
        verbose_name = 'Department Clearance Status'
        verbose_name_plural = 'Department Clearance Statuses'

    def __str__(self):
        return f"{self.request.student.reg_number} - {self.department.code}: {self.status}"


class LibraryRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='library_record')
    books_borrowed = models.SmallIntegerField(default=0)
    books_returned = models.SmallIntegerField(default=0)
    fines_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'library_record'

    def __str__(self):
        return f"Library: {self.student.reg_number}"


class FinanceRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='finance_record')
    fees_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_dues = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'finance_record'

    def __str__(self):
        return f"Finance: {self.student.reg_number}"


class HostelRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='hostel_record')
    room_number = models.CharField(max_length=20)
    block = models.CharField(max_length=40)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'hostel_record'

    def __str__(self):
        return f"Hostel: {self.student.reg_number} - {self.block}/{self.room_number}"


NOTIFICATION_TYPE_CHOICES = [
    ('REQUEST_SUBMITTED', 'Request Submitted'),
    ('DEPT_CLEARED', 'Department Cleared'),
    ('DEPT_REJECTED', 'Department Rejected'),
    ('CLEARANCE_COMPLETE', 'Clearance Complete'),
]

NOTIFICATION_STATUS_CHOICES = [
    ('SENT', 'Sent'),
    ('FAILED', 'Failed'),
]


class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    request = models.ForeignKey(ClearanceRequest, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=40, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS_CHOICES, default='SENT')

    class Meta:
        db_table = 'notification'

    def __str__(self):
        return f"Notification to {self.student.reg_number}: {self.type} ({self.status})"
