import csv
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dashboard.models import ClinicianProfile, FrameComment, PatientAlert, PatientProfile, PressureFrame, PressureSession
from dashboard.utils import HIGH_PRESSURE_THRESHOLD, compute_frame_metrics

User = get_user_model()


class Command(BaseCommand):
    help = 'Import Graphene Trace pressure CSV files from a folder.'

    def add_arguments(self, parser):
        parser.add_argument('folder', type=str)
        parser.add_argument('--limit-frames', type=int, default=None, help='Optional max number of frames to import per file.')

    @transaction.atomic
    def handle(self, *args, **options):
        folder = Path(options['folder'])
        limit_frames = options.get('limit_frames')
        if not folder.exists():
            raise CommandError(f'Folder not found: {folder}')

        admin_user, _ = User.objects.get_or_create(username='admin', defaults={'role': User.Roles.ADMIN, 'is_staff': True, 'is_superuser': True})
        admin_user.set_password('admin123')
        admin_user.save()

        clinician_user, _ = User.objects.get_or_create(username='clinician1', defaults={'role': User.Roles.CLINICIAN, 'first_name': 'Case', 'last_name': 'Clinician'})
        clinician_user.set_password('clinician123')
        clinician_user.save()
        clinician, _ = ClinicianProfile.objects.get_or_create(user=clinician_user, defaults={'specialty': 'Pressure care'})

        csv_files = sorted(folder.glob('*.csv'))
        if not csv_files:
            raise CommandError('No CSV files found.')

        imported_sessions = 0
        imported_frames = 0
        for csv_file in csv_files:
            user_id, date_text = csv_file.stem.split('_')
            session_date = datetime.strptime(date_text, '%Y%m%d').date()
            username = f'patient_{user_id[:8]}'
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'role': User.Roles.PATIENT,
                    'first_name': 'Patient',
                    'last_name': user_id[:8],
                },
            )
            user.role = User.Roles.PATIENT
            user.set_password('patient123')
            user.save()
            patient, _ = PatientProfile.objects.get_or_create(
                user=user,
                defaults={'external_id': user_id, 'clinician': clinician, 'age': 0},
            )
            if patient.external_id != user_id:
                patient.external_id = user_id
            if patient.clinician_id is None:
                patient.clinician = clinician
            patient.save()

            session_start = datetime.combine(session_date, datetime.min.time()).replace(tzinfo=dt_timezone.utc)
            session, _ = PressureSession.objects.get_or_create(
                patient=patient,
                source_file=csv_file.name,
                defaults={'session_date': session_date, 'started_at': session_start},
            )
            if session.frames.exists():
                self.stdout.write(self.style.WARNING(f'Skipping existing session: {csv_file.name}'))
                continue

            with csv_file.open(newline='') as f:
                rows = [list(map(float, row)) for row in csv.reader(f) if row]

            frame_count = len(rows) // 32
            if limit_frames is not None:
                frame_count = min(frame_count, limit_frames)
            for frame_index in range(frame_count):
                matrix = rows[frame_index * 32:(frame_index + 1) * 32]
                recorded_at = session_start + timedelta(seconds=frame_index)
                metrics = compute_frame_metrics(matrix)
                frame = PressureFrame.objects.create(
                    session=session,
                    frame_index=frame_index,
                    recorded_at=recorded_at,
                    matrix_json=matrix,
                    **metrics,
                )
                imported_frames += 1
                if metrics['flagged_for_review']:
                    max_value = metrics['peak_pressure_index'] or metrics['max_pressure']
                    level = PatientAlert.Levels.CRITICAL if max_value >= HIGH_PRESSURE_THRESHOLD + 30 else PatientAlert.Levels.WARNING
                    PatientAlert.objects.create(
                        patient=patient,
                        frame=frame,
                        level=level,
                        message=f'High pressure region detected at frame {frame_index} on {session_date}.',
                    )
            session.frame_count = frame_count
            session.save(update_fields=['frame_count'])
            imported_sessions += 1
            self.stdout.write(self.style.SUCCESS(f'Imported {csv_file.name}: {frame_count} frames'))

        self.stdout.write(self.style.SUCCESS(f'Done. Imported {imported_sessions} sessions and {imported_frames} frames.'))
