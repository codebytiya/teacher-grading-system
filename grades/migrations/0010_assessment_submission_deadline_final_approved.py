from django.db import migrations, models
from datetime import datetime, time


def backfill_submission_deadlines(apps, schema_editor):
    Assessment = apps.get_model('grades', 'Assessment')
    for assessment in Assessment.objects.filter(submission_deadline__isnull=True):
        assessment.submission_deadline = datetime.combine(assessment.duedate, time(23, 59))
        assessment.save(update_fields=['submission_deadline'])


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0009_workflow_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='submission_deadline',
            field=models.DateTimeField(blank=True, db_column='SubmissionDeadline', null=True),
        ),
        migrations.AlterField(
            model_name='grade',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted to HoD'), ('approved_by_hod', 'Approved by HoD'), ('returned', 'Returned to Lecturer'), ('approved', 'Published (Final)'), ('final_approved', 'Final Approved'), ('declined', 'Declined by Dean')], default='draft', max_length=20),
        ),
        migrations.RunPython(backfill_submission_deadlines, migrations.RunPython.noop),
    ]
