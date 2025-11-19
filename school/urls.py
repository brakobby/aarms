# school/urls.py
from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/bulk-actions/', views.student_bulk_actions, name='student_bulk_actions'),
    
    # Teachers
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    
    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Classes
    path('classes/', views.class_list, name='class_list'),
    path('classes/create/', views.class_create, name='class_create'),
    path('classes/<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:pk>/delete/', views.class_delete, name='class_delete'),
    path('classes/<int:class_id>/performance/', views.class_performance_report, name='class_performance'),
    
    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Academic Years
    path('academic-years/', views.academic_year_list, name='academic_year_list'),
    path('academic-years/create/', views.academic_year_create, name='academic_year_create'),
    path('academic-years/<int:pk>/edit/', views.academic_year_edit, name='academic_year_edit'),
    path('academic-years/<int:pk>/delete/', views.academic_year_delete, name='academic_year_delete'),
    path('academic-years/<int:pk>/toggle/', views.academic_year_toggle_active, name='academic_year_toggle'),
    
    # Quarters
    path('quarters/', views.quarter_list, name='quarter_list'),
    path('quarters/create/', views.quarter_create, name='quarter_create'),
    path('quarters/<int:pk>/edit/', views.quarter_edit, name='quarter_edit'),
    path('quarters/<int:pk>/delete/', views.quarter_delete, name='quarter_delete'),
    path('quarters/<int:pk>/toggle/', views.quarter_toggle_active, name='quarter_toggle'),
    path('quarters/<int:pk>/lock/', views.quarter_lock, name='quarter_lock'),
    
    # Teacher Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    
    # Semesters
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/create/', views.semester_create, name='semester_create'),
    path('semesters/<int:pk>/edit/', views.semester_edit, name='semester_edit'),
    path('semesters/<int:pk>/delete/', views.semester_delete, name='semester_delete'),
    path('semesters/<int:semester_id>/calculate/', views.semester_calculate, name='semester_calculate'),
    path('semesters/<int:pk>/lock/', views.semester_lock, name='semester_lock'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:pk>/preview/', views.template_preview, name='template_preview'),
    
    # Results
    path('results/quarter-select/', views.quarter_select, name='quarter_select'),
    path('results/entry/<int:quarter_id>/<int:class_id>/<int:course_id>/', views.result_entry, name='result_entry'),
    path('results/submit/<int:quarter_id>/<int:class_id>/<int:course_id>/', views.submit_results, name='submit_results'),
    
    # Admin approval
    path('results/approval/', views.approval_list, name='approval_list'),
    path('results/approve/<int:pk>/', views.approve_result, name='approve_result'),
    path('results/reject/<int:pk>/', views.reject_result, name='reject_result'),
    path('results/bulk-approve/', views.bulk_approve_results, name='bulk_approve'),
    
    # Reports
    path('reports/top-performers/', views.top_performers, name='top_performers'),
    
    # Printing
    path('print/quarterly/<int:quarter_id>/<int:student_id>/', views.print_quarterly, name='print_quarterly'),
    path('print/semester/<int:semester_id>/<int:student_id>/', views.print_semester, name='print_semester'),
]