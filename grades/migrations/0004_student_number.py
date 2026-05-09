from django.db import migrations, models


def populate_student_numbers(apps, schema_editor):
    Student = apps.get_model('grades', 'Student')
    for index, student in enumerate(Student.objects.order_by('studentid'), start=1600):
        if not student.studentnumber:
            student.studentnumber = f'MA{index}'
            student.save(update_fields=['studentnumber'])


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0003_hod_comments_and_portal_window'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='studentnumber',
            field=models.CharField(blank=True, db_column='StudentNumber', max_length=20, null=True, unique=True),
        ),
        migrations.RunPython(populate_student_numbers, migrations.RunPython.noop),
    ]
