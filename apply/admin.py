from django.contrib import admin
from apply.models import Courses, EmailVerificationToken, UserCourses, Semesters, Faq, CoursesAdmin, Random, UserCoursesAdmin, Misc
from django.contrib.auth.models import User

# Register your models here.
# class UserCoursesAdmin(admin.ModelAdmin):
#     search_fields = ['user__username', 'course__course_name', 'semester_year']

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name','last_name','date_joined','is_staff')
    
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Courses, CoursesAdmin)
admin.site.register(UserCourses, UserCoursesAdmin)
admin.site.register(Semesters)
admin.site.register(Faq)
admin.site.register(Random)
admin.site.register(Misc)
admin.site.register(EmailVerificationToken)