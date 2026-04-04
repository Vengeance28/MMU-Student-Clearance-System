from django.core.management.base import BaseCommand
from django.db import transaction
from clearance.models import Faculty, Programme, ClearanceDept, Student, Staff, LibraryRecord, FinanceRecord, HostelRecord


STUDENTS_BY_FACULTY = {
    'CIT': [
        ('James',  'Mwangi',   'james.mwangi@gmail.com',   '+254711001001', 2021, 10, '222'),
        ('Grace',  'Otieno',   'grace.otieno@gmail.com',   '+254711001002', 2021, 11, '221'),
        ('Brian',  'Kipchoge', 'brian.kipchoge@gmail.com', '+254711001003', 2022, 5,  '223'),
        ('Cynthia','Wanjiku',  'cynthia.wanjiku@gmail.com','+254711001004', 2022, 6,  '224'),
        ('Dennis', 'Ochieng',  'dennis.ochieng@gmail.com', '+254711001005', 2020, 20, '222'),
        ('Faith',  'Kamau',    'faith.kamau@gmail.com',    '+254711001006', 2023, 3,  '225'),
        ('George', 'Mutua',    'george.mutua@gmail.com',   '+254711001007', 2021, 12, '224'),
    ],
    'BUS': [
        ('Hannah', 'Njoroge',  'hannah.njoroge@gmail.com', '+254722002001', 2021, 15, '231'),
        ('Ian',    'Oduya',    'ian.oduya@gmail.com',      '+254722002002', 2021, 16, '232'),
        ('Judy',   'Achieng',  'judy.achieng@gmail.com',   '+254722002003', 2022, 8,  '233'),
        ('Kevin',  'Kimani',   'kevin.kimani@gmail.com',   '+254722002004', 2020, 30, '234'),
        ('Linda',  'Waweru',   'linda.waweru@gmail.com',   '+254722002005', 2022, 9,  '235'),
        ('Martin', 'Cheruiyot','martin.cheruiyot@gmail.com','+254722002006',2021, 17, '236'),
        ('Nancy',  'Mbugua',   'nancy.mbugua@gmail.com',   '+254722002007', 2023, 4,  '231'),
    ],
    'MED': [
        ('Oscar',  'Kariuki',  'oscar.kariuki@gmail.com',  '+254733003001', 2021, 22, '241'),
        ('Purity', 'Njeri',    'purity.njeri@gmail.com',   '+254733003002', 2022, 7,  '242'),
        ('Quentin','Oluoch',   'quentin.oluoch@gmail.com', '+254733003003', 2020, 25, '241'),
        ('Rachel', 'Wangui',   'rachel.wangui@gmail.com',  '+254733003004', 2021, 23, '243'),
        ('Samuel', 'Koech',    'samuel.koech@gmail.com',   '+254733003005', 2022, 10, '242'),
        ('Tabitha','Maina',    'tabitha.maina@gmail.com',  '+254733003006', 2023, 2,  '241'),
        ('Usman',  'Hassan',   'usman.hassan@gmail.com',   '+254733003007', 2021, 24, '243'),
    ],
    'ENG': [
        ('Violet', 'Chebet',   'violet.chebet@gmail.com',  '+254744004001', 2021, 18, '251'),
        ('Walter', 'Omondi',   'walter.omondi@gmail.com',  '+254744004002', 2020, 35, '252'),
        ('Xenia',  'Kimetto',  'xenia.kimetto@gmail.com',  '+254744004003', 2022, 11, '253'),
        ('Yusuf',  'Abdi',     'yusuf.abdi@gmail.com',     '+254744004004', 2021, 19, '251'),
        ('Zipporah','Rotich',  'zipporah.rotich@gmail.com','+254744004005', 2022, 12, '252'),
        ('Aaron',  'Nganga',   'aaron.nganga@gmail.com',   '+254744004006', 2023, 5,  '254'),
        ('Beatrice','Simiyu',  'beatrice.simiyu@gmail.com','+254744004007', 2020, 36, '253'),
    ],
    'SST': [
        ('Charles','Kiplagat', 'charles.kiplagat@gmail.com','+254755005001',2021, 28, '261'),
        ('Dorcas', 'Ayieko',   'dorcas.ayieko@gmail.com',  '+254755005002', 2022, 13, '262'),
        ('Edward', 'Mwenda',   'edward.mwenda@gmail.com',  '+254755005003', 2020, 40, '263'),
        ('Florence','Nyambura','florence.nyambura@gmail.com','+254755005004',2021,29, '261'),
        ('Gerald', 'Owino',    'gerald.owino@gmail.com',   '+254755005005', 2022, 14, '262'),
        ('Hilda',  'Lagat',    'hilda.lagat@gmail.com',    '+254755005006', 2023, 6,  '263'),
        ('Isaac',  'Wekesa',   'isaac.wekesa@gmail.com',   '+254755005007', 2021, 30, '261'),
    ],
    'SCI': [
        ('Janet',  'Chepchumba','janet.chepchumba@gmail.com','+254766006001',2021,35, '271'),
        ('Kenneth','Muthoni',  'kenneth.muthoni@gmail.com','+254766006002', 2022, 15, '272'),
        ('Lilian', 'Gacheru',  'lilian.gacheru@gmail.com', '+254766006003', 2020, 45, '273'),
        ('Michael','Barasa',   'michael.barasa@gmail.com', '+254766006004', 2021, 36, '274'),
        ('Naomi',  'Chepkemoi','naomi.chepkemoi@gmail.com','+254766006005', 2022, 16, '271'),
        ('Patrick','Murithi',  'patrick.murithi@gmail.com','+254766006006', 2023, 7,  '272'),
        ('Queen',  'Apiyo',    'queen.apiyo@gmail.com',    '+254766006007', 2021, 37, '273'),
    ],
}


class Command(BaseCommand):
    help = 'Seed MMU database with faculties, programmes, departments, and test accounts'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding MMU data...')

        # ── Faculties ────────────────────────────────────────────────────────
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
            f, _ = Faculty.objects.get_or_create(faculty_code=code, defaults={'name':name,'dean_name':dean,'email':email})
            faculties[code] = f
        self.stdout.write(f'  ✓ {len(faculties)} faculties ready')

        # ── Programmes ───────────────────────────────────────────────────────
        programmes_data = [
            ('221','BSc Information Technology','Undergraduate','CIT'),
            ('222','BSc Computer Technology','Undergraduate','CIT'),
            ('223','BSc Software Engineering','Undergraduate','CIT'),
            ('224','BSc Computer Science','Undergraduate','CIT'),
            ('225','Diploma in ICT','Diploma','CIT'),
            ('226','MSc Information Technology','Postgraduate','CIT'),
            ('227','MSc Computer Science','Postgraduate','CIT'),
            ('231','Bachelor of Commerce','Undergraduate','BUS'),
            ('232','Bachelor of Business Information Technology','Undergraduate','BUS'),
            ('233','BSc Actuarial Science','Undergraduate','BUS'),
            ('234','BSc Economics','Undergraduate','BUS'),
            ('235','Bachelor of Procurement and Logistics Management','Undergraduate','BUS'),
            ('236','Diploma in Business Administration','Diploma','BUS'),
            ('237','MBA','Postgraduate','BUS'),
            ('238','MSc Economics','Postgraduate','BUS'),
            ('241','Bachelor of Science in Journalism','Undergraduate','MED'),
            ('242','Bachelor of Film and Theatre Arts','Undergraduate','MED'),
            ('243','Diploma in Media Studies','Diploma','MED'),
            ('251','BSc Electrical and Electronic Engineering','Undergraduate','ENG'),
            ('252','BSc Telecommunication Engineering','Undergraduate','ENG'),
            ('253','BSc Mechanical Engineering','Undergraduate','ENG'),
            ('254','Diploma in Engineering','Diploma','ENG'),
            ('261','Bachelor of Arts in Sociology','Undergraduate','SST'),
            ('262','Bachelor of Arts in Criminology','Undergraduate','SST'),
            ('263','BSc Peace and Conflict Studies','Undergraduate','SST'),
            ('271','BSc Mathematics','Undergraduate','SCI'),
            ('272','BSc Physics','Undergraduate','SCI'),
            ('273','BSc Chemistry','Undergraduate','SCI'),
            ('274','BSc Biochemistry','Undergraduate','SCI'),
        ]
        programmes = {}
        for code, name, level, fac_code in programmes_data:
            p, _ = Programme.objects.get_or_create(programme_code=code, defaults={'name':name,'level':level,'faculty':faculties[fac_code]})
            programmes[code] = p
        self.stdout.write(f'  ✓ {len(programmes)} programmes ready')

        # ── 6 Clearance Departments ──────────────────────────────────────────
        depts_data = [
            ('LIBRARY','Library','library@mmu.ac.ke'),
            ('FINANCE','Finance','finance@mmu.ac.ke'),
            ('HOSTELS','Hostels','hostels@mmu.ac.ke'),
            ('FACULTY','Faculty/School','faculty@mmu.ac.ke'),
            ('ICT','ICT Services','ict@mmu.ac.ke'),
            ('REGISTRY','Registry','registry@mmu.ac.ke'),
        ]
        depts = {}
        for code, name, email in depts_data:
            d, _ = ClearanceDept.objects.get_or_create(code=code, defaults={'name':name,'contact_email':email})
            depts[code] = d
        self.stdout.write(f'  ✓ 6 clearance departments ready')

        # ── Victor Kimutai (primary test student) ────────────────────────────
        if not Student.objects.filter(reg_number='CIT-222-044/2020').exists():
            s = Student(first_name='Victor',last_name='Kimutai',email='vkimu20@gmail.com',phone='+254712345678',admission_year=2020,cohort_number=44,programme=programmes['222'])
            s.set_password('student123'); s.save()
            LibraryRecord.objects.get_or_create(student=s,defaults={'books_borrowed':3,'books_returned':2,'fines_due':50.00})
            FinanceRecord.objects.get_or_create(student=s,defaults={'fees_balance':0.00,'other_dues':0.00})
            HostelRecord.objects.get_or_create(student=s,defaults={'room_number':'A104','block':'Block A','balance_due':0.00})
        else:
            # Update email if exists
            Student.objects.filter(reg_number='CIT-222-044/2020').update(email='vkimu20@gmail.com')
        self.stdout.write('  ✓ Primary test student: CIT-222-044/2020 / student123')

        # ── 7 Students per Faculty ───────────────────────────────────────────
        self.stdout.write('\n  📋 Student Registration Numbers:')
        self.stdout.write('  ' + '─'*52)
        created_count = 0
        for fac_code, students in STUDENTS_BY_FACULTY.items():
            self.stdout.write(f'\n  {fac_code} Faculty:')
            for fname, lname, email, phone, yr, cohort, prog_code in students:
                prog = programmes[prog_code]
                fac = faculties[fac_code]
                reg = f'{fac_code}-{prog_code}-{cohort:03d}/{yr}'
                if not Student.objects.filter(reg_number=reg).exists():
                    s = Student(first_name=fname,last_name=lname,email=email,phone=phone,admission_year=yr,cohort_number=cohort,programme=prog)
                    s.set_password('student123'); s.save()
                    LibraryRecord.objects.get_or_create(student=s,defaults={'books_borrowed':0,'books_returned':0,'fines_due':0.00})
                    FinanceRecord.objects.get_or_create(student=s,defaults={'fees_balance':0.00,'other_dues':0.00})
                    created_count += 1
                self.stdout.write(f'    {reg}  ({fname} {lname})')

        self.stdout.write(f'\n  ✓ {created_count} new students created (all password: student123)')

        # ── Staff ────────────────────────────────────────────────────────────
        staff_data = [
            ('LIB-001','Alice','Njoroge','alice.njoroge@mmu.ac.ke','officer','LIBRARY'),
            ('FIN-001','Bob','Otieno','bob.otieno@mmu.ac.ke','officer','FINANCE'),
            ('HOS-001','Carol','Wambui','carol.wambui@mmu.ac.ke','officer','HOSTELS'),
            ('FAC-001','Daniel','Mutua','daniel.mutua@mmu.ac.ke','officer','FACULTY'),
            ('ICT-001','Eve','Achieng','eve.achieng@mmu.ac.ke','officer','ICT'),
            ('REG-001','Frank','Kiplagat','frank.kiplagat@mmu.ac.ke','officer','REGISTRY'),
            ('ADM-001','Grace','Mwangi','grace.mwangi@mmu.ac.ke','admin','REGISTRY'),
        ]
        for sn, fn, ln, em, role, dept_code in staff_data:
            if not Staff.objects.filter(staff_number=sn).exists():
                st = Staff(staff_number=sn,first_name=fn,last_name=ln,email=em,role=role,department=depts[dept_code],is_active=True)
                st.set_password('admin123' if role=='admin' else 'staff123'); st.save()
        self.stdout.write('\n  ✓ 7 staff accounts ready')

        self.stdout.write(self.style.SUCCESS('\n✅ MMU seed data loaded successfully!\n'))
        self.stdout.write('  STUDENT (primary):  CIT-222-044/2020  / student123')
        self.stdout.write('  STAFF:    LIB-001, FIN-001, HOS-001, FAC-001, ICT-001, REG-001  / staff123')
        self.stdout.write('  ADMIN:    ADM-001  / admin123')
