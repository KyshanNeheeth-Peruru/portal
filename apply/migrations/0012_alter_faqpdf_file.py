# Generated by Django 4.2.1 on 2024-05-14 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0011_remove_faq_pdf_faqpdf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faqpdf',
            name='file',
            field=models.FileField(upload_to='static/pdfs/'),
        ),
    ]
