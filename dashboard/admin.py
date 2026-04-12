from django.contrib import admin
from .models import ClinicianProfile, PatientProfile, PressureSession, PressureFrame, PatientAlert, FrameComment

admin.site.register(ClinicianProfile)
admin.site.register(PatientProfile)
admin.site.register(PressureSession)
admin.site.register(PressureFrame)
admin.site.register(PatientAlert)
admin.site.register(FrameComment)
