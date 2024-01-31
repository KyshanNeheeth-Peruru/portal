from django.contrib import admin
from apply.models import Courses, UserCourses, Semesters, Faq, CoursesAdmin, Random

# Register your models here.
# class UserCoursesAdmin(admin.ModelAdmin):
#     search_fields = ['user__username', 'course__course_name', 'semester_year']
admin.site.register(Courses, CoursesAdmin)
admin.site.register(UserCourses)
admin.site.register(Semesters)
admin.site.register(Faq)
admin.site.register(Random)