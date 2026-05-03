from django.contrib import admin
from .models import Faculty, Department, Student, Course, Lecture, Enrollment, Assessment, Grade, Profile, CourseAssignment

# Register Profile (role model)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)

admin.site.register(Profile, ProfileAdmin)

# Register other models
admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Lecture)
admin.site.register(Enrollment)
admin.site.register(Assessment)
admin.site.register(Grade)
admin.site.register(CourseAssignment)