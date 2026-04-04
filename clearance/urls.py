from django.urls import path
from .views import (
    StudentForgotPasswordView, StaffForgotPasswordView,
    StudentClearanceResubmitView,
    StudentLoginView, StaffLoginView, LogoutView,
    StudentProfileView, StudentClearanceStatusView,
    StudentClearanceSubmitView, StudentCertificateView,
    StudentNotificationsView,
    StaffQueueView, StaffQueueDetailView, StaffActionView, StaffHistoryView,
    AdminRequestsView, AdminRequestDetailView,
    AdminStaffView, AdminStaffDetailView, AdminReportsSummaryView,
)

urlpatterns = [
    # Auth
    path('auth/student/login/', StudentLoginView.as_view(), name='student-login'),
    path('auth/staff/login/', StaffLoginView.as_view(), name='staff-login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Student
    path('student/profile/', StudentProfileView.as_view(), name='student-profile'),
    path('student/clearance/status/', StudentClearanceStatusView.as_view(), name='clearance-status'),
    path('student/clearance/submit/', StudentClearanceSubmitView.as_view(), name='clearance-submit'),
    path('student/clearance/resubmit/', StudentClearanceResubmitView.as_view(), name='clearance-resubmit'),
    path('student/clearance/certificate/', StudentCertificateView.as_view(), name='clearance-certificate'),
    path('student/notifications/', StudentNotificationsView.as_view(), name='student-notifications'),

    # Staff
    path('staff/queue/', StaffQueueView.as_view(), name='staff-queue'),
    path('staff/queue/<int:request_id>/', StaffQueueDetailView.as_view(), name='staff-queue-detail'),
    path('staff/queue/<int:request_id>/action/', StaffActionView.as_view(), name='staff-action'),
    path('staff/history/', StaffHistoryView.as_view(), name='staff-history'),

    # Forgot password
    path('auth/student/forgot-password/', StudentForgotPasswordView.as_view(), name='student-forgot-password'),
    path('auth/staff/forgot-password/', StaffForgotPasswordView.as_view(), name='staff-forgot-password'),

    # Admin
    path('admin/requests/', AdminRequestsView.as_view(), name='admin-requests'),
    path('admin/requests/<int:pk>/', AdminRequestDetailView.as_view(), name='admin-request-detail'),
    path('admin/staff/', AdminStaffView.as_view(), name='admin-staff'),
    path('admin/staff/<int:pk>/', AdminStaffDetailView.as_view(), name='admin-staff-detail'),
    path('admin/reports/summary/', AdminReportsSummaryView.as_view(), name='admin-reports'),
]
