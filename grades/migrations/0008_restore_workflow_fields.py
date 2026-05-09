from django.db import migrations, models


def backfill_student_numbers(apps, schema_editor):
    Student = apps.get_model('grades', 'Student')
    used = set()
    for index, student in enumerate(Student.objects.order_by('studentid'), start=1):
        lastname = student.lastname or 'Student'
        prefix = ''.join(ch for ch in lastname.lower() if ch.isalpha())[:2] or 'st'
        number = f'{prefix}{index:04d}'
        while number in used:
            index += 1
            number = f'{prefix}{index:04d}'
        used.add(number)
        student.studentnumber = number
        student.save(update_fields=['studentnumber'])


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0007_alter_course_description_alter_lecture_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='studentnumber',
            field=models.CharField(blank=True, db_column='StudentNumber', max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='grade',
            name='hod_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='portal_is_open',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='portal_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_student_numbers, migrations.RunPython.noop),
    ]
