from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Faculty, Programme, Student, ClearanceDept, Staff,
    ClearanceRequest, DeptClearanceStatus, LibraryRecord,
    FinanceRecord, HostelRecord, Notification
)

admin.site.site_header = "MMU Clearance System — Admin"
admin.site.site_title = "MMU Clearance Admin"
admin.site.index_title = "Clearance Management"


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['faculty_code', 'name', 'dean_name', 'email']
    search_fields = ['faculty_code', 'name']


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['programme_code', 'name', 'level', 'faculty']
    list_filter = ['level', 'faculty']
    search_fields = ['programme_code', 'name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['reg_number', 'first_name', 'last_name', 'email', 'programme', 'admission_year']
    list_filter = ['programme__faculty', 'admission_year']
    search_fields = ['reg_number', 'first_name', 'last_name', 'email']
    readonly_fields = ['reg_number']

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


@admin.register(ClearanceDept)
class ClearanceDeptAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'contact_email']

    def has_delete_permission(self, request, obj=None):
        # The 6 fixed departments must never be deleted
        return False


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['staff_number', 'first_name', 'last_name', 'email', 'role', 'department', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['staff_number', 'first_name', 'last_name', 'email']

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


class DeptClearanceStatusInline(admin.TabularInline):
    model = DeptClearanceStatus
    extra = 0
    readonly_fields = ['department', 'status', 'cleared_by', 'remarks', 'updated_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ClearanceRequest)
class ClearanceRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'academic_year', 'overall_status', 'initiated_date', 'completed_date']
    list_filter = ['overall_status', 'academic_year']
    search_fields = ['student__reg_number', 'student__first_name', 'student__last_name']
    readonly_fields = ['initiated_date', 'completed_date']
    inlines = [DeptClearanceStatusInline]

    def colored_status(self, obj):
        colors = {
            'PENDING': 'orange',
            'IN_PROGRESS': 'blue',
            'COMPLETED': 'green',
            'REJECTED': 'red',
        }
        color = colors.get(obj.overall_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.overall_status
        )
    colored_status.short_description = 'Status'


@admin.register(DeptClearanceStatus)
class DeptClearanceStatusAdmin(admin.ModelAdmin):
    list_display = ['request', 'department', 'status', 'cleared_by', 'updated_at']
    list_filter = ['status', 'department']
    search_fields = ['request__student__reg_number']
    readonly_fields = ['updated_at']


@admin.register(LibraryRecord)
class LibraryRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'books_borrowed', 'books_returned', 'fines_due']
    search_fields = ['student__reg_number', 'student__first_name']


@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'fees_balance', 'other_dues']
    search_fields = ['student__reg_number', 'student__first_name']


@admin.register(HostelRecord)
class HostelRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'room_number', 'block', 'balance_due']
    search_fields = ['student__reg_number']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'type', 'status', 'sent_at']
    list_filter = ['type', 'status']
    search_fields = ['student__reg_number']
    readonly_fields = ['sent_at']
