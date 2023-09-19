from django.contrib import admin
from apply.models import Courses, UserCourses, Semesters, Faq, CoursesAdmin, RegistrationProfile

# Register your models here.

admin.site.register(Courses, CoursesAdmin)
admin.site.register(UserCourses)
admin.site.register(Semesters)
admin.site.register(Faq)
admin.site.register(RegistrationProfile)