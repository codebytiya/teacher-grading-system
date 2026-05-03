from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ========== FACULTY ==========
class Faculty(models.Model):
    facultyid = models.AutoField(db_column='FacultyID', primary_key=True)
    facultyname = models.CharField(db_column='FacultyName', max_length=100)
    deanid = models.IntegerField(db_column='DeanID', blank=True, null=True)

    def __str__(self):
        return self.facultyname

    class Meta:
        db_table = 'faculty'

# ========== DEPARTMENT ==========
class Department(models.Model):
    departmentid = models.AutoField(db_column='DepartmentID', primary_key=True)
    departmentname = models.CharField(db_column='DepartmentName', max_length=100)
    facultyid = models.IntegerField(db_column='FacultyID')

    def __str__(self):
        return self.departmentname

    class Meta:
        db_table = 'department'

# ========== STUDENT ==========
class Student(models.Model):
    studentid = models.AutoField(db_column='StudentID', primary_key=True)
    firstname = models.CharField(db_column='FirstName', max_length=50)
    lastname = models.CharField(db_column='LastName', max_length=50)
    email = models.CharField(db_column='Email', unique=True, max_length=100)
    dateofbirth = models.DateField(db_column='DateOfBirth')
    enrollmentdate = models.DateField(db_column='EnrollmentDate')
    departmentid = models.IntegerField(db_column='DepartmentID')
    phone = models.CharField(db_column='Phone', max_length=20)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    class Meta:
        db_table = 'student'

# ========== COURSE ==========
class Course(models.Model):
    courseid = models.AutoField(db_column='CourseID', primary_key=True)
    coursecode = models.CharField(db_column='CourseCode', unique=True, max_length=20)
    coursename = models.CharField(db_column='CourseName', max_length=100)
    credits = models.IntegerField(db_column='Credits')
    departmentid = models.IntegerField(db_column='DepartmentID')
    description = models.TextField(db_column='Description')

    def __str__(self):
        return f"{self.coursecode} - {self.coursename}"

    class Meta:
        db_table = 'course'

# ========== LECTURE (LECTURER) ==========
class Lecture(models.Model):
    lecturerid = models.AutoField(db_column='LecturerID', primary_key=True)
    firstname = models.CharField(db_column='FirstName', max_length=50)
    lastname = models.CharField(db_column='LastName', max_length=50)
    email = models.CharField(db_column='Email', unique=True, max_length=100)
    departmentid = models.IntegerField(db_column='DepartmentID')
    phone = models.CharField(db_column='Phone', max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    class Meta:
        db_table = 'lecture'

# ========== ENROLLMENT ==========
class Enrollment(models.Model):
    enrollmentid = models.AutoField(db_column='EnrollmentID', primary_key=True)
    studentid = models.ForeignKey(Student, models.DO_NOTHING, db_column='StudentID')
    courseid = models.ForeignKey(Course, models.DO_NOTHING, db_column='CourseID')
    enrollmentdate = models.DateField(db_column='EnrollmentDate')
    semester = models.CharField(db_column='Semester', max_length=20)
    status = models.CharField(db_column='Status', max_length=9)

    def __str__(self):
        return f"{self.studentid.firstname} {self.studentid.lastname} - {self.courseid.coursecode}"

    class Meta:
        db_table = 'enrollment'

# ========== ASSESSMENT ==========
class Assessment(models.Model):
    assessmentid = models.AutoField(db_column='AssessmentID', primary_key=True)
    courseid = models.ForeignKey(Course, models.DO_NOTHING, db_column='CourseID')
    assessmentname = models.CharField(db_column='AssessmentName', max_length=100)
    assessmenttype = models.CharField(db_column='AssessmentType', max_length=10)
    maxscore = models.DecimalField(db_column='MaxScore', max_digits=5, decimal_places=2)
    weight = models.DecimalField(db_column='Weight', max_digits=5, decimal_places=2, blank=True, null=True)
    duedate = models.DateField(db_column='DueDate')

    def __str__(self):
        return f"{self.assessmentname} - {self.courseid.coursecode}"

    class Meta:
        db_table = 'assessment'

# ========== GRADE ==========
class Grade(models.Model):
    gradeid = models.AutoField(db_column='GradeID', primary_key=True)
    studentid = models.ForeignKey(Student, models.DO_NOTHING, db_column='StudentID')
    assessmentid = models.ForeignKey(Assessment, models.DO_NOTHING, db_column='AssessmentID')
    score = models.DecimalField(db_column='Score', max_digits=5, decimal_places=2, blank=True, null=True)
    lettergrade = models.CharField(db_column='LetterGrade', max_length=2, blank=True, null=True)
    submissiondate = models.DateTimeField(db_column='SubmissionDate', blank=True, null=True)
    override_reason = models.TextField(blank=True, null=True)
    was_flagged = models.BooleanField(default=False)
    flagged_by = models.CharField(max_length=50, blank=True, null=True)
    flagged_value = models.FloatField(blank=True, null=True)
    class_average = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.studentid.firstname} {self.studentid.lastname} - {self.assessmentid.assessmentname}: {self.score}"

    class Meta:
        db_table = 'grade'

# ========== COURSE ASSIGNMENT ==========
class CourseAssignment(models.Model):
    assignmentid = models.AutoField(db_column='AssignmentID', primary_key=True)
    courseid = models.ForeignKey(Course, models.DO_NOTHING, db_column='CourseID')
    lecturerid = models.ForeignKey(Lecture, models.DO_NOTHING, db_column='LecturerID')
    semesterid = models.IntegerField(db_column='SemesterID')

    def __str__(self):
        return f"{self.courseid.coursecode} - {self.lecturerid.firstname} {self.lecturerid.lastname}"

    class Meta:
        db_table = 'course_assignment'

# ========== PROFILE (for roles) ==========
class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('hod', 'Head of Department'),
        ('dean', 'Dean'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        db_table = 'user_profile'

# ========== SIGNALS TO AUTO-CREATE PROFILE ==========
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()