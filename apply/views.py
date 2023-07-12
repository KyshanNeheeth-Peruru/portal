from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import login, logout, get_user_model, authenticate, update_session_auth_hash
from apply.constants import ActionNames
from apply.forms import RegistrationForm, AdminView
from apply.helper import insert_courses_into_user_courses, semester_year, change_ldap_password
from apply.models import Courses, UserCourses, Semesters, Faq
from apply.utils import token_generator
from apply.ldap_helper import LDAPHelper
from apply.remote_connect import RemoteConnect
from apply.ldap import LDAP

# Create your views here.

#logger = logging.getLogger(__name__)


def activate_user(user):
    user.is_active = True
    user.save()
    obj = LDAPHelper(**{"userName": user})
    obj.unlock_ldap_account()


def deactivate_user(user):
    user.is_active = False
    user.save()


def create_ldap_user(request):
    user = {
        "userName": request.POST["username"],
        "userPassword": request.POST["password2"],
        "fullName": f"{request.POST['first_name'].capitalize()} {request.POST['last_name'].capitalize()}",
        "firstName": request.POST["first_name"].capitalize(),
        "lastName": request.POST["last_name"].capitalize(),
        "email": request.POST["email"],
    }
    obj = LDAP(**user)
    obj.add_new_user()
    
def send_activation_email(request, user):
    global login_name
    login_name = user.username
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    domain = get_current_site(request).domain
    link = reverse(
        "activate",
        kwargs={"uidb64": uidb64, "token": token_generator.make_token(user)},
    )
    activity_url = f"http://{domain}{link}"
    email_subject = ActionNames.EmailSubject
    email_body = f"Hi {user.first_name} please use this link to activate the account\n {activity_url}"
    user_email = request.POST.get("email")
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email="noreply@cs.umb.edu",
        to=[user_email],
    )
    email.send()
    logger.debug(f"Verification Email has been sent to {user_email}")


def register_view(request):
    if request.method == "POST":
        username= request.POST['username']
        firstname= request.POST['firstname']
        lastname= request.POST['lastname']
        email= request.POST['email']
        pasw1= request.POST['pasw1']
        pasw2= request.POST['pasw2']
        if(pasw1!=pasw2):
            messages.error(request,"Passwords dont match")
            return redirect('signup')
        else:
            user = User.objects.create_user(username,email,pasw1)
            user.first_name = firstname
            user.last_name = lastname
            user.save()
            # user = User.objects.get(username=request.POST["username"])
            #deactivate_user(user)
            # create_ldap_user(request)
            #send_activation_email(request, user)
            # return render(request, "../templates/home.html", {"activated": False})
            return render(request, "../templates/registration/register.html")
    return render(request, "../templates/registration/register.html")


login_name = ""


def verification_view(request, uidb64, token):
    user = User.objects.get(username=login_name)
    activate_user(user)
    logger.debug("Verification link has been generated")
    return render(request, "../templates/home.html", {"activated": True})

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request, 'registered_courses.html')

        else:
            messages.error(request, "Username or password invalid")
            return redirect('registered_courses')

    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    messages.success(request,"Logged out")
    return redirect('login')


# @login_required(login_url="/accounts/login/")
def selected_courses(request):
    if request.method == "POST":
        userID = request.user.id
        selectedID = request.POST.getlist("id")
        userName = request.user.username
        obj = LDAPHelper(**{"userName": userName})
        remote_connection = RemoteConnect()
        semester = semester_year().lower().split()
        if semester[0] == "summer":
            semester = semester[0][:3] + semester[1][2:]
        else:
            semester = semester[0][:1] + semester[1][2:]

        for courseID in selectedID:
            temp = Courses.objects.filter(id=int(courseID))
            selectedCourse = temp[0].course_number
            selectedCourseSection = temp[0].course_section
            selectedCoursesInstructor = temp[0].course_instructor
            selectedCoursesSemester = temp[0].course_semester.semester_abbrev
            prof_unix_name = temp[0].prof_unix_name
            insert_courses_into_user_courses(userID,
                                             selectedCourse,
                                             selectedCoursesSemester,
                                             selectedCourseSection,
                                             selectedCoursesInstructor
                                             )
            ldapCourseSection = f"{selectedCourse}-{selectedCourseSection}"
            graderGroup = f"{selectedCourse}-{selectedCourseSection}G"
            uid = obj.get_uid_number()
            obj.add_user_to_courses(ldapCourseSection)
            remote_connection.execute_command(f"sudo python3 /srv/course_directory.py -user {userName} "
                                              f"-course {selectedCourse} -sem {semester} "
                                              f"-prof {prof_unix_name} -uid {uid} -graderGroup {graderGroup}")

        return HttpResponseRedirect("registered/")
    else:
        current_semester = semester_year()
        # Get a Queryset of registered Courses
        user_registered_courses = UserCourses.objects.filter(semester_year=current_semester,
                                                             user_id=request.user.id).order_by("course")
        courses = []
        try:
            # exclude the courses from the display list which the user has already registered
            course_semester_id = Semesters.objects.filter(semester_longname=current_semester).values_list("semester_abbrev")[0]
            courses = Courses.objects.exclude(
                course_number__in=[c.course for c in user_registered_courses]).filter(
                course_semester_id=course_semester_id).order_by("course_number")
        except Exception as ex:
            logger.error("Exception: ", ex)
        if courses is None or len(courses) == 0:
            courses = []
        return render(
            request,
            "../templates/courses.html",
            {"courses": courses, "current_semester": current_semester},
        )


# @login_required(login_url="/accounts/login/")
def registered_courses(request):
    current_semester = semester_year()
    courses = UserCourses.objects.filter(semester_year=current_semester, user_id=request.user.id).order_by("course")
    courses_list = []
    for idx in range(len(courses)):
        temp = {
            "course_number": courses[idx].course.course_number,
            "course_section": courses[idx].course.course_section,
            "course_name": courses[idx].course.course_name,
            "course_instructor": courses[idx].course.course_instructor,
            "course_notes": courses[idx].course.course_notes,
        }
        courses_list.append(temp)
    return render(
        request,
        "../templates/registered_courses.html",
        {"current_semester": current_semester, "courses": courses_list},
    )


# @login_required(login_url="/accounts/login/")
def change_password(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = request.user.username
            password = request.POST["new_password1"]
            change_ldap_password(user, password)
            user = form.save()
            update_session_auth_hash(request, user)  # Important! (To keep the user logged in)
            # messages.success(request, 'Your password was successfully updated!')
            return render(request, '../templates/registration/change_password_complete.html')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = SetPasswordForm(request.user)
    return render(request, '../templates/registration/change_password.html', {
        'form': form
    })

def about_us(request):
    return render(request, "../templates/about_us.html")

def faq(request):
    faqs=Faq.objects.all()
    return render(request, "../templates/faq.html",{'faqs':faqs})


def admin_view(request):
    form = AdminView()
    return render(request, "../templates/admin_view.html", {"form": form})