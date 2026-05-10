from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/grades/', views.hod_grades, name='hod_grades'),
    path('dean/', views.dean_dashboard, name='dean_dashboard'),
    path('lecturer/enter-grades/', views.lecturer_enter_grades, name='lecturer_enter_grades'),
    path('lecturer/view-grades/', views.lecturer_view_grades, name='lecturer_view_grades'),
    path('lecturer/finalize/<int:assignment_id>/', views.lecturer_finalize_course, name='lecturer_finalize_course'),
    path('api/course-students/<int:course_id>/', views.course_students_api, name='course_students_api'),
    path('api/student/<int:student_id>/', views.student_detail_api, name='student_detail_api'),
    path('api/students/<str:student_number>/', views.student_lookup_api, name='student_lookup_api'),
    path('api/class-average/', views.class_average_api, name='class_average_api'),
    path('lecturer/submit-grade/', views.submit_grades_api, name='submit_grades_api'),
]
