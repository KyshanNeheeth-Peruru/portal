from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import UnicodeUsernameValidator

# Create your models here.

class Semesters(models.Model):
    semester_abbrev = models.CharField(max_length=8, primary_key=True)
    semester_longname = models.CharField(max_length=40)

    def __str__(self):
        return self.semester_longname

    class Meta:
        verbose_name = "Semesters"
        verbose_name_plural = "Semesters"

    def __unicode__(self):
        return self.semester_longname


class Courses(models.Model):
    course_number = models.CharField(max_length=8)
    course_section = models.CharField(max_length=8)
    course_name = models.CharField(max_length=60)
    course_instructor = models.CharField(max_length=60)
    course_description = models.TextField(blank=True)
    course_semester = models.ForeignKey(Semesters, on_delete=models.CASCADE)
    course_active = models.BooleanField(default=False)
    course_notes = models.CharField(max_length=255, default="", blank=True)
    prof_unix_name = models.CharField(max_length=10, blank=False)

    def __str__(self):
        return self.course_number

    class Meta:
        verbose_name = "Courses"
        verbose_name_plural = "Courses"

    def __unicode__(self):
        return "{}, {}, {}".format(
            self.course_number, self.course_section, self.course_semester
        )


class UserCourses(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    semester_year = models.CharField(max_length=20)
    enrolled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    # notified = models.BooleanField()

    def __str__(self):
        return f"{self.user} {self.course}"

    class Meta:
        verbose_name = "User Courses"
        verbose_name_plural = "User Courses"

    def __unicode__(self):
        return self.user.username
