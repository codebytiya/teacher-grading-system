from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
from .models import Profile, Lecture, CourseAssignment, Course, Student, Assessment, Grade, Department

# ========== HELPER ==========
def get_letter_grade(score):
    if score >= 90: return 'A'
    elif score >= 85: return 'A-'
    elif score >= 80: return 'B+'
    elif score >= 75: return 'B'
    elif score >= 70: return 'B-'
    elif score >= 65: return 'C+'
    elif score >= 60: return 'C'
    elif score >= 55: return 'C-'
    elif score >= 50: return 'D'
    else: return 'F'

# ========== LOGIN / LOGOUT ==========
@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                role = user.profile.role
            except Profile.DoesNotExist:
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

# ========== LECTURER DASHBOARD ==========
@login_required
def lecturer_dashboard(request):
    lecturer = None
    
    # Try to find lecturer by exact email match
    lecturers = Lecture.objects.filter(email=request.user.email)
    if lecturers.exists():
        # If multiple lecturers have same email, find the one with course assignments
        for l in lecturers:
            if CourseAssignment.objects.filter(lecturerid=l).exists():
                lecturer = l
                break
        # If none have assignments, take the first one
        if not lecturer:
            lecturer = lecturers.first()
    
    assigned_courses = CourseAssignment.objects.filter(lecturerid=lecturer).select_related('courseid')
    context = {
        'user': request.user,
        'lecturer': lecturer,
        'assigned_courses': assigned_courses,
    }
    return render(request, 'lecturer_dashboard.html', context)

# ========== LECTURER ENTER GRADES ==========
@login_required
def lecturer_enter_grades(request):
    try:
        lecturer = Lecture.objects.filter(email=request.user.email).first()
    except Lecture.DoesNotExist:
        lecturer = None
    
    # Get assigned courses for this lecturer
    assigned_courses = CourseAssignment.objects.filter(lecturerid=lecturer).select_related('courseid')
    
    # Get all students for lookup
    students = Student.objects.all().values('studentid', 'firstname', 'lastname', 'email')
    students_json = json.dumps(list(students))
    
    context = {
        'user': request.user,
        'lecturer': lecturer,
        'assigned_courses': assigned_courses,
        'students_json': students_json,
    }
    return render(request, 'lecturer_enter_grades.html', context)

# ========== LECTURER VIEW GRADES ==========
@login_required
def lecturer_view_grades(request):
    return render(request, 'lecturer_view_grades.html')

# ========== SUBMIT GRADES API ==========
@login_required
@require_http_methods(["POST"])
def submit_grades_api(request):
    try:
        data = json.loads(request.body)
        
        # Handle single grade submission
        if 'student_id' in data:
            student_id = data.get('student_id')
            assignment = float(data.get('assignment', 0))
            quiz = float(data.get('quiz', 0))
            midterm = float(data.get('midterm', 0))
            final_exam = float(data.get('final', 0))
            course_id = data.get('course_id')

            final_score = assignment * 0.20 + quiz * 0.20 + midterm * 0.30 + final_exam * 0.30
            letter = get_letter_grade(final_score)

            course = Course.objects.get(courseid=course_id)
            if not course:
                return JsonResponse({'success': False, 'error': 'Course not found'})
            
            assessment, _ = Assessment.objects.get_or_create(
                assessmentname='Combined Grades',
                assessmenttype='Combined',
                defaults={
                    'maxscore': 100, 
                    'weight': 100, 
                    'courseid': course,
                    'duedate': '2024-12-31'  # Default due date
                }
            )
            student = Student.objects.get(studentid=student_id)

            flagged = (final_score < 40 or final_score > 95)

            Grade.objects.create(
                studentid=student,
                assessmentid=assessment,
                score=final_score,
                lettergrade=letter,
                status='submitted',
                was_flagged=flagged,
                override_reason='' if not flagged else 'Flagged by AI – needs HOD review'
            )

            return JsonResponse({
                'success': True, 
                'flagged': flagged,
                'message': f'Grade submitted successfully for student {student.firstname} {student.lastname}!'
            })
        
        # Handle multiple grades submission
        elif 'grades' in data:
            grades_data = data.get('grades', [])
            course_id = data.get('course_id')
            
            if not course_id:
                return JsonResponse({'success': False, 'error': 'Course ID required'})
                
            course = Course.objects.get(courseid=course_id)
            if not course:
                return JsonResponse({'success': False, 'error': 'Course not found'})
            
            assessment, _ = Assessment.objects.get_or_create(
                assessmentname='Combined Grades',
                assessmenttype='Combined',
                defaults={
                    'maxscore': 100, 
                    'weight': 100, 
                    'courseid': course,
                    'duedate': '2024-12-31'  # Default due date
                }
            )
            
            submitted_count = 0
            for grade_data in grades_data:
                student_id = grade_data.get('student_id')
                assignment = float(grade_data.get('assignment', 0))
                quiz = float(grade_data.get('quiz', 0))
                midterm = float(grade_data.get('midterm', 0))
                final_exam = float(grade_data.get('final', 0))

                final_score = assignment * 0.20 + quiz * 0.20 + midterm * 0.30 + final_exam * 0.30
                letter = get_letter_grade(final_score)

                student = Student.objects.get(studentid=student_id)
                flagged = (final_score < 40 or final_score > 95)

                Grade.objects.create(
                    studentid=student,
                    assessmentid=assessment,
                    score=final_score,
                    lettergrade=letter,
                    status='submitted',
                    was_flagged=flagged,
                    override_reason='' if not flagged else 'Flagged by AI – needs HOD review'
                )
                submitted_count += 1

            return JsonResponse({
                'success': True, 
                'message': f'Successfully submitted {submitted_count} grades!'
            })
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request format'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ========== STUDENT LOOKUP API ==========
@login_required
@require_http_methods(["GET"])
def student_lookup_api(request, student_number):
    try:
        student = Student.objects.get(studentid=student_number)
        data = {
            'studentid': student.studentid,
            'firstname': student.firstname,
            'lastname': student.lastname,
            'email': student.email,
        }
        return JsonResponse({'success': True, 'student': data})
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})

# ========== COURSE STUDENTS API ==========
@login_required
@require_http_methods(["GET"])
def course_students_api(request, course_id):
    try:
        # Get all students enrolled in this course
        enrollments = Enrollment.objects.filter(courseid=course_id).select_related('studentid')
        students_data = []
        
        for enrollment in enrollments:
            student = enrollment.studentid
            students_data.append({
                'studentid': student.studentid,
                'firstname': student.firstname,
                'lastname': student.lastname,
                'email': student.email,
            })
        
        return JsonResponse({'success': True, 'students': students_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ========== STUDENT SEARCH API ==========
@login_required
@require_http_methods(["GET"])
def student_search_api(request):
    try:
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'success': True, 'students': []})
        
        # Search by student ID, first name, or last name
        students = Student.objects.filter(
            models.Q(studentid__icontains=query) |
            models.Q(firstname__icontains=query) |
            models.Q(lastname__icontains=query)
        ).values('studentid', 'firstname', 'lastname', 'email', 'dateofbirth', 'enrollmentdate')
        
        return JsonResponse({'success': True, 'students': list(students)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ========== HOD GRADES VIEW ==========
@login_required
def hod_grades(request):
    flagged_grades = Grade.objects.filter(was_flagged=True).select_related('studentid', 'assessmentid')
    context = {
        'flagged_grades': flagged_grades,
    }
    return render(request, 'hod_grades.html', context)

# ========== PLACEHOLDER DASHBOARDS ==========
@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html')

@login_required
def hod_dashboard(request):
    return render(request, 'hod_dashboard.html')

@login_required
def dean_dashboard(request):
    return render(request, 'dean_dashboard.html')

@login_required
def admin_dashboard(request):
    # Get real counts from database
    student_count = Student.objects.count()
    lecturer_count = Lecture.objects.count()
    course_count = Course.objects.count()
    department_count = Department.objects.count()
    
    # Get first course for display
    first_course = Course.objects.first()
    
    # Get students for the table
    students = Student.objects.all()[:10]  # Show first 10 students
    
    context = {
        'student_count': student_count,
        'lecturer_count': lecturer_count,
        'course_count': course_count,
        'department_count': department_count,
        'first_course': first_course,
        'students': students,
    }
    return render(request, 'admin_dashboard.html', context)