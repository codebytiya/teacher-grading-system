from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/enter-grades/', views.lecturer_enter_grades, name='lecturer_enter_grades'),
    path('lecturer/view-grades/', views.lecturer_view_grades, name='lecturer_view_grades'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('dean/', views.dean_dashboard, name='dean_dashboard'),
]