# Generated by Django 4.2.1 on 2024-05-07 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0008_alter_random_alerts_alter_random_stats'),
    ]

    operations = [
        migrations.CreateModel(
            name='Misc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('setting', models.IntegerField()),
                ('value', models.IntegerField()),
            ],
        ),
    ]