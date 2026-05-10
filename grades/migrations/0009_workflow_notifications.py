from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def normalize_statuses(apps, schema_editor):
    Grade = apps.get_model('grades', 'Grade')
    for grade in Grade.objects.all():
        if grade.status == 'final':
            grade.status = 'approved'
        elif grade.status == 'approved':
            grade.status = 'approved_by_hod'
        elif grade.status == 'rejected':
            grade.status = 'returned'
        grade.percentage = grade.score
        grade.letter_grade = grade.lettergrade
        grade.flagged = False if grade.override_reason else grade.was_flagged
        grade.flag_override_reason = grade.override_reason or ''
        grade.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('grades', '0008_restore_workflow_fields'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='courseassignment',
                    name='is_grading_complete',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='courseassignment',
                    name='portal_close_date',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='grade',
                    name='dean_comment',
                    field=models.TextField(blank=True),
                ),
                migrations.AddField(
                    model_name='grade',
                    name='flag_override_reason',
                    field=models.TextField(blank=True),
                ),
                migrations.AddField(
                    model_name='grade',
                    name='flag_reasons',
                    field=models.JSONField(blank=True, default=list),
                ),
                migrations.AddField(
                    model_name='grade',
                    name='flagged',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='grade',
                    name='gpa',
                    field=models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True),
                ),
                migrations.AddField(
                    model_name='grade',
                    name='letter_grade',
                    field=models.CharField(blank=True, max_length=2, null=True),
                ),
                migrations.AddField(
                    model_name='grade',
                    name='percentage',
                    field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
                ),
                migrations.AlterField(
                    model_name='grade',
                    name='status',
                    field=models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted to HoD'), ('approved_by_hod', 'Approved by HoD'), ('returned', 'Returned to Lecturer'), ('approved', 'Published (Final)'), ('declined', 'Declined by Dean')], default='draft', max_length=20),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notification_type', models.CharField(max_length=50)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'grade_notification',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(normalize_statuses, migrations.RunPython.noop),
    ]
