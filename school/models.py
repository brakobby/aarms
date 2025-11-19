from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ============================================
# USER MODEL (Custom)
# ============================================

class User(AbstractUser):
    """Custom user with roles"""
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('class_teacher', 'Class Teacher'),
        ('principal', 'Principal'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def is_teacher(self):
        return self.role in ['teacher', 'class_teacher']


# ============================================
# ACADEMIC STRUCTURE
# ============================================

class Department(models.Model):
    """Departments like Primary, JHS, etc."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    """Academic year e.g., 2024/2025"""
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name


class Class(models.Model):
    """Classes like Grade 1A, Grade 2B"""
    name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classes')
    class_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_classes')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes')
    capacity = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Classes'
    
    def __str__(self):
        return f"{self.name} - {self.department.code}"


# ============================================
# COURSES
# ============================================

class Course(models.Model):
    """Subjects/Courses"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class TeacherAssignment(models.Model):
    """Teachers assigned to courses"""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['teacher', 'course', 'class_assigned', 'academic_year']
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.course.code} - {self.class_assigned.name}"


# ============================================
# STUDENTS
# ============================================

class Student(models.Model):
    """Student records"""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    
    admission_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    current_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    
    # Guardian info
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    guardian_email = models.EmailField(blank=True)
    guardian_address = models.TextField()
    
    is_active = models.BooleanField(default=True)
    enrollment_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.admission_number} - {self.get_full_name()}"
    
    def get_full_name(self):
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name}{middle} {self.last_name}"


# ============================================
# RESULTS
# ============================================

class Quarter(models.Model):
    """Quarters Q1, Q2, Q3, Q4"""
    QUARTER_CHOICES = (
        ('Q1', 'Quarter 1'),
        ('Q2', 'Quarter 2'),
        ('Q3', 'Quarter 3'),
        ('Q4', 'Quarter 4'),
    )
    
    name = models.CharField(max_length=2, choices=QUARTER_CHOICES)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['name', 'academic_year']
        ordering = ['academic_year', 'name']
    
    def __str__(self):
        return f"{self.get_name_display()} - {self.academic_year.name}"


class QuarterlyResult(models.Model):
    """Quarterly results"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    score = models.DecimalField(max_digits=5, decimal_places=2, 
                               validators=[MinValueValidator(0), MaxValueValidator(100)])
    teacher_comment = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_results')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course', 'quarter']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code} - {self.quarter.name}"
    
    def get_grade(self):
        if self.score >= 90: return 'A'
        elif self.score >= 80: return 'B'
        elif self.score >= 70: return 'C'
        elif self.score >= 60: return 'D'
        else: return 'F'


class Semester(models.Model):
    """Semesters (S1 = Q1+Q2, S2 = Q3+Q4)"""
    SEMESTER_CHOICES = (
        ('S1', 'Semester 1'),
        ('S2', 'Semester 2'),
    )
    
    name = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    quarter_1 = models.ForeignKey(Quarter, on_delete=models.CASCADE, related_name='sem_q1')
    quarter_2 = models.ForeignKey(Quarter, on_delete=models.CASCADE, related_name='sem_q2')
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['name', 'academic_year']
    
    def __str__(self):
        return f"{self.get_name_display()} - {self.academic_year.name}"


class SemesterResult(models.Model):
    """Semester results (auto-calculated)"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    
    q1_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    q2_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_score = models.DecimalField(max_digits=5, decimal_places=2)
    average_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    teacher_comment = models.TextField(blank=True)
    class_teacher_comment = models.TextField(blank=True)
    headteacher_comment = models.TextField(blank=True)
    
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'course', 'semester']
    
    def calculate(self):
        """Calculate semester totals"""
        if self.q1_score and self.q2_score:
            self.total_score = self.q1_score + self.q2_score
            self.average_score = self.total_score / 2
            self.save()
    
    def get_grade(self):
        if self.average_score >= 90: return 'A'
        elif self.average_score >= 80: return 'B'
        elif self.average_score >= 70: return 'C'
        elif self.average_score >= 60: return 'D'
        else: return 'F'


# ============================================
# TEMPLATES
# ============================================

class ResultTemplate(models.Model):
    """Print templates"""
    TYPE_CHOICES = (
        ('quarterly', 'Quarterly Report'),
        ('semester', 'Semester Report'),
    )
    
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    template_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    html_content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.department.code}"