import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import role_required
from .forms import FrameCommentForm
from .models import ClinicianProfile, FrameComment, PatientAlert, PatientProfile, PressureFrame, PressureSession

User = get_user_model()


def _period_hours(value):
    return {'1h': 1, '6h': 6, '24h': 24}.get(value)


from django.contrib.auth.decorators import login_required


@login_required
def role_redirect(request):
    if request.user.role == User.Roles.ADMIN:
        return redirect('dashboard:admin_dashboard')
    if request.user.role == User.Roles.CLINICIAN:
        return redirect('dashboard:clinician_dashboard')
    return redirect('dashboard:patient_dashboard')


@role_required(User.Roles.PATIENT)
def patient_dashboard(request):
    patient = get_object_or_404(PatientProfile, user=request.user)
    period = request.GET.get('period', '24h')
    selected_frame_id = request.GET.get('frame')
    frames = PressureFrame.objects.filter(session__patient=patient).select_related('session')

    hours = _period_hours(period)
    if hours:
        latest_ts = frames.order_by('-recorded_at').values_list('recorded_at', flat=True).first()
        if latest_ts:
            frames = frames.filter(recorded_at__gte=latest_ts - timedelta(hours=hours))

    latest_frame = frames.order_by('-recorded_at').first()
    if selected_frame_id:
        selected_frame = get_object_or_404(PressureFrame.objects.select_related('session'), id=selected_frame_id, session__patient=patient)
    else:
        selected_frame = latest_frame

    chart_frames = list(frames.order_by('recorded_at')[:300])
    alerts = PatientAlert.objects.filter(patient=patient).select_related('frame')[:10]
    top_comments = selected_frame.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author') if selected_frame else []

    context = {
        'patient': patient,
        'selected_frame': selected_frame,
        'latest_frame': latest_frame,
        'alerts': alerts,
        'period': period,
        'chart_labels': json.dumps([frame.recorded_at.strftime('%m-%d %H:%M:%S') for frame in chart_frames]),
        'ppi_data': json.dumps([frame.peak_pressure_index for frame in chart_frames]),
        'contact_area_data': json.dumps([frame.contact_area_percent for frame in chart_frames]),
        'frame_options': frames.order_by('-recorded_at')[:50],
        'comment_form': FrameCommentForm(),
        'top_comments': top_comments,
    }
    return render(request, 'dashboard/patient_dashboard.html', context)


@role_required(User.Roles.PATIENT)
def patient_frame_detail(request, frame_id):
    patient = get_object_or_404(PatientProfile, user=request.user)
    frame = get_object_or_404(PressureFrame, id=frame_id, session__patient=patient)
    return redirect(f"/dashboard/patient/?frame={frame.id}")


@role_required(User.Roles.PATIENT)
def add_frame_comment(request, frame_id):
    patient = get_object_or_404(PatientProfile, user=request.user)
    frame = get_object_or_404(PressureFrame, id=frame_id, session__patient=patient)
    form = FrameCommentForm(request.POST)
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.frame = frame
        comment.author = request.user
        comment.save()
        messages.success(request, 'Your note was added for this timestamp.')
    else:
        messages.error(request, 'Could not save your note.')
    return redirect(f"/dashboard/patient/?frame={frame.id}")


@role_required(User.Roles.CLINICIAN)
def clinician_dashboard(request):
    clinician = get_object_or_404(ClinicianProfile, user=request.user)
    patients = clinician.patients.select_related('user').annotate(session_count=Count('sessions')).order_by('user__username')
    alerts = PatientAlert.objects.filter(patient__clinician=clinician).select_related('patient__user', 'frame').order_by('-created_at')[:20]
    recent_comments = FrameComment.objects.filter(frame__session__patient__clinician=clinician, parent__isnull=True).select_related('author', 'frame__session__patient__user').order_by('-created_at')[:20]
    context = {
        'clinician': clinician,
        'patients': patients,
        'alerts': alerts,
        'recent_comments': recent_comments,
    }
    return render(request, 'dashboard/clinician_dashboard.html', context)


@role_required(User.Roles.CLINICIAN)
def clinician_patient_detail(request, patient_id):
    clinician = get_object_or_404(ClinicianProfile, user=request.user)
    patient = get_object_or_404(PatientProfile.objects.select_related('user'), id=patient_id, clinician=clinician)
    frames = PressureFrame.objects.filter(session__patient=patient).select_related('session').order_by('-recorded_at')
    selected_frame = frames.first()
    comments = selected_frame.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author') if selected_frame else []
    context = {
        'clinician': clinician,
        'patient': patient,
        'selected_frame': selected_frame,
        'frame_options': frames[:50],
        'comments': comments,
        'reply_form': FrameCommentForm(),
    }
    return render(request, 'dashboard/clinician_patient_detail.html', context)


@role_required(User.Roles.CLINICIAN)
def reply_to_comment(request, comment_id):
    clinician = get_object_or_404(ClinicianProfile, user=request.user)
    parent = get_object_or_404(FrameComment, id=comment_id, frame__session__patient__clinician=clinician)
    form = FrameCommentForm(request.POST)
    if request.method == 'POST' and form.is_valid():
        reply = form.save(commit=False)
        reply.frame = parent.frame
        reply.author = request.user
        reply.parent = parent
        reply.save()
        messages.success(request, 'Reply added.')
    return redirect('dashboard:clinician_patient_detail', patient_id=parent.frame.session.patient.id)


@role_required(User.Roles.ADMIN)
def admin_dashboard(request):
    context = {
        'user_count': User.objects.count(),
        'patient_count': PatientProfile.objects.count(),
        'clinician_count': ClinicianProfile.objects.count(),
        'session_count': PressureSession.objects.count(),
        'frame_count': PressureFrame.objects.count(),
        'alert_count': PatientAlert.objects.count(),
        'latest_sessions': PressureSession.objects.select_related('patient__user')[:10],
    }
    return render(request, 'dashboard/admin_dashboard.html', context)
