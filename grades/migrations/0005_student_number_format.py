from django.db import migrations


def formatted_number(student, index):
    lastname = student.lastname or 'Student'
    prefix = ''.join(ch for ch in lastname.lower() if ch.isalpha())[:2] or 'st'
    return f'{prefix}{index:04d}'


def update_existing_student_numbers(apps, schema_editor):
    Student = apps.get_model('grades', 'Student')
    for index, student in enumerate(Student.objects.order_by('studentid'), start=1):
        student.studentnumber = formatted_number(student, index)
        student.save(update_fields=['studentnumber'])


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0004_student_number'),
    ]

    operations = [
        migrations.RunPython(update_existing_student_numbers, migrations.RunPython.noop),
    ]
