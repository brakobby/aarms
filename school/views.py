from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import *
from .forms import *


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('school:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('school:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'school/login.html')


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('school:login')  # ← FIXED: namespaced


# ============================================
# DASHBOARD
# ============================================

@login_required
def dashboard_view(request):
    """Main dashboard - routes based on user role"""
    context = {
        'today': timezone.now().date(),
        'now': timezone.now(),
    }
    
    if request.user.role == 'admin':
        # Main Statistics
        context['total_students'] = Student.objects.filter(is_active=True).count()
        context['total_teachers'] = User.objects.filter(
            role__in=['teacher', 'class_teacher']
        ).count()
        context['total_classes'] = Class.objects.count()
        context['pending_results'] = QuarterlyResult.objects.filter(
            status='submitted'
        ).count()
        
        # Additional Stats
        context['total_departments'] = Department.objects.count()
        context['total_courses'] = Course.objects.count()
        context['active_quarters'] = Quarter.objects.filter(is_active=True).count()
        context['total_results'] = QuarterlyResult.objects.filter(
            status='approved'
        ).count()
        
        # Recent Activities (sample data - customize as needed)
        context['recent_activities'] = [
            {
                'title': 'New Student Registered',
                'description': 'John Doe added to Grade 1A',
                'timestamp': timezone.now() - timezone.timedelta(hours=2),
                'icon': 'fa-user-plus',
                'color': '#10b981'
            },
            {
                'title': 'Results Submitted',
                'description': 'Teacher Smith submitted Math Q1 results',
                'timestamp': timezone.now() - timezone.timedelta(hours=5),
                'icon': 'fa-file-upload',
                'color': '#3b82f6'
            },
            {
                'title': 'Results Approved',
                'description': '25 quarterly results approved',
                'timestamp': timezone.now() - timezone.timedelta(days=1),
                'icon': 'fa-check-circle',
                'color': '#10b981'
            },
            {
                'title': 'New Class Created',
                'description': 'Grade 2B created in Primary Department',
                'timestamp': timezone.now() - timezone.timedelta(days=2),
                'icon': 'fa-plus-circle',
                'color': '#8b5cf6'
            },
        ]
        
        return render(request, 'school/admin_dashboard.html', context)
    
    elif request.user.is_teacher():
        # Teacher dashboard
        context['my_classes'] = TeacherAssignment.objects.filter(
            teacher=request.user
        ).select_related('class_assigned', 'course')
        
        context['submitted_results'] = QuarterlyResult.objects.filter(
            teacher=request.user,
            status='submitted'
        ).count()
        
        context['draft_results'] = QuarterlyResult.objects.filter(
            teacher=request.user,
            status='draft'
        ).count()
        
        context['approved_results'] = QuarterlyResult.objects.filter(
            teacher=request.user,
            status='approved'
        ).count()
        
        return render(request, 'school/teacher_dashboard.html', context)
    
    else:
        # Principal or other roles
        return render(request, 'school/dashboard.html', context)

# ============================================
# STUDENT VIEWS
# ============================================

@login_required
def student_list(request):
    students = Student.objects.filter(is_active=True).select_related('current_class__department')

    search = request.GET.get('search')
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(admission_number__icontains=search)
        )

    return render(request, 'school/student_list.html', {'students': students})


@login_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully!')
            return redirect('school:student_list')
    else:
        form = StudentForm()

    return render(request, 'school/student_form.html', {'form': form})


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('school:student_list')
    else:
        form = StudentForm(instance=student)

    return render(request, 'school/student_form.html', {'form': form, 'student': student})


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    results = QuarterlyResult.objects.filter(student=student).select_related('course', 'quarter__academic_year')
    return render(request, 'school/student_detail.html', {'student': student, 'results': results})


# ============================================
# RESULT ENTRY VIEWS
# ============================================

@login_required
def quarter_select(request):
    quarters = Quarter.objects.filter(is_active=True)

    if request.user.is_teacher():
        assignments = TeacherAssignment.objects.filter(
            teacher=request.user,
            academic_year__is_active=True
        ).select_related('class_assigned', 'course')
    else:
        assignments = TeacherAssignment.objects.select_related('class_assigned', 'course')

    return render(request, 'school/quarter_select.html', {
        'quarters': quarters,
        'assignments': assignments
    })


@login_required
def result_entry(request, quarter_id, class_id, course_id):
    quarter = get_object_or_404(Quarter, pk=quarter_id)
    class_obj = get_object_or_404(Class, pk=class_id)
    course = get_object_or_404(Course, pk=course_id)

    # Permission check for teachers
    if request.user.is_teacher():
        if not TeacherAssignment.objects.filter(
            teacher=request.user,
            class_assigned=class_obj,
            course=course
        ).exists():
            messages.error(request, 'You are not assigned to teach this course in this class.')
            return redirect('school:quarter_select')

    students = Student.objects.filter(current_class=class_obj, is_active=True).order_by('last_name', 'first_name')

    if request.method == 'POST':
        for student in students:
            score_key = f'score_{student.id}'
            comment_key = f'comment_{student.id}'
            score = request.POST.get(score_key)

            if score not in ['', None]:
                QuarterlyResult.objects.update_or_create(
                    student=student,
                    course=course,
                    quarter=quarter,
                    defaults={
                        'teacher': request.user,
                        'score': score,
                        'teacher_comment': request.POST.get(comment_key, ''),
                        'status': 'draft'
                    }
                )
        messages.success(request, 'Results saved as draft.')
        return redirect('school:quarter_select')

    # Load existing results
    existing = QuarterlyResult.objects.filter(
        quarter=quarter, course=course, student__in=students
    ).select_related('student')
    result_dict = {r.student_id: r for r in existing}

    return render(request, 'school/result_entry.html', {
        'quarter': quarter,
        'class_obj': class_obj,
        'course': course,
        'students': students,
        'result_dict': result_dict,
    })


@login_required
def submit_results(request, quarter_id, class_id, course_id):
    if request.method != 'POST':
        return redirect('school:quarter_select')

    updated = QuarterlyResult.objects.filter(
        quarter_id=quarter_id,
        course_id=course_id,
        student__current_class_id=class_id,
        teacher=request.user,
        status='draft'
    ).update(status='submitted', submitted_at=timezone.now())

    if updated:
        messages.success(request, f'{updated} results submitted for approval!')
    else:
        messages.info(request, 'No draft results found to submit.')

    return redirect('school:quarter_select')


# ============================================
# ADMIN - RESULT APPROVAL
# ============================================

@login_required
def approval_list(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')

    pending = QuarterlyResult.objects.filter(status='submitted') \
        .select_related('student', 'course', 'quarter__academic_year', 'teacher') \
        .order_by('-submitted_at')

    return render(request, 'school/approval_list.html', {'pending_results': pending})


@login_required
def approve_result(request, pk):
    if request.user.role != 'admin':
        return redirect('school:dashboard')

    result = get_object_or_404(QuarterlyResult, pk=pk, status='submitted')
    result.status = 'approved'
    result.approved_by = request.user
    result.approved_at = timezone.now()
    result.save()
    messages.success(request, 'Result approved successfully.')
    return redirect('school:approval_list')


@login_required
def reject_result(request, pk):
    if request.user.role != 'admin':
        return redirect('school:dashboard')

    result = get_object_or_404(QuarterlyResult, pk=pk, status='submitted')
    result.status = 'rejected'
    result.save()
    messages.warning(request, 'Result has been rejected.')
    return redirect('school:approval_list')


# ============================================
# MANAGEMENT VIEWS (Class, Course, Department)
# ============================================

@login_required
def class_list(request):
    classes = Class.objects.select_related('department', 'class_teacher', 'academic_year')
    return render(request, 'school/class_list.html', {'classes': classes})


@login_required
def class_create(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class created!')
            return redirect('school:class_list')
    else:
        form = ClassForm()
    return render(request, 'school/class_form.html', {'form': form})


@login_required
def course_list(request):
    courses = Course.objects.select_related('department')
    return render(request, 'school/course_list.html', {'courses': courses})


@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course added!')
            return redirect('school:course_list')
    else:
        form = CourseForm()
    return render(request, 'school/course_form.html', {'form': form})


@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'school/department_list.html', {'departments': departments})


@login_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created!')
            return redirect('school:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'school/department_form.html', {'form': form})


# ============================================
# PRINT VIEWS
# ============================================

@login_required
def print_quarterly(request, quarter_id, student_id):
    quarter = get_object_or_404(Quarter, pk=quarter_id)
    student = get_object_or_404(Student, pk=student_id)
    results = QuarterlyResult.objects.filter(
        student=student, quarter=quarter, status='approved'
    ).select_related('course')

    return render(request, 'school/print_quarterly.html', {
        'quarter': quarter, 'student': student, 'results': results
    })


@login_required
def print_semester(request, semester_id, student_id):
    semester = get_object_or_404(Semester, pk=semester_id)
    student = get_object_or_404(Student, pk=student_id)
    results = SemesterResult.objects.filter(student=student, semester=semester).select_related('course')

    return render(request, 'school/print_semester.html', {
        'semester': semester, 'student': student, 'results': results
    })

# Add these views to school/views.py

# ============================================
# TEACHER MANAGEMENT VIEWS
# ============================================

@login_required
def teacher_list(request):
    """List all teachers (Admin only)"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    teachers = User.objects.filter(
        role__in=['teacher', 'class_teacher']
    ).order_by('last_name', 'first_name')
    
    context = {'teachers': teachers}
    return render(request, 'school/teacher_list.html', context)


@login_required
def teacher_create(request):
    """Create new teacher account (Admin only)"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        role = request.POST.get('role')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role=role
        )
        
        messages.success(request, f'Teacher account created successfully for {user.get_full_name()}!')
        return redirect('school:teacher_list')
    
    return render(request, 'school/teacher_form.html')


# ============================================
# ACADEMIC YEAR & QUARTER MANAGEMENT
# ============================================

@login_required
def academic_year_list(request):
    """List all academic years"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    years = AcademicYear.objects.all().order_by('-start_date')
    context = {'academic_years': years}
    return render(request, 'school/academic_year_list.html', context)


@login_required
def academic_year_create(request):
    """Create academic year"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic year created successfully!')
            return redirect('school:academic_year_list')
    else:
        form = AcademicYearForm()
    
    context = {'form': form}
    return render(request, 'school/academic_year_form.html', context)


@login_required
def quarter_list(request):
    """List all quarters"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarters = Quarter.objects.all().select_related('academic_year')
    context = {'quarters': quarters}
    return render(request, 'school/quarter_list.html', context)


@login_required
def quarter_create(request):
    """Create quarter"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = QuarterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quarter created successfully!')
            return redirect('school:quarter_list')
    else:
        form = QuarterForm()
    
    context = {'form': form}
    return render(request, 'school/quarter_form.html', context)


@login_required
def quarter_toggle_active(request, pk):
    """Toggle quarter active status"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarter = get_object_or_404(Quarter, pk=pk)
    quarter.is_active = not quarter.is_active
    quarter.save()
    
    status = "activated" if quarter.is_active else "deactivated"
    messages.success(request, f'Quarter {quarter.get_name_display()} {status}!')
    return redirect('school:quarter_list')


@login_required
def quarter_lock(request, pk):
    """Lock/unlock quarter"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarter = get_object_or_404(Quarter, pk=pk)
    quarter.is_locked = not quarter.is_locked
    quarter.save()
    
    status = "locked" if quarter.is_locked else "unlocked"
    messages.success(request, f'Quarter {quarter.get_name_display()} {status}!')
    return redirect('school:quarter_list')


# ============================================
# TEACHER ASSIGNMENT VIEWS
# ============================================

@login_required
def assignment_list(request):
    """List all teacher assignments"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    assignments = TeacherAssignment.objects.all().select_related(
        'teacher', 'course', 'class_assigned', 'academic_year'
    )
    
    context = {'assignments': assignments}
    return render(request, 'school/assignment_list.html', context)


@login_required
def assignment_create(request):
    """Create teacher assignment"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = TeacherAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher assigned successfully!')
            return redirect('school:assignment_list')
    else:
        form = TeacherAssignmentForm()
    
    context = {'form': form}
    return render(request, 'school/assignment_form.html', context)


@login_required
def assignment_delete(request, pk):
    """Delete teacher assignment"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    assignment = get_object_or_404(TeacherAssignment, pk=pk)
    assignment.delete()
    messages.success(request, 'Assignment removed successfully!')
    return redirect('school:assignment_list')


# ============================================
# SEMESTER MANAGEMENT
# ============================================

@login_required
def semester_list(request):
    """List all semesters"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    semesters = Semester.objects.all().select_related(
        'academic_year', 'quarter_1', 'quarter_2'
    )
    
    context = {'semesters': semesters}
    return render(request, 'school/semester_list.html', context)


@login_required
def semester_calculate(request, semester_id):
    """Calculate semester results from quarters"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    semester = get_object_or_404(Semester, pk=semester_id)
    
    # Get all quarterly results for both quarters
    q1_results = QuarterlyResult.objects.filter(
        quarter=semester.quarter_1,
        status='approved'
    ).select_related('student', 'course')
    
    q2_results = QuarterlyResult.objects.filter(
        quarter=semester.quarter_2,
        status='approved'
    ).select_related('student', 'course')
    
    # Create dict for easy lookup
    q2_dict = {(r.student_id, r.course_id): r for r in q2_results}
    
    calculated = 0
    
    for q1_result in q1_results:
        # Find matching Q2 result
        key = (q1_result.student_id, q1_result.course_id)
        if key in q2_dict:
            q2_result = q2_dict[key]
            
            # Create or update semester result
            sem_result, created = SemesterResult.objects.get_or_create(
                student=q1_result.student,
                course=q1_result.course,
                semester=semester,
                defaults={
                    'q1_score': q1_result.score,
                    'q2_score': q2_result.score,
                    'total_score': q1_result.score + q2_result.score,
                    'average_score': (q1_result.score + q2_result.score) / 2,
                }
            )
            
            if not created:
                # Update existing
                sem_result.q1_score = q1_result.score
                sem_result.q2_score = q2_result.score
                sem_result.calculate()
            
            calculated += 1
    
    messages.success(request, f'Calculated {calculated} semester results!')
    return redirect('school:semester_list')


# ============================================
# BULK OPERATIONS
# ============================================

@login_required
def bulk_approve_results(request):
    """Bulk approve all pending results"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        updated = QuarterlyResult.objects.filter(
            status='submitted'
        ).update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        
        messages.success(request, f'Approved {updated} results!')
        return redirect('school:approval_list')
    
    return redirect('school:approval_list')


# ============================================
# REPORTS & ANALYTICS
# ============================================

@login_required
def class_performance_report(request, class_id):
    """View class performance analytics"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    class_obj = get_object_or_404(Class, pk=class_id)
    students = Student.objects.filter(current_class=class_obj, is_active=True)
    
    # Get latest quarter results
    latest_quarter = Quarter.objects.filter(is_active=True).first()
    
    if latest_quarter:
        results = QuarterlyResult.objects.filter(
            student__in=students,
            quarter=latest_quarter,
            status='approved'
        ).select_related('student', 'course')
        
        # Calculate class average
        from django.db.models import Avg
        class_avg = results.aggregate(Avg('score'))['score__avg']
        
        context = {
            'class_obj': class_obj,
            'students': students,
            'results': results,
            'class_average': class_avg,
            'quarter': latest_quarter
        }
        
        return render(request, 'school/class_performance.html', context)
    
    messages.warning(request, 'No active quarter found.')
    return redirect('school:class_list')


@login_required
def top_performers(request):
    """View top performing students"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    # Get latest quarter
    latest_quarter = Quarter.objects.filter(is_active=True).first()
    
    if latest_quarter:
        # Get top performers
        from django.db.models import Avg
        top_students = Student.objects.filter(
            results__quarter=latest_quarter,
            results__status='approved',
            is_active=True
        ).annotate(
            avg_score=Avg('results__score')
        ).order_by('-avg_score')[:20]
        
        context = {
            'top_students': top_students,
            'quarter': latest_quarter
        }
        
        return render(request, 'school/top_performers.html', context)
    
    messages.warning(request, 'No active quarter found.')
    return redirect('school:dashboard')

@login_required
def teacher_list(request):
    """List all teachers (Admin only)"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    teachers = User.objects.filter(
        role__in=['teacher', 'class_teacher']
    ).order_by('last_name', 'first_name')
    
    context = {'teachers': teachers}
    return render(request, 'school/teacher_list.html', context)

@login_required
def teacher_create(request):
    """Create new teacher account (Admin only)"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'Teacher account created successfully for {user.get_full_name()}!')
            return redirect('school:teacher_list')
    else:
        form = TeacherForm()
    
    return render(request, 'school/teacher_form.html', {'form': form})

@login_required
def teacher_edit(request, pk):
    """Edit teacher account"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    teacher = get_object_or_404(User, pk=pk, role__in=['teacher', 'class_teacher'])
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('school:teacher_list')
    else:
        form = TeacherForm(instance=teacher)
    
    return render(request, 'school/teacher_form.html', {'form': form, 'teacher': teacher})

@login_required
def teacher_delete(request, pk):
    """Delete teacher account"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    teacher = get_object_or_404(User, pk=pk, role__in=['teacher', 'class_teacher'])
    
    if request.method == 'POST':
        teacher.delete()
        messages.success(request, 'Teacher account deleted successfully!')
        return redirect('school:teacher_list')
    
    return render(request, 'school/teacher_confirm_delete.html', {'teacher': teacher})

# ============================================
# ACADEMIC YEAR MANAGEMENT
# ============================================

@login_required
def academic_year_list(request):
    """List all academic years"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    years = AcademicYear.objects.all().order_by('-start_date')
    context = {'academic_years': years}
    return render(request, 'school/academic_year_list.html', context)

@login_required
def academic_year_create(request):
    """Create academic year"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic year created successfully!')
            return redirect('school:academic_year_list')
    else:
        form = AcademicYearForm()
    
    context = {'form': form}
    return render(request, 'school/academic_year_form.html', context)

@login_required
def academic_year_edit(request, pk):
    """Edit academic year"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    
    if request.method == 'POST':
        form = AcademicYearForm(request.POST, instance=academic_year)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic year updated successfully!')
            return redirect('school:academic_year_list')
    else:
        form = AcademicYearForm(instance=academic_year)
    
    return render(request, 'school/academic_year_form.html', {'form': form})

@login_required
def academic_year_delete(request, pk):
    """Delete academic year"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    
    if request.method == 'POST':
        academic_year.delete()
        messages.success(request, 'Academic year deleted successfully!')
        return redirect('school:academic_year_list')
    
    return render(request, 'school/academic_year_confirm_delete.html', {'academic_year': academic_year})

@login_required
def academic_year_toggle_active(request, pk):
    """Toggle academic year active status"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    
    # Deactivate all other years if activating this one
    if not academic_year.is_active:
        AcademicYear.objects.filter(is_active=True).update(is_active=False)
    
    academic_year.is_active = not academic_year.is_active
    academic_year.save()
    
    status = "activated" if academic_year.is_active else "deactivated"
    messages.success(request, f'Academic year {academic_year.name} {status}!')
    return redirect('school:academic_year_list')

# ============================================
# DEPARTMENT MANAGEMENT
# ============================================

@login_required
def department_edit(request, pk):
    """Edit department"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully!')
            return redirect('school:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'school/department_form.html', {'form': form})

@login_required
def department_delete(request, pk):
    """Delete department"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully!')
        return redirect('school:department_list')
    
    return render(request, 'school/department_confirm_delete.html', {'department': department})

# ============================================
# CLASS MANAGEMENT
# ============================================

@login_required
def class_edit(request, pk):
    """Edit class"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class updated successfully!')
            return redirect('school:class_list')
    else:
        form = ClassForm(instance=class_obj)
    
    return render(request, 'school/class_form.html', {'form': form})

@login_required
def class_delete(request, pk):
    """Delete class"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        class_obj.delete()
        messages.success(request, 'Class deleted successfully!')
        return redirect('school:class_list')
    
    return render(request, 'school/class_confirm_delete.html', {'class_obj': class_obj})

# ============================================
# COURSE MANAGEMENT
# ============================================

@login_required
def course_edit(request, pk):
    """Edit course"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('school:course_list')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'school/course_form.html', {'form': form})

@login_required
def course_delete(request, pk):
    """Delete course"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('school:course_list')
    
    return render(request, 'school/course_confirm_delete.html', {'course': course})

# ============================================
# QUARTER MANAGEMENT
# ============================================

@login_required
def quarter_list(request):
    """List all quarters"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarters = Quarter.objects.all().select_related('academic_year').order_by('-academic_year__start_date', 'name')
    context = {'quarters': quarters}
    return render(request, 'school/quarter_list.html', context)

@login_required
def quarter_create(request):
    """Create quarter"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = QuarterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quarter created successfully!')
            return redirect('school:quarter_list')
    else:
        form = QuarterForm()
    
    context = {'form': form}
    return render(request, 'school/quarter_form.html', context)

@login_required
def quarter_edit(request, pk):
    """Edit quarter"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarter = get_object_or_404(Quarter, pk=pk)
    
    if request.method == 'POST':
        form = QuarterForm(request.POST, instance=quarter)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quarter updated successfully!')
            return redirect('school:quarter_list')
    else:
        form = QuarterForm(instance=quarter)
    
    return render(request, 'school/quarter_form.html', {'form': form})

@login_required
def quarter_delete(request, pk):
    """Delete quarter"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarter = get_object_or_404(Quarter, pk=pk)
    
    if request.method == 'POST':
        quarter.delete()
        messages.success(request, 'Quarter deleted successfully!')
        return redirect('school:quarter_list')
    
    return render(request, 'school/quarter_confirm_delete.html', {'quarter': quarter})

@login_required
def quarter_toggle_active(request, pk):
    """Toggle quarter active status"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarter = get_object_or_404(Quarter, pk=pk)
    
    # Deactivate all other quarters if activating this one
    if not quarter.is_active:
        Quarter.objects.filter(is_active=True).update(is_active=False)
    
    quarter.is_active = not quarter.is_active
    quarter.save()
    
    status = "activated" if quarter.is_active else "deactivated"
    messages.success(request, f'Quarter {quarter.get_name_display()} {status}!')
    return redirect('school:quarter_list')

@login_required
def quarter_lock(request, pk):
    """Lock/unlock quarter"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    quarter = get_object_or_404(Quarter, pk=pk)
    quarter.is_locked = not quarter.is_locked
    quarter.save()
    
    status = "locked" if quarter.is_locked else "unlocked"
    messages.success(request, f'Quarter {quarter.get_name_display()} {status}!')
    return redirect('school:quarter_list')

# ============================================
# TEACHER ASSIGNMENT VIEWS
# ============================================

@login_required
def assignment_list(request):
    """List all teacher assignments"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    assignments = TeacherAssignment.objects.all().select_related(
        'teacher', 'course', 'class_assigned', 'academic_year'
    )
    
    context = {'assignments': assignments}
    return render(request, 'school/assignment_list.html', context)

@login_required
def assignment_create(request):
    """Create teacher assignment"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = TeacherAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher assigned successfully!')
            return redirect('school:assignment_list')
    else:
        form = TeacherAssignmentForm()
    
    context = {'form': form}
    return render(request, 'school/assignment_form.html', context)

@login_required
def assignment_edit(request, pk):
    """Edit teacher assignment"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    assignment = get_object_or_404(TeacherAssignment, pk=pk)
    
    if request.method == 'POST':
        form = TeacherAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect('school:assignment_list')
    else:
        form = TeacherAssignmentForm(instance=assignment)
    
    return render(request, 'school/assignment_form.html', {'form': form})

@login_required
def assignment_delete(request, pk):
    """Delete teacher assignment"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    assignment = get_object_or_404(TeacherAssignment, pk=pk)
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment removed successfully!')
        return redirect('school:assignment_list')
    
    return render(request, 'school/assignment_confirm_delete.html', {'assignment': assignment})

# ============================================
# SEMESTER MANAGEMENT
# ============================================

@login_required
def semester_list(request):
    """List all semesters"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    semesters = Semester.objects.all().select_related(
        'academic_year', 'quarter_1', 'quarter_2'
    ).order_by('-academic_year__start_date', 'name')
    
    context = {'semesters': semesters}
    return render(request, 'school/semester_list.html', context)

@login_required
def semester_create(request):
    """Create semester"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester created successfully!')
            return redirect('school:semester_list')
    else:
        form = SemesterForm()
    
    context = {'form': form}
    return render(request, 'school/semester_form.html', context)

@login_required
def semester_edit(request, pk):
    """Edit semester"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    semester = get_object_or_404(Semester, pk=pk)
    
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester updated successfully!')
            return redirect('school:semester_list')
    else:
        form = SemesterForm(instance=semester)
    
    return render(request, 'school/semester_form.html', {'form': form})

@login_required
def semester_delete(request, pk):
    """Delete semester"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    semester = get_object_or_404(Semester, pk=pk)
    
    if request.method == 'POST':
        semester.delete()
        messages.success(request, 'Semester deleted successfully!')
        return redirect('school:semester_list')
    
    return render(request, 'school/semester_confirm_delete.html', {'semester': semester})

@login_required
def semester_calculate(request, semester_id):
    """Calculate semester results from quarters"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    semester = get_object_or_404(Semester, pk=semester_id)
    
    # Get all quarterly results for both quarters
    q1_results = QuarterlyResult.objects.filter(
        quarter=semester.quarter_1,
        status='approved'
    ).select_related('student', 'course')
    
    q2_results = QuarterlyResult.objects.filter(
        quarter=semester.quarter_2,
        status='approved'
    ).select_related('student', 'course')
    
    # Create dict for easy lookup
    q2_dict = {(r.student_id, r.course_id): r for r in q2_results}
    
    calculated = 0
    
    for q1_result in q1_results:
        # Find matching Q2 result
        key = (q1_result.student_id, q1_result.course_id)
        if key in q2_dict:
            q2_result = q2_dict[key]
            
            # Create or update semester result
            sem_result, created = SemesterResult.objects.get_or_create(
                student=q1_result.student,
                course=q1_result.course,
                semester=semester,
                defaults={
                    'q1_score': q1_result.score,
                    'q2_score': q2_result.score,
                    'total_score': q1_result.score + q2_result.score,
                    'average_score': (q1_result.score + q2_result.score) / 2,
                }
            )
            
            if not created:
                # Update existing
                sem_result.q1_score = q1_result.score
                sem_result.q2_score = q2_result.score
                sem_result.calculate()
            
            calculated += 1
    
    messages.success(request, f'Calculated {calculated} semester results!')
    return redirect('school:semester_list')

@login_required
def semester_lock(request, pk):
    """Lock/unlock semester"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    semester = get_object_or_404(Semester, pk=pk)
    semester.is_locked = not semester.is_locked
    semester.save()
    
    status = "locked" if semester.is_locked else "unlocked"
    messages.success(request, f'Semester {semester.get_name_display()} {status}!')
    return redirect('school:semester_list')

# ============================================
# TEMPLATE MANAGEMENT
# ============================================

@login_required
def template_list(request):
    """List all result templates"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    templates = ResultTemplate.objects.all().select_related('department')
    context = {'templates': templates}
    return render(request, 'school/template_list.html', context)

@login_required
def template_create(request):
    """Create result template"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        form = ResultTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template created successfully!')
            return redirect('school:template_list')
    else:
        form = ResultTemplateForm()
    
    context = {'form': form}
    return render(request, 'school/template_form.html', context)

@login_required
def template_edit(request, pk):
    """Edit result template"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    template = get_object_or_404(ResultTemplate, pk=pk)
    
    if request.method == 'POST':
        form = ResultTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template updated successfully!')
            return redirect('school:template_list')
    else:
        form = ResultTemplateForm(instance=template)
    
    return render(request, 'school/template_form.html', {'form': form})

@login_required
def template_delete(request, pk):
    """Delete result template"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    template = get_object_or_404(ResultTemplate, pk=pk)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template deleted successfully!')
        return redirect('school:template_list')
    
    return render(request, 'school/template_confirm_delete.html', {'template': template})

@login_required
def template_preview(request, pk):
    """Preview result template"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    template = get_object_or_404(ResultTemplate, pk=pk)
    return render(request, 'school/template_preview.html', {'template': template})

# ============================================
# BULK OPERATIONS
# ============================================

@login_required
def bulk_approve_results(request):
    """Bulk approve all pending results"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        updated = QuarterlyResult.objects.filter(
            status='submitted'
        ).update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        
        messages.success(request, f'Approved {updated} results!')
        return redirect('school:approval_list')
    
    return redirect('school:approval_list')

# ============================================
# STUDENT BULK ACTIONS
# ============================================

@login_required
def student_bulk_actions(request):
    """Handle bulk student actions"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('school:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('student_ids')
        
        if action == 'deactivate':
            Student.objects.filter(id__in=student_ids).update(is_active=False)
            messages.success(request, f'{len(student_ids)} students deactivated!')
        
        elif action == 'activate':
            Student.objects.filter(id__in=student_ids).update(is_active=True)
            messages.success(request, f'{len(student_ids)} students activated!')
        
        elif action == 'change_class':
            new_class_id = request.POST.get('new_class')
            if new_class_id:
                Student.objects.filter(id__in=student_ids).update(current_class_id=new_class_id)
                messages.success(request, f'{len(student_ids)} students moved to new class!')
        
        elif action == 'delete':
            Student.objects.filter(id__in=student_ids).delete()
            messages.success(request, f'{len(student_ids)} students deleted!')
    
    return redirect('school:student_list')