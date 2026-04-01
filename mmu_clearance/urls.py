from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('clearance.urls')),

    # Frontend pages — all served as Django templates (shells for JS SPA)
    path('', TemplateView.as_view(template_name='student/login.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='student/login.html'), name='student_login'),
    path('dashboard/', TemplateView.as_view(template_name='student/dashboard.html'), name='student_dashboard'),
    path('certificate/', TemplateView.as_view(template_name='student/certificate.html'), name='certificate'),
    path('staff/login/', TemplateView.as_view(template_name='staff/login.html'), name='staff_login'),
    path('staff/dashboard/', TemplateView.as_view(template_name='staff/dashboard.html'), name='staff_dashboard'),
    path('staff/action/<int:request_id>/', TemplateView.as_view(template_name='staff/action.html'), name='staff_action'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
