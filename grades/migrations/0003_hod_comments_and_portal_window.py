from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0002_grade_class_average_grade_flagged_by_and_more'),
    ]

    operations = [
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
    ]
