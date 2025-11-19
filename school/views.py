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
    """Main dashboard - Admin or Teacher"""
    context = {}

    if request.user.role == 'admin':
        context.update({
            'total_students': Student.objects.filter(is_active=True).count(),
            'total_teachers': User.objects.filter(role__in=['teacher', 'class_teacher']).count(),
            'total_classes': Class.objects.count(),
            'pending_results': QuarterlyResult.objects.filter(status='submitted').count(),
        })
        return render(request, 'school/admin_dashboard.html', context)

    elif request.user.is_teacher():
        assignments = TeacherAssignment.objects.filter(
            teacher=request.user,
            academic_year__is_active=True  # Only current year
        ).select_related('class_assigned', 'course', 'class_assigned__department')

        context.update({
            'my_classes': assignments,
            'submitted_results': QuarterlyResult.objects.filter(
                teacher=request.user,
                status='submitted'
            ).count(),
        })
        return render(request, 'school/teacher_dashboard.html', context)

    # Fallback (e.g. principal)
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