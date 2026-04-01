from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Faculty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faculty_code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('dean_name', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={'db_table': 'faculty', 'verbose_name_plural': 'Faculties'},
        ),
        migrations.CreateModel(
            name='ClearanceDept',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=80)),
                ('contact_email', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={'db_table': 'clearance_dept', 'verbose_name': 'Clearance Department', 'verbose_name_plural': 'Clearance Departments'},
        ),
        migrations.CreateModel(
            name='Programme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('programme_code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('level', models.CharField(choices=[('Undergraduate', 'Undergraduate'), ('Postgraduate', 'Postgraduate'), ('Diploma', 'Diploma'), ('Certificate', 'Certificate')], max_length=30)),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='programmes', to='clearance.faculty')),
            ],
            options={'db_table': 'programme'},
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reg_number', models.CharField(blank=True, max_length=25, unique=True)),
                ('first_name', models.CharField(max_length=60)),
                ('last_name', models.CharField(max_length=60)),
                ('email', models.EmailField(max_length=120, unique=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('admission_year', models.SmallIntegerField()),
                ('cohort_number', models.SmallIntegerField()),
                ('password_hash', models.CharField(max_length=255)),
                ('programme', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='students', to='clearance.programme')),
            ],
            options={'db_table': 'student'},
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('staff_number', models.CharField(max_length=20, unique=True)),
                ('first_name', models.CharField(max_length=60)),
                ('last_name', models.CharField(max_length=60)),
                ('email', models.EmailField(max_length=120, unique=True)),
                ('password_hash', models.CharField(max_length=255)),
                ('role', models.CharField(choices=[('officer', 'Officer'), ('admin', 'Admin')], default='officer', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='staff_members', to='clearance.clearancedept')),
            ],
            options={'db_table': 'staff', 'verbose_name_plural': 'Staff'},
        ),
        migrations.CreateModel(
            name='ClearanceRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initiated_date', models.DateField(auto_now_add=True)),
                ('completed_date', models.DateField(blank=True, null=True)),
                ('academic_year', models.CharField(max_length=12)),
                ('overall_status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='clearance_request', to='clearance.student')),
            ],
            options={'db_table': 'clearance_request'},
        ),
        migrations.CreateModel(
            name='DeptClearanceStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('CLEARED', 'Cleared'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('document', models.FileField(blank=True, null=True, upload_to='clearance_docs/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cleared_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_taken', to='clearance.staff')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='clearance_statuses', to='clearance.clearancedept')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dept_statuses', to='clearance.clearancerequest')),
            ],
            options={'db_table': 'dept_clearance_status', 'verbose_name': 'Department Clearance Status', 'verbose_name_plural': 'Department Clearance Statuses'},
        ),
        migrations.AddConstraint(
            model_name='deptclearancestatus',
            constraint=models.UniqueConstraint(fields=('request', 'department'), name='uq_request_department'),
        ),
        migrations.CreateModel(
            name='LibraryRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('books_borrowed', models.SmallIntegerField(default=0)),
                ('books_returned', models.SmallIntegerField(default=0)),
                ('fines_due', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='library_record', to='clearance.student')),
            ],
            options={'db_table': 'library_record'},
        ),
        migrations.CreateModel(
            name='FinanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fees_balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('other_dues', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='finance_record', to='clearance.student')),
            ],
            options={'db_table': 'finance_record'},
        ),
        migrations.CreateModel(
            name='HostelRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_number', models.CharField(max_length=20)),
                ('block', models.CharField(max_length=40)),
                ('balance_due', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hostel_record', to='clearance.student')),
            ],
            options={'db_table': 'hostel_record'},
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('REQUEST_SUBMITTED', 'Request Submitted'), ('DEPT_CLEARED', 'Department Cleared'), ('DEPT_REJECTED', 'Department Rejected'), ('CLEARANCE_COMPLETE', 'Clearance Complete')], max_length=40)),
                ('message', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('SENT', 'Sent'), ('FAILED', 'Failed')], default='SENT', max_length=20)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='clearance.clearancerequest')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='clearance.student')),
            ],
            options={'db_table': 'notification'},
        ),
    ]
