import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import Assessment, Course, CourseAssignment, Department, Enrollment, Grade, Lecture, Profile, Student


FLAG_THRESHOLD = 25
OVERRIDE_CHOICES = ['Medical leave', 'Significant improvement', 'Typo correction', 'Other']


def get_letter_grade(score):
    if score >= 90:
        return 'A'
    if score >= 85:
        return 'A-'
    if score >= 80:
        return 'B+'
    if score >= 75:
        return 'B'
    if score >= 70:
        return 'B-'
    if score >= 65:
        return 'C+'
    if score >= 60:
        return 'C'
    if score >= 55:
        return 'C-'
    if score >= 50:
        return 'D'
    return 'F'


def user_role(user):
    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return 'student'


def require_role(request, role):
    if user_role(request.user) != role:
        return redirect('login')
    return None


def department_name(department_id):
    department = Department.objects.filter(departmentid=department_id).first()
    return department.departmentname if department else f'Department {department_id}'


def lecturer_for_user(user):
    email = (user.email or '').strip()
    username = (user.username or '').strip()
    lecturer = None
    if email:
        lecturer = Lecture.objects.filter(email__iexact=email).first()
    if not lecturer and username:
        lecturer = Lecture.objects.filter(email__iexact=username).first()
    return lecturer


def student_for_user(user):
    email = (user.email or '').strip()
    username = (user.username or '').strip()
    student = None
    if username:
        student = Student.objects.filter(studentnumber__iexact=username).first()
    if not student and email:
        student = Student.objects.filter(email__iexact=email).first()
    return student


def student_lookup(value):
    lookup = str(value or '').strip()
    student = Student.objects.filter(studentnumber__iexact=lookup).first()
    if not student and lookup.isdigit():
        student = Student.objects.filter(studentid=int(lookup)).first()
    return student


def student_payload(student):
    enrollment = (
        Enrollment.objects.filter(studentid=student)
        .select_related('courseid')
        .order_by('-enrollmentdate')
        .first()
    )
    return {
        'studentid': student.studentid,
        'studentnumber': student.studentnumber or str(student.studentid),
        'firstname': student.firstname,
        'lastname': student.lastname,
        'email': student.email,
        'program': enrollment.courseid.coursename if enrollment else 'Not enrolled in a course yet',
        'year': (enrollment.enrollmentdate.year if enrollment else student.enrollmentdate.year),
        'semester': enrollment.semester if enrollment else 'Not enrolled',
        'department': department_name(student.departmentid),
        'mode': 'Full-time',
    }


def course_average(course_id):
    value = (
        Grade.objects.filter(assessmentid__courseid_id=course_id, score__isnull=False)
        .exclude(status='rejected')
        .aggregate(avg=Avg('score'))['avg']
    )
    return float(round(value, 2)) if value is not None else 75.0


def lecturer_course_ids(lecturer):
    return list(CourseAssignment.objects.filter(lecturerid=lecturer).values_list('courseid_id', flat=True))


def lecturer_override_rate(lecturer):
    grades = Grade.objects.filter(assessmentid__courseid_id__in=lecturer_course_ids(lecturer)).exclude(status='draft')
    total = grades.count()
    if not total:
        return 0
    return round((grades.filter(was_flagged=True).count() / total) * 100, 1)


@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if not user:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

        login(request, user)
        role = user_role(user)
        if role == 'student':
            return redirect('student_dashboard')
        if role == 'lecturer':
            return redirect('lecturer_dashboard')
        if role == 'hod':
            return redirect('hod_dashboard')
        if role == 'dean':
            return redirect('dean_dashboard')
        return redirect('/admin/')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def lecturer_dashboard(request):
    redirect_response = require_role(request, 'lecturer')
    if redirect_response:
        return redirect_response
    lecturer = lecturer_for_user(request.user)
    assignments = CourseAssignment.objects.filter(lecturerid=lecturer).select_related('courseid') if lecturer else []
    course_ids = lecturer_course_ids(lecturer) if lecturer else []
    grades = (
        Grade.objects.filter(assessmentid__courseid_id__in=course_ids)
        .select_related('studentid', 'assessmentid', 'assessmentid__courseid')
        .order_by('-submissiondate')
    )
    return render(request, 'lecturer_dashboard.html', {
        'lecturer': lecturer,
        'lecturer_department': department_name(lecturer.departmentid) if lecturer else '',
        'assigned_courses': assignments,
        'grades': grades[:10],
        'submitted_count': grades.filter(status='submitted').count(),
        'approved_count': grades.filter(status__in=['approved', 'final']).count(),
        'rejected_count': grades.filter(status='rejected').count(),
    })


@login_required
def lecturer_enter_grades(request):
    redirect_response = require_role(request, 'lecturer')
    if redirect_response:
        return redirect_response
    lecturer = lecturer_for_user(request.user)
    assignments = CourseAssignment.objects.filter(lecturerid=lecturer, portal_is_open=True).select_related('courseid') if lecturer else []
    students = [student_payload(student) for student in Student.objects.order_by('studentnumber', 'studentid')]
    course_averages = {str(assignment.courseid_id): course_average(assignment.courseid_id) for assignment in assignments}
    return render(request, 'lecturer_enter_grades.html', {
        'lecturer': lecturer,
        'assigned_courses': assignments,
        'students_json': json.dumps(students),
        'course_averages_json': json.dumps(course_averages),
        'override_choices': OVERRIDE_CHOICES,
        'flag_threshold': FLAG_THRESHOLD,
    })


@login_required
def lecturer_view_grades(request):
    redirect_response = require_role(request, 'lecturer')
    if redirect_response:
        return redirect_response
    lecturer = lecturer_for_user(request.user)
    grades = (
        Grade.objects.filter(assessmentid__courseid_id__in=lecturer_course_ids(lecturer))
        .select_related('studentid', 'assessmentid', 'assessmentid__courseid')
        .order_by('-submissiondate')
    )
    return render(request, 'lecturer_view_grades.html', {'lecturer': lecturer, 'grades': grades})


@login_required
def course_students_api(request, course_id):
    students = [
        student_payload(enrollment.studentid)
        for enrollment in Enrollment.objects.filter(courseid_id=course_id).select_related('studentid')
    ]
    if not students:
        students = [student_payload(student) for student in Student.objects.order_by('studentnumber', 'studentid')]
    return JsonResponse({'students': students})


@login_required
def student_detail_api(request, student_id):
    student = student_lookup(student_id)
    if not student:
        return JsonResponse({'error': 'Student not found'}, status=404)
    return JsonResponse(student_payload(student))


@login_required
def student_lookup_api(request, student_number):
    student = student_lookup(student_number)
    if not student:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    return JsonResponse({'success': True, 'student': student_payload(student)})


@login_required
def class_average_api(request):
    course_id = request.GET.get('course_id')
    return JsonResponse({'average': course_average(course_id) if course_id else 0, 'threshold': FLAG_THRESHOLD})


@login_required
@require_http_methods(['POST'])
def submit_grades_api(request):
    redirect_response = require_role(request, 'lecturer')
    if redirect_response:
        return JsonResponse({'success': False, 'error': 'Only lecturers can submit grades.'}, status=403)

    try:
        lecturer = lecturer_for_user(request.user)
        data = json.loads(request.body)
        course_id = int(data.get('course_id'))
        student = student_lookup(data.get('student_id'))
        if not student:
            return JsonResponse({'success': False, 'error': 'Student number was not found.'}, status=404)

        assignment_window = CourseAssignment.objects.filter(
            lecturerid=lecturer,
            courseid_id=course_id,
            portal_is_open=True,
        ).first()
        if not assignment_window:
            return JsonResponse({'success': False, 'error': 'The HOD has closed grade entry for this course.'}, status=403)

        marks = [float(data.get(key, 0)) for key in ['assignment', 'quiz', 'midterm', 'final']]
        if any(mark < 0 or mark > 100 for mark in marks):
            return JsonResponse({'success': False, 'error': 'Each mark must be between 0 and 100.'}, status=400)

        final_score = marks[0] * 0.20 + marks[1] * 0.20 + marks[2] * 0.30 + marks[3] * 0.30
        class_avg = course_average(course_id)
        flagged = abs(final_score - class_avg) > FLAG_THRESHOLD
        reason_type = str(data.get('override_reason_type', '')).strip()
        explanation = str(data.get('override_reason', '')).strip()
        if flagged and (not reason_type or not explanation):
            return JsonResponse({'success': False, 'error': 'Flagged grades need a reason type and explanation.'}, status=400)

        course = get_object_or_404(Course, courseid=course_id)
        assessment, _ = Assessment.objects.get_or_create(
            courseid=course,
            assessmentname='Combined Grades',
            defaults={'assessmenttype': 'Exam', 'maxscore': 100, 'weight': 100, 'duedate': timezone.now().date()},
        )
        existing = Grade.objects.filter(studentid=student, assessmentid=assessment).exclude(status='rejected').first()
        if existing:
            return JsonResponse({'success': False, 'error': 'This student already has a locked submission for this course.'}, status=409)

        Grade.objects.create(
            studentid=student,
            assessmentid=assessment,
            score=round(final_score, 2),
            lettergrade=get_letter_grade(final_score),
            submissiondate=timezone.now(),
            status='submitted',
            was_flagged=flagged,
            flagged_by='Automatic validation' if flagged else '',
            flagged_value=round(final_score, 2) if flagged else None,
            class_average=class_avg,
            override_reason=f'{reason_type}: {explanation}' if flagged else '',
        )
        assignment_window.portal_is_open = False
        assignment_window.portal_updated_at = timezone.now()
        assignment_window.save(update_fields=['portal_is_open', 'portal_updated_at'])
        logout(request)
        return JsonResponse({'success': True, 'flagged': flagged, 'redirect_url': '/'})
    except Exception as error:
        return JsonResponse({'success': False, 'error': str(error)}, status=400)


@login_required
def hod_dashboard(request):
    redirect_response = require_role(request, 'hod')
    if redirect_response:
        return redirect_response
    if request.method == 'POST':
        assignment = get_object_or_404(CourseAssignment, assignmentid=request.POST.get('assignment_id'))
        assignment.portal_is_open = request.POST.get('portal_action') == 'open'
        assignment.portal_updated_at = timezone.now()
        assignment.save(update_fields=['portal_is_open', 'portal_updated_at'])
        return redirect('hod_dashboard')

    pending = Grade.objects.filter(status='submitted').select_related('studentid', 'assessmentid__courseid')
    assignments = CourseAssignment.objects.select_related('courseid', 'lecturerid').order_by('lecturerid__lastname')
    return render(request, 'hod_dashboard.html', {
        'pending_count': pending.count(),
        'flagged_count': pending.filter(was_flagged=True).count(),
        'open_portals': assignments.filter(portal_is_open=True).count(),
        'closed_portals': assignments.filter(portal_is_open=False).count(),
        'assignments': assignments,
        'recent_grades': pending.order_by('-submissiondate')[:8],
    })


@login_required
def hod_grades(request):
    redirect_response = require_role(request, 'hod')
    if redirect_response:
        return redirect_response
    if request.method == 'POST':
        grade_id = request.POST.get('approve') or request.POST.get('reject')
        grade = get_object_or_404(Grade, gradeid=grade_id, status='submitted')
        comment = request.POST.get(f'comment_{grade.gradeid}', '').strip()
        if request.POST.get('approve'):
            if grade.was_flagged and not grade.override_reason:
                grade.status = 'rejected'
                grade.hod_comment = 'Auto-rejected: flagged grade requires lecturer override reason.'
            else:
                grade.status = 'approved'
                grade.hod_comment = comment
        else:
            grade.status = 'rejected'
            grade.hod_comment = comment or 'Sent back by HOD for correction.'
        grade.save(update_fields=['status', 'hod_comment'])
        return redirect('hod_grades')

    grades = (
        Grade.objects.filter(status='submitted')
        .select_related('studentid', 'assessmentid', 'assessmentid__courseid')
        .order_by('-submissiondate')
    )
    lecturer_warnings = {}
    for assignment in CourseAssignment.objects.select_related('lecturerid'):
        rate = lecturer_override_rate(assignment.lecturerid)
        if rate > 50:
            lecturer_warnings[assignment.courseid_id] = f'{assignment.lecturerid} override rate is {rate}%.'
    return render(request, 'hod_grades.html', {
        'grades': grades,
        'threshold': FLAG_THRESHOLD,
        'lecturer_warnings': lecturer_warnings,
    })


@login_required
def dean_dashboard(request):
    redirect_response = require_role(request, 'dean')
    if redirect_response:
        return redirect_response
    if request.method == 'POST':
        if request.POST.get('approve_all_course'):
            course_id = request.POST.get('approve_all_course')
            Grade.objects.filter(status='approved', assessmentid__courseid_id=course_id).update(status='final')
        elif request.POST.get('finalize'):
            grade = get_object_or_404(Grade, gradeid=request.POST.get('finalize'), status='approved')
            grade.status = 'final'
            grade.save(update_fields=['status'])
        return redirect('dean_dashboard')

    approved = Grade.objects.filter(status='approved').select_related('studentid', 'assessmentid__courseid').order_by('-submissiondate')
    rejected = Grade.objects.filter(status='rejected').select_related('studentid', 'assessmentid__courseid').order_by('-submissiondate')[:8]
    course_groups = approved.values('assessmentid__courseid_id', 'assessmentid__courseid__coursecode').annotate(total=Count('gradeid'))
    return render(request, 'dean_dashboard.html', {
        'approved_grades': approved,
        'rejected_grades': rejected,
        'course_groups': course_groups,
        'approved_count': approved.count(),
        'final_count': Grade.objects.filter(status='final').count(),
        'threshold': FLAG_THRESHOLD,
    })


@login_required
def student_dashboard(request):
    redirect_response = require_role(request, 'student')
    if redirect_response:
        return redirect_response
    student = student_for_user(request.user)
    grades = Grade.objects.none()
    if student:
        grades = Grade.objects.filter(studentid=student, status='final').select_related('assessmentid__courseid')
    return render(request, 'student_dashboard.html', {'student': student, 'grades': grades})
