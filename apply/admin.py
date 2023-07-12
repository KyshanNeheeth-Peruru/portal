from django.contrib import admin
from apply.models import Courses, UserCourses, Semesters, Faq

# Register your models here.

admin.site.register(Courses)
admin.site.register(UserCourses)
admin.site.register(Semesters)
admin.site.register(Faq)