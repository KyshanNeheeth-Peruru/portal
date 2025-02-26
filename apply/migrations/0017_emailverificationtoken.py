# Generated by Django 5.1.3 on 2025-01-26 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0016_alter_misc_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('token_hash', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
            ],
        ),
    ]
