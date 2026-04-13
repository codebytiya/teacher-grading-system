from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Student, Grade, Lecture, Course, UserProfile

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            try:
                profile = user.userprofile
                role = profile.role
            except:
                role = 'student'
            
            if role == 'student':
                return redirect('student_dashboard')
            elif role == 'lecturer':
                return redirect('lecturer_dashboard')
            elif role == 'hod':
                return redirect('hod_dashboard')
            elif role == 'dean':
                return redirect('dean_dashboard')
            else:
                return redirect('/admin/')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def student_dashboard(request):
    try:
        student = Student.objects.get(email=request.user.email)
    except Student.DoesNotExist:
        student = Student.objects.first()
    
    grades = Grade.objects.filter(studentid=student)
    
    context = {
        'user': request.user,
        'student': student,
        'grades': grades,
    }
    return render(request, 'student_dashboard.html', context)
@login_required
def lecturer_enter_grades(request):
    # Get the lecturer based on email
    try:
        lecturer = Lecture.objects.get(email=request.user.email)
    except Lecture.DoesNotExist:
        lecturer = None
    
    # Get courses assigned to this lecturer
    from .models import CourseAssignment
    assigned_courses = CourseAssignment.objects.filter(lecturerid=lecturer).select_related('courseid')
    students = Student.objects.all()
    
    # Get students enrolled in those courses
    students = Student.objects.filter(enrollment__courseid__in=[ac.courseid for ac in assigned_courses]).distinct()
    
    if request.method == 'POST':
        # Process grade submission
        for student in students:
            score = request.POST.get(f'score_{student.studentid}')
            assessment_id = request.POST.get('assessment_id')
            if score and assessment_id:
                Grade.objects.update_or_create(
                    studentid=student,
                    assessmentid_id=assessment_id,
                    defaults={
                        'score': score,
                        'submissiondate': timezone.now(),
                        'was_flagged': False,
                    }
                )
        messages.success(request, "Grades submitted successfully!")
        return redirect('lecturer_dashboard')
    
    context = {
        'user': request.user,
        'lecturer': lecturer,
        'students': students,
        'assigned_courses': assigned_courses,
    }
    return render(request, 'lecturer_enter_grades.html', context)

@login_required
def lecturer_dashboard(request):
    try:
        lecturer = Lecture.objects.get(email=request.user.email)
    except Lecture.DoesNotExist:
        lecturer = Lecture.objects.first()
    
    context = {
        'user': request.user,
        'lecturer': lecturer,
    }
    return render(request, 'lecturer_dashboard.html', context)
from django.contrib import messages

@login_required
def hod_grades(request):
    if request.method == 'POST':
        if 'approve' in request.POST:
            grade_id = request.POST.get('approve')
            grade = Grade.objects.get(gradeid=grade_id)
            grade.was_flagged = False
            grade.override_reason = f"Approved by HOD on {timezone.now()}"
            grade.save()
            messages.success(request, f"Grade for {grade.studentid.firstname} {grade.studentid.lastname} approved!")
        
        elif 'reject' in request.POST:
            grade_id = request.POST.get('reject')
            grade = Grade.objects.get(gradeid=grade_id)
            grade.was_flagged = True
            grade.override_reason = f"Rejected by HOD - needs review"
            grade.save()
            messages.error(request, f"Grade for {grade.studentid.firstname} {grade.studentid.lastname} rejected!")
        
        return redirect('hod_grades')
    
    # Get all grades that need review
    grades = Grade.objects.all().select_related('studentid', 'assessmentid', 'assessmentid__courseid')
    
    context = {
        'user': request.user,
        'grades': grades,
    }
    return render(request, 'hod_grades.html', context)

@login_required
def hod_dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, 'hod_dashboard.html', context)
@login_required
def lecturer_view_grades(request):
    try:
        lecturer = Lecture.objects.get(email=request.user.email)
    except Lecture.DoesNotExist:
        lecturer = None
    
    # Get grades for courses taught by this lecturer
    grades = Grade.objects.filter(
        assessmentid__courseid__courseassignment__lecturerid=lecturer
    ).select_related('studentid', 'assessmentid', 'assessmentid__courseid')
    
    context = {
        'user': request.user,
        'lecturer': lecturer,
        'grades': grades,
    }
    return render(request, 'lecturer_view_grades.html', context)

@login_required
def dean_dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, 'dean_dashboard.html', context)

@login_required
def lecturer_enter_grades(request):
    try:
        lecturer = Lecture.objects.get(email=request.user.email)
    except Lecture.DoesNotExist:
        lecturer = None
    
    assigned_courses = CourseAssignment.objects.filter(lecturerid=lecturer).select_related('courseid')
    
    # Get all students (you can filter by course later)
    students = Student.objects.all()
    
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        assessment_type = request.POST.get('assessment_type')
        override_reason = request.POST.get('override_reason', '')
        
        for student in students:
            score = request.POST.get(f'score_{student.studentid}')
            if score:
                # Create or update grade
                grade, created = Grade.objects.update_or_create(
                    studentid=student,
                    assessmentid__assessmenttype=assessment_type,
                    defaults={
                        'score': score,
                        'submissiondate': timezone.now(),
                        'override_reason': override_reason,
                        'was_flagged': False,
                    }
                )
        
        messages.success(request, "Grades submitted successfully!")
        return redirect('lecturer_dashboard')
    
    context = {
        'user': request.user,
        'lecturer': lecturer,
        'students': students,
        'assigned_courses': assigned_courses,
    }
    return render(request, 'lecturer_enter_grades.html', context)
from .models import Student, Grade, Lecture, Course, UserProfile, CourseAssignment