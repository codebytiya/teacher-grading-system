import random
import string
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Assessment,
    Course,
    CourseAssignment,
    Department,
    Enrollment,
    Faculty,
    Grade,
    Lecture,
    Notification,
    Profile,
    Student,
)

admin.site.site_header = 'ICBM'
admin.site.site_title = 'ICBM Admin'
admin.site.index_title = 'Admin Profile'


DEFAULT_PASSWORD = 'ChangeMe123!'

def generate_password(length=12):
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


ADMIN_MODEL_ORDER = [
    ('auth', 'User'),
    ('grades', 'Profile'),
    ('grades', 'Lecture'),
    ('grades', 'Student'),
    ('grades', 'Enrollment'),
    ('grades', 'Department'),
    ('grades', 'Course'),
    ('grades', 'Assessment'),
]


def ordered_app_list(request):
    original = admin.site._build_app_dict(request)
    models = {}
    for app_label, app_data in original.items():
        for model_data in app_data['models']:
            models[(app_label, model_data['object_name'])] = model_data

    ordered_models = [models[key] for key in ADMIN_MODEL_ORDER if key in models]
    return [{
        'name': 'Admin Profile',
        'app_label': 'admin_profile',
        'app_url': '',
        'has_module_perms': True,
        'models': ordered_models,
    }]


admin.site.get_app_list = ordered_app_list


def ensure_role_user(request, email, first_name, last_name, role, username=None, generate_new_password=False):
    username = username or email
    if not username:
        return None

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        },
    )
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    
    if created or generate_new_password:
        password = generate_password()
        user.set_password(password)
        user.save()
        
        # Store the password in session to display to admin
        from django.contrib.messages import get_messages
        messages.info(request, f"Generated password for {username}: {password}")
    
    user.save()

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.role = role
    profile.save()
    return user


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'role')


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    class CourseAssignmentInline(admin.TabularInline):
        model = CourseAssignment
        extra = 1
        fields = ('courseid', 'semesterid')

    inlines = [CourseAssignmentInline]
    list_display = ('lecturerid', 'firstname', 'lastname', 'email', 'departmentid', 'phone')
    search_fields = ('firstname', 'lastname', 'email')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        ensure_role_user(request, obj.email, obj.firstname, obj.lastname, 'lecturer')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('studentnumber', 'studentid', 'firstname', 'lastname', 'email', 'departmentid', 'enrollmentdate')
    readonly_fields = ('studentnumber',)
    search_fields = ('studentnumber', 'firstname', 'lastname', 'email')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        ensure_role_user(request, obj.email, obj.firstname, obj.lastname, 'student', username=obj.studentnumber or obj.email)


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('courseid', 'lecturerid', 'semesterid', 'get_lecturer_email', 'assignment_date')
    list_filter = ('semesterid', 'courseid__departmentid', 'lecturerid')
    search_fields = ('courseid__coursecode', 'courseid__coursename', 'lecturerid__firstname', 'lecturerid__lastname', 'lecturerid__email')
    raw_id_fields = ('courseid', 'lecturerid')
    list_per_page = 20
    ordering = ('-assignmentid',)
    
    fieldsets = (
        ('Course Assignment', {
            'fields': ('courseid', 'lecturerid', 'semesterid'),
            'classes': ('wide',),
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['courseid', 'lecturerid']:
            kwargs['queryset'] = db_field.related_model.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_lecturer_email(self, obj):
        return obj.lecturerid.email
    get_lecturer_email.short_description = 'Lecturer Email'
    
    def assignment_date(self, obj):
        return obj.assignmentid
    assignment_date.short_description = 'Assignment ID'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            messages.success(request, f"✅ Course {obj.courseid.coursecode} successfully assigned to {obj.lecturerid.firstname} {obj.lecturerid.lastname}")
        else:
            messages.success(request, f"📝 Course assignment for {obj.courseid.coursecode} updated")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('courseid', 'lecturerid')
    
    actions = ['bulk_assign_to_lecturer']
    
    def bulk_assign_to_lecturer(self, request, queryset):
        # This is a placeholder for bulk assignment
        messages.info(request, f"📋 Selected {queryset.count()} course assignments for bulk operations")
    bulk_assign_to_lecturer.short_description = "Bulk assign selected courses"


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('gradeid', 'studentid', 'assessmentid', 'percentage', 'letter_grade', 'status', 'flagged')
    list_filter = ('status', 'flagged')
    search_fields = ('studentid__firstname', 'studentid__lastname', 'assessmentid__assessmentname')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'read', 'created_at')
    list_filter = ('notification_type', 'read')
    search_fields = ('recipient__username', 'sender__username', 'message')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('coursecode', 'coursename', 'departmentid', 'credits', 'get_assigned_lecturers')
    list_filter = ('departmentid',)
    search_fields = ('coursecode', 'coursename', 'departmentid__name')
    readonly_fields = ('courseid',)
    list_per_page = 25
    ordering = ('coursecode',)
    
    fieldsets = (
        ('Course Information', {
            'fields': ('coursecode', 'coursename', 'description', 'credits', 'departmentid'),
            'classes': ('wide',),
        }),
    )
    
    class CourseAssignmentInline(admin.TabularInline):
        model = CourseAssignment
        extra = 3
        fields = ('lecturerid', 'semesterid')
        min_num = 0
        
    def get_assigned_lecturers(self, obj):
        assignments = CourseAssignment.objects.filter(courseid=obj)
        lecturers = [f"{a.lecturerid.firstname} {a.lecturerid.lastname}" for a in assignments]
        return ", ".join(lecturers[:3]) + ("..." if len(lecturers) > 3 else "")
    get_assigned_lecturers.short_description = 'Assigned Lecturers'
    
    inlines = [CourseAssignmentInline]

admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(Enrollment)
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('assessmentname', 'courseid', 'assessmenttype', 'duedate', 'submission_deadline')
    list_filter = ('assessmenttype', 'duedate')
    search_fields = ('assessmentname', 'courseid__coursecode', 'courseid__coursename')
