from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class ClinicianProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clinician_profile')
    specialty = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    external_id = models.CharField(max_length=50, unique=True)
    clinician = models.ForeignKey(ClinicianProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')
    age = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class PressureSession(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='sessions')
    source_file = models.CharField(max_length=255)
    session_date = models.DateField()
    started_at = models.DateTimeField()
    frame_count = models.PositiveIntegerField(default=0)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']
        unique_together = ('patient', 'source_file')

    def __str__(self):
        return f'{self.patient.external_id} - {self.session_date}'


class PressureFrame(models.Model):
    session = models.ForeignKey(PressureSession, on_delete=models.CASCADE, related_name='frames')
    frame_index = models.PositiveIntegerField()
    recorded_at = models.DateTimeField(db_index=True)
    matrix_json = models.JSONField()
    peak_pressure_index = models.FloatField(default=0)
    contact_area_percent = models.FloatField(default=0)
    occupied_pixels = models.PositiveIntegerField(default=0)
    max_pressure = models.FloatField(default=0)
    high_pressure_regions = models.JSONField(default=list, blank=True)
    plain_english_summary = models.TextField(blank=True)
    flagged_for_review = models.BooleanField(default=False)

    class Meta:
        ordering = ['recorded_at']
        unique_together = ('session', 'frame_index')

    def __str__(self):
        return f'{self.session} frame {self.frame_index}'


class PatientAlert(models.Model):
    class Levels(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='alerts')
    frame = models.ForeignKey(PressureFrame, on_delete=models.CASCADE, related_name='alerts')
    level = models.CharField(max_length=20, choices=Levels.choices, default=Levels.WARNING)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class FrameComment(models.Model):
    frame = models.ForeignKey(PressureFrame, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='frame_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.frame}'
