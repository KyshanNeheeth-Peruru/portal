"""
URL configuration for portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView

from apply import views as apply_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', apply_views.login_view, name='login'),
    path('login/', apply_views.login_view, name='login'),
    path('courses_list/', apply_views.courses_list_view, name='courses_list'),
    path("register/", apply_views.register_view),
    path('password_reset/', apply_views.change_password, name='forgotpasw'),
    path('logout/', apply_views.logout_view, name='logout'),
    path("activate/<uidb64>/<token>", apply_views.verification_view, name="activate"),
    path("courses/", apply_views.selected_courses),
    path("courses/registered/", apply_views.registered_courses, name="registeredCourses"),
    path('password/', apply_views.change_password, name='change_password'),
    path("about_us/", apply_views.about_us, name='about_us'),
    path("faq/", apply_views.faq, name='faq'),
    path("printQuota/", apply_views.printQuota, name='printQuota'),
    path("lablist/", apply_views.lablist, name='lablist'),
    path("admin_view/", apply_views.admin_view, name='admin_view'),
]
