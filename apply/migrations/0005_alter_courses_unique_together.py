# Generated by Django 4.2.1 on 2023-12-27 06:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0004_registrationprofile'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='courses',
            unique_together={('course_number', 'course_section', 'course_semester')},
        ),
    ]
