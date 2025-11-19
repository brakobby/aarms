# school/urls.py
from django.urls import path
from . import views

app_name = 'school'   # THIS LINE WAS MISSING!

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
    
    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    
    # Classes
    path('classes/', views.class_list, name='class_list'),
    path('classes/create/', views.class_create, name='class_create'),
    
    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    
    # Results
    path('results/quarter-select/', views.quarter_select, name='quarter_select'),
    path('results/entry/<int:quarter_id>/<int:class_id>/<int:course_id>/', views.result_entry, name='result_entry'),
    path('results/submit/<int:quarter_id>/<int:class_id>/<int:course_id>/', views.submit_results, name='submit_results'),
    
    # Admin approval
    path('results/approval/', views.approval_list, name='approval_list'),
    path('results/approve/<int:pk>/', views.approve_result, name='approve_result'),
    path('results/reject/<int:pk>/', views.reject_result, name='reject_result'),
    
    # Printing
    path('print/quarterly/<int:quarter_id>/<int:student_id>/', views.print_quarterly, name='print_quarterly'),
    path('print/semester/<int:semester_id>/<int:student_id>/', views.print_semester, name='print_semester'),
]