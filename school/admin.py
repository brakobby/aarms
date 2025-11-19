from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'get_full_name', 'role', 'email', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'profile_picture')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'class_teacher', 'academic_year', 'capacity']
    list_filter = ['department', 'academic_year']
    search_fields = ['name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department']
    list_filter = ['department']
    search_fields = ['name', 'code']


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'course', 'class_assigned', 'academic_year']
    list_filter = ['academic_year', 'course']
    search_fields = ['teacher__username', 'teacher__first_name', 'teacher__last_name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'get_full_name', 'gender', 'current_class', 'is_active']
    list_filter = ['gender', 'is_active', 'current_class']
    search_fields = ['admission_number', 'first_name', 'last_name']
    date_hierarchy = 'enrollment_date'


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'start_date', 'end_date', 'is_active', 'is_locked']
    list_filter = ['is_active', 'is_locked', 'academic_year']


@admin.register(QuarterlyResult)
class QuarterlyResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'quarter', 'score', 'get_grade', 'status', 'teacher']
    list_filter = ['status', 'quarter', 'course']
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'quarter_1', 'quarter_2', 'is_locked']
    list_filter = ['is_locked', 'academic_year']


@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'semester', 'average_score', 'get_grade', 'is_approved']
    list_filter = ['is_approved', 'semester']
    search_fields = ['student__first_name', 'student__last_name']


@admin.register(ResultTemplate)
class ResultTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'template_type', 'is_active']
    list_filter = ['template_type', 'is_active', 'department']