from django.core.management.base import BaseCommand
from django.db import transaction
from clearance.models import Faculty, Programme, ClearanceDept, Student, Staff, LibraryRecord, FinanceRecord, HostelRecord


class Command(BaseCommand):
    help = 'Seed MMU database with faculties, programmes, departments, and test accounts'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding MMU data...')

        # ── 6 Faculties ──────────────────────────────────────────────────────
        faculties_data = [
            ('CIT', 'Faculty of Computing and Information Technology', 'Prof. John Doe', 'cit@mmu.ac.ke'),
            ('BUS', 'Faculty of Business and Economics', 'Prof. Jane Smith', 'bus@mmu.ac.ke'),
            ('MED', 'Faculty of Media and Communication', 'Prof. Alex Mwangi', 'med@mmu.ac.ke'),
            ('ENG', 'Faculty of Engineering and Technology', 'Prof. Sarah Ochieng', 'eng@mmu.ac.ke'),
            ('SST', 'Faculty of Social Sciences and Technology', 'Prof. David Kamau', 'sst@mmu.ac.ke'),
            ('SCI', 'Faculty of Science and Technology', 'Prof. Mary Wanjiku', 'sci@mmu.ac.ke'),
        ]
        faculties = {}
        for code, name, dean, email in faculties_data:
            f, _ = Faculty.objects.get_or_create(faculty_code=code, defaults={'name': name, 'dean_name': dean, 'email': email})
            faculties[code] = f
        self.stdout.write(f'  ✓ {len(faculties)} faculties ready')

        # ── Programmes ───────────────────────────────────────────────────────
        programmes_data = [
            # CIT
            ('221', 'BSc Information Technology', 'Undergraduate', 'CIT'),
            ('222', 'BSc Computer Technology', 'Undergraduate', 'CIT'),
            ('223', 'BSc Software Engineering', 'Undergraduate', 'CIT'),
            ('224', 'BSc Computer Science', 'Undergraduate', 'CIT'),
            ('225', 'Diploma in ICT', 'Diploma', 'CIT'),
            ('226', 'MSc Information Technology', 'Postgraduate', 'CIT'),
            ('227', 'MSc Computer Science', 'Postgraduate', 'CIT'),
            # BUS
            ('231', 'Bachelor of Commerce', 'Undergraduate', 'BUS'),
            ('232', 'Bachelor of Business Information Technology', 'Undergraduate', 'BUS'),
            ('233', 'BSc Actuarial Science', 'Undergraduate', 'BUS'),
            ('234', 'BSc Economics', 'Undergraduate', 'BUS'),
            ('235', 'Bachelor of Procurement and Logistics Management', 'Undergraduate', 'BUS'),
            ('236', 'Diploma in Business Administration', 'Diploma', 'BUS'),
            ('237', 'MBA', 'Postgraduate', 'BUS'),
            ('238', 'MSc Economics', 'Postgraduate', 'BUS'),
            # MED
            ('241', 'Bachelor of Science in Journalism', 'Undergraduate', 'MED'),
            ('242', 'Bachelor of Film and Theatre Arts', 'Undergraduate', 'MED'),
            ('243', 'Diploma in Media Studies', 'Diploma', 'MED'),
            # ENG
            ('251', 'BSc Electrical and Electronic Engineering', 'Undergraduate', 'ENG'),
            ('252', 'BSc Telecommunication Engineering', 'Undergraduate', 'ENG'),
            ('253', 'BSc Mechanical Engineering', 'Undergraduate', 'ENG'),
            ('254', 'Diploma in Engineering', 'Diploma', 'ENG'),
            # SST
            ('261', 'Bachelor of Arts in Sociology', 'Undergraduate', 'SST'),
            ('262', 'Bachelor of Arts in Criminology', 'Undergraduate', 'SST'),
            ('263', 'BSc Peace and Conflict Studies', 'Undergraduate', 'SST'),
            # SCI
            ('271', 'BSc Mathematics', 'Undergraduate', 'SCI'),
            ('272', 'BSc Physics', 'Undergraduate', 'SCI'),
            ('273', 'BSc Chemistry', 'Undergraduate', 'SCI'),
            ('274', 'BSc Biochemistry', 'Undergraduate', 'SCI'),
        ]
        programmes = {}
        for code, name, level, fac_code in programmes_data:
            p, _ = Programme.objects.get_or_create(
                programme_code=code,
                defaults={'name': name, 'level': level, 'faculty': faculties[fac_code]}
            )
            programmes[code] = p
        self.stdout.write(f'  ✓ {len(programmes)} programmes ready')

        # ── 6 Clearance Departments ──────────────────────────────────────────
        depts_data = [
            ('LIBRARY', 'Library', 'library@mmu.ac.ke'),
            ('FINANCE', 'Finance', 'finance@mmu.ac.ke'),
            ('HOSTELS', 'Hostels', 'hostels@mmu.ac.ke'),
            ('FACULTY', 'Faculty/School', 'faculty@mmu.ac.ke'),
            ('ICT', 'ICT Services', 'ict@mmu.ac.ke'),
            ('REGISTRY', 'Registry', 'registry@mmu.ac.ke'),
        ]
        depts = {}
        for code, name, email in depts_data:
            d, _ = ClearanceDept.objects.get_or_create(code=code, defaults={'name': name, 'contact_email': email})
            depts[code] = d
        self.stdout.write(f'  ✓ 6 clearance departments ready')

        # ── Test Student ─────────────────────────────────────────────────────
        cit_222 = programmes['222']
        if not Student.objects.filter(reg_number='CIT-222-044/2020').exists():
            student = Student(
                first_name='Victor',
                last_name='Kimutai',
                email='vkimu20@gmail.com',
                phone='+254712345678',
                admission_year=2020,
                cohort_number=44,
                programme=cit_222,
            )
            student.set_password('student123')
            student.save()
            # Supporting records
            LibraryRecord.objects.get_or_create(student=student, defaults={'books_borrowed': 3, 'books_returned': 2, 'fines_due': 50.00})
            FinanceRecord.objects.get_or_create(student=student, defaults={'fees_balance': 0.00, 'other_dues': 0.00})
            HostelRecord.objects.get_or_create(student=student, defaults={'room_number': 'A104', 'block': 'Block A', 'balance_due': 0.00})
            self.stdout.write(f'  ✓ Test student: CIT-222-044/2020 / student123')
        else:
            self.stdout.write(f'  ℹ Test student already exists')

        # ── Test Staff (one per dept + admin) ────────────────────────────────
        staff_data = [
            ('LIB-001', 'Alice', 'Njoroge', 'alice.njoroge@mmu.ac.ke', 'officer', 'LIBRARY'),
            ('FIN-001', 'Bob', 'Otieno', 'bob.otieno@mmu.ac.ke', 'officer', 'FINANCE'),
            ('HOS-001', 'Carol', 'Wambui', 'carol.wambui@mmu.ac.ke', 'officer', 'HOSTELS'),
            ('FAC-001', 'Daniel', 'Mutua', 'daniel.mutua@mmu.ac.ke', 'officer', 'FACULTY'),
            ('ICT-001', 'Eve', 'Achieng', 'eve.achieng@mmu.ac.ke', 'officer', 'ICT'),
            ('REG-001', 'Frank', 'Kiplagat', 'frank.kiplagat@mmu.ac.ke', 'officer', 'REGISTRY'),
            ('ADM-001', 'Grace', 'Mwangi', 'grace.mwangi@mmu.ac.ke', 'admin', 'REGISTRY'),
        ]
        passwords = {
            'ADM-001': 'admin123',
        }
        for staff_num, fname, lname, email, role, dept_code in staff_data:
            if not Staff.objects.filter(staff_number=staff_num).exists():
                staff = Staff(
                    staff_number=staff_num,
                    first_name=fname,
                    last_name=lname,
                    email=email,
                    role=role,
                    department=depts[dept_code],
                    is_active=True,
                )
                pw = passwords.get(staff_num, 'staff123')
                staff.set_password(pw)
                staff.save()
        self.stdout.write(f'  ✓ 7 staff accounts ready (staff123 / admin123)')

        self.stdout.write(self.style.SUCCESS('\n✅ MMU seed data loaded successfully!\n'))
        self.stdout.write('Test Accounts:')
        self.stdout.write('  STUDENT:  CIT-222-044/2020  / student123')
        self.stdout.write('  STAFF:    LIB-001, FIN-001, HOS-001, FAC-001, ICT-001, REG-001  / staff123')
        self.stdout.write('  ADMIN:    ADM-001  / admin123')
