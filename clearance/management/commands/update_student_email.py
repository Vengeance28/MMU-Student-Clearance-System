from django.core.management.base import BaseCommand
from clearance.models import Student

class Command(BaseCommand):
    help = 'Update test student email to real email'

    def handle(self, *args, **options):
        try:
            student = Student.objects.get(reg_number='CIT-222-044/2020')
            student.email = 'vkimu20@gmail.com'
            student.save(update_fields=['email'])
            self.stdout.write(self.style.SUCCESS('✅ Student email updated to vkimu20@gmail.com'))
        except Student.DoesNotExist:
            self.stdout.write(self.style.ERROR('Student not found — run seed_mmu_data first'))
