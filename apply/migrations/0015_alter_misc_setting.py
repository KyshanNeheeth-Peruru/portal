# Generated by Django 4.2.1 on 2024-05-14 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0014_delete_faqpdf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='misc',
            name='setting',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]