import datetime
from apply.models import Courses, User, UserCourses
from apply.ldap_helper import LDAPHelper
from apply.ldap import LDAP
from django.core.mail import EmailMessage


def get_today_date():
    return datetime.datetime.today()


def semester_year():
    today = get_today_date()
    year = str(today.year)
    if 9 <= today.month <= 12:
        semester = "Fall"
    elif 1 <= today.month <= 4:
        semester = "Spring"
    else:
        semester = "Summer"
    return f"{semester} {year}"


def create_ldap_user(request):
    user = {
        "userName": request.POST["username"],
        "userPassword": request.POST["password2"],
        "fullName": f"{request.POST['first_name']} {request.POST['last_name']}",
        "firstName": request.POST["first_name"],
        "lastName": request.POST["last_name"],
        "email": request.POST["email"],
    }
    obj = LDAP(**user)
    obj.add_new_user()


def change_ldap_password(user, password):
    obj = LDAPHelper(**{"userName": user})
    obj.change_password(password)


def insert_courses_into_user_courses(user_id, course, semester, section, instructor):
    user = User.objects.get(id=user_id)
    courseObject = Courses.objects.get(course_number=course,
                                       course_semester=semester,
                                       course_section=section,
                                       course_instructor=instructor)
    userCourses = UserCourses(
        user=user, course=courseObject, semester_year=semester_year()
    )
    userCourses.save()
        

def send_email(user_name, subject, body, exception=""):
    # email_body = f"Hi {user.first_name} please use this link to verify the account\n {activity_url}"
    # user_email = request.POST.get("email")
    email = EmailMessage(
        subject=subject,
        body=f"{body} for user_name: {user_name}. \n {exception}",
        from_email="noreply@cs.umb.edu",
        to=["portal@cs.umb.edu"],
    )
    email.send()