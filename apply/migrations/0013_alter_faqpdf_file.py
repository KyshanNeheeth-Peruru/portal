# Generated by Django 4.2.1 on 2024-05-14 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0012_alter_faqpdf_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faqpdf',
            name='file',
            field=models.FileField(upload_to='pdfs/'),
        ),
    ]