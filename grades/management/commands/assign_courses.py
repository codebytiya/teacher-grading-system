from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib import messages
from grades.models import Course, CourseAssignment, Lecture
import random

class Command(BaseCommand):
    help = 'Quickly assign multiple courses to lecturers'

    def add_arguments(self, parser):
        parser.add_argument('--lecturer', type=str, help='Lecturer email or username')
        parser.add_argument('--courses', type=str, help='Comma-separated list of course codes')
        parser.add_argument('--semester', type=str, default='2024-1', help='Semester identifier')

    def handle(self, *args, **options):
        lecturer_email = options.get('lecturer')
        course_codes = options.get('courses')
        semester_id = options.get('semester')

        if not lecturer_email or not course_codes:
            self.stdout.write(self.style.ERROR('Please provide both --lecturer and --courses arguments'))
            return

        try:
            lecturer = Lecture.objects.get(email__icontains=lecturer_email)
        except Lecture.DoesNotExist:
            try:
                user = User.objects.get(email__icontains=lecturer_email)
                lecturer = Lecture.objects.get(lecturerid=user.lecturerid)
            except:
                self.stdout.write(self.style.ERROR(f'Lecturer {lecturer_email} not found'))
                return

        course_codes = [code.strip() for code in course_codes.split(',')]
        assigned_count = 0

        for course_code in course_codes:
            try:
                course = Course.objects.get(coursecode__iexact=course_code)
                
                # Check if already assigned
                if CourseAssignment.objects.filter(
                    courseid=course, 
                    lecturerid=lecturer, 
                    semesterid=semester_id
                ).exists():
                    self.stdout.write(self.style.WARNING(f'Course {course_code} already assigned to {lecturer.firstname}'))
                    continue

                # Create assignment
                assignment = CourseAssignment.objects.create(
                    courseid=course,
                    lecturerid=lecturer,
                    semesterid=semester_id
                )
                assigned_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Assigned {course_code} to {lecturer.firstname} {lecturer.lastname}'))

            except Course.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Course {course_code} not found'))

        self.stdout.write(self.style.SUCCESS(f'\n🎉 Successfully assigned {assigned_count} courses to {lecturer.firstname} {lecturer.lastname}'))
