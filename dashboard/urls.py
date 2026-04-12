from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.role_redirect, name='role_redirect'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/frame/<int:frame_id>/', views.patient_frame_detail, name='patient_frame_detail'),
    path('patient/frame/<int:frame_id>/comment/', views.add_frame_comment, name='add_frame_comment'),
    path('clinician/', views.clinician_dashboard, name='clinician_dashboard'),
    path('clinician/patient/<int:patient_id>/', views.clinician_patient_detail, name='clinician_patient_detail'),
    path('clinician/comment/<int:comment_id>/reply/', views.reply_to_comment, name='reply_to_comment'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]
