from django.core.management.base import BaseCommand
from django.db import transaction
from clearance.models import Student, Programme, FinanceRecord, LibraryRecord

class Command(BaseCommand):
    help = 'Add Irene Muchiri'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            prog = Programme.objects.get(programme_code='233')
        except Programme.DoesNotExist:
            self.stdout.write(self.style.ERROR('Programme 233 not found. Run seed_mmu_data first.'))
            return

        if Student.objects.filter(reg_number='BUS-233-009/2022').exists():
            self.stdout.write('Irene Muchiri already exists.')
            return

        s = Student(
            first_name='Irene',
            last_name='Muchiri',
            email='irene.muchiri@gmail.com',
            phone='+254700000009',
            admission_year=2022,
            cohort_number=9,
            programme=prog,
        )
        s.set_password('student123')
        s.save()
        LibraryRecord.objects.create(student=s, books_borrowed=0, books_returned=0, fines_due=0)
        FinanceRecord.objects.create(student=s, fees_balance=0, other_dues=0)

        self.stdout.write(self.style.SUCCESS(
            f'✅ Added: {s.reg_number} — Irene Muchiri (BSc Actuarial Science, BUS)\n   Password: student123'
        ))
