# Generated by Django 4.2.1 on 2024-05-28 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0015_alter_misc_setting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='misc',
            name='value',
            field=models.CharField(max_length=255),
        ),
    ]
