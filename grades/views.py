from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Profile, Lecture, CourseAssignment

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

# ========== LECTURER DASHBOARD (REAL) ==========
@login_required
def lecturer_dashboard(request):
    try:
        lecturer = Lecture.objects.get(email=request.user.email)
    except Lecture.DoesNotExist:
        lecturer = None

    assigned_courses = CourseAssignment.objects.filter(lecturerid=lecturer).select_related('courseid')

    context = {
        'user': request.user,
        'lecturer': lecturer,
        'assigned_courses': assigned_courses,
    }
    return render(request, 'lecturer_dashboard.html', context)

# ========== STUDENT DASHBOARD (PLACEHOLDER) ==========
@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html')   # or a simple HttpResponse

# ========== HOD DASHBOARD (PLACEHOLDER) ==========
@login_required
def hod_dashboard(request):
    return render(request, 'hod_dashboard.html')

# ========== DEAN DASHBOARD (PLACEHOLDER) ==========
@login_required
def dean_dashboard(request):
    return render(request, 'dean_dashboard.html')