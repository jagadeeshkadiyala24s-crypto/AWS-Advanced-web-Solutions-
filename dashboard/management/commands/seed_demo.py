from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from dashboard.models import ClinicianProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo admin and clinician accounts."

    def handle(self, *args, **options):
        admin_user, _ = User.objects.get_or_create(username='admin', defaults={'role': User.Roles.ADMIN, 'is_staff': True, 'is_superuser': True})
        admin_user.role = User.Roles.ADMIN
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password('admin123')
        admin_user.save()

        clinician_user, _ = User.objects.get_or_create(username='clinician1', defaults={'role': User.Roles.CLINICIAN, 'first_name': 'Case', 'last_name': 'Clinician'})
        clinician_user.role = User.Roles.CLINICIAN
        clinician_user.set_password('clinician123')
        clinician_user.save()
        ClinicianProfile.objects.get_or_create(user=clinician_user, defaults={'specialty': 'Pressure care'})
        self.stdout.write(self.style.SUCCESS('Demo users created.'))
