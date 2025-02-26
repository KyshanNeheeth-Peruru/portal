import hashlib
import subprocess
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import login, logout, get_user_model, authenticate, update_session_auth_hash
from apply.constants import ActionNames
from apply.forms import RegistrationForm, AdminView
from apply.helper import insert_courses_into_user_courses, semester_year, change_ldap_password, sem_name, get_client_ip
from apply.models import Courses, UserCourses, Semesters, Faq, Random, Misc, EmailVerificationToken
from apply.utils import token_generator
from apply.ldap_helper import LDAPHelper
from apply.remote_connect import RemoteConnect
from apply.ldap import LDAP
from django.db.models import Q
import paramiko
import environ
from django.db import IntegrityError
import re
import io
import csv
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
import secrets
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from django import forms
from django.db.models.functions import Lower, Upper, Concat, Substr, Length
from django.db.models import Value, CharField, Q, F, Func, Case, When
from django.db.models.functions import Concat

env = environ.Env()
environ.Env.read_env()

# Create your views here.

logger = logging.getLogger(__name__)

@login_required
def ip_address(request):
    ip = get_client_ip(request)
    if request.method == 'POST':
        try:
            cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-i', '/tmp/id_ed25519', 'root@pe15.cs.umb.edu',
                   'bash -c "/usr/bin/fail2ban-client unban {0}"'.format(ip)]
            res = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = res.communicate()
            if res.returncode == 0:
                logger.info(f"User: {request.user.username} Unbanned themselves. :: IP {ip}")
            else:
                logger.info(f"User: {request.user.username} IP is not banned. :: IP: {ip}")
        except Exception as e:
            logger.error(f"Error in IP_address: {e}")
    return render(request, '../templates/ip_address.html', {"ip": ip})

def deactivate_user(user):
    user.is_active = False
    user.save()


def create_ldap_user(request):
    user = {
        "userName": request["username"],
        "userPassword": request["pasw1"],
        "fullName": f"{request['firstname'].capitalize()} {request['lastname'].capitalize()}",
        "firstName": request["firstname"].capitalize(),
        "lastName": request["lastname"].capitalize(),
        "email": request["email"],
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


    
def send_verification_email(email,domain):
    uidb64 = urlsafe_base64_encode(force_bytes(email))
    token = secrets.token_urlsafe()  # Generates a secure random token
    token_hash = hashlib.sha256(f"{email}{token}".encode()).hexdigest()
    verification_token, created = EmailVerificationToken.objects.get_or_create(
        email=email,
        defaults={'token_hash': token_hash}  # Set the token_hash if creating a new record
    )
    
    if not created:
        # If the token already exists, update the token_hash
        verification_token.token_hash = token_hash
        verification_token.created_at = timezone.now()  # Update the timestamp
        verification_token.is_used = False  # Reset the used status
        verification_token.save()
    link = reverse("registration-form", kwargs={"uidb64": uidb64, "token": token})
    activity_url = f"http://{domain}{link}"
    print(activity_url)
    email_subject = ActionNames.RegisterLink
    email_body = f"Hi, please use this link to register :\n{activity_url}"
    email_msg = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email="noreply@cs.umb.edu",
        to=[email],
    )
    email_msg.send()
    logger.debug(f"Registraion link has been sent to {email}")
    
def send_password_reset_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = f"http://yourwebsite.com/reset_password/{uid}/{token}/"
    subject = 'Password Reset'
    message = f'Hi {user.username}, you can reset your password by clicking the following link: {reset_url}'
    from_email = 'noreply@cs.umb.edu'
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                user=User.objects.get(email=email)
                send_password_reset_email(user)
                messages.success(request, 'Password recovery email sent.')
                return render(request, '../templates/registration/password_reset_form.html')
            else:
                messages.error(request, 'No user found with this email address.')
                return render(request, '../templates/registration/password_reset_form.html')
        else:
            messages.error(request, 'Please enter valid email address.')
            return render(request, '../templates/registration/password_reset_form.html')
        
    return render(request, "../templates/registration/password_reset_form.html")



def register_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'A user already exists with this email.')
                return render(request, '../templates/registration/register_email.html')
            else:
                if not email.endswith("@umb.edu"):
                    messages.error(request, "Email must be from @umb.edu domain")
                    return render(request, "../templates/registration/register_email.html")
                domain = get_current_site(request).domain
                send_verification_email(email,domain)
                messages.success(request, f"Registraion link has been sent to {email}")
                return render(request, '../templates/registration/register_email.html')
            
        else:
            messages.error(request, 'Please enter valid email address.')
            return render(request, '../templates/registration/register_email.html')
        
    return render(request, "../templates/registration/register_email.html")

def register_view(request, uidb64,token):
    try:
        email = force_str(urlsafe_base64_decode(uidb64))
        
    except:
        email=None
    account_registration = (Misc.objects.get(setting='is_account_registration_enabled').value.lower()=="true")
    if account_registration!=True:
        return render(request, "../templates/registration/registration_disabled.html")
    if request.method == "POST":
        
        try:
            received_token_hash = hashlib.sha256(f"{email}{token}".encode()).hexdigest()
            verification_token = EmailVerificationToken.objects.get(email=email)
            if verification_token.token_hash == received_token_hash:
                if verification_token.is_used:
                    messages.error(request, "registration link has already been used.")
                    return redirect('register')
                
                username= request.POST['username']
                firstname= request.POST['firstname']
                lastname= request.POST['lastname']
                pasw1= request.POST['pasw1']
                pasw2= request.POST['pasw2']
                
                if User.objects.filter(username=username).exists():
                    messages.error(request, "A user with this username already exists. Please choose a different username.")
                    return render(request, "../templates/registration/register.html")
                
                users_with_same_name = User.objects.filter(first_name=firstname, last_name=lastname)
                if users_with_same_name.exists():
                    email_parts = email.split('@')
                    name_part = email_parts[0]
                    name_parts = name_part.split('.')
                    first_name = name_parts[0]
                    last_name = name_parts[1]
                    if last_name[-3:].isdigit():
                        last_name_nonum = last_name[:-3]
                        users_no_num_lastname = User.objects.filter(first_name=first_name, last_name=last_name_nonum)
                        firstname = first_name
                        lastname = last_name_nonum
                        if users_no_num_lastname.exists():
                            last_name=name_parts[1]
                            lastname=last_name
                        else:
                            last_name=last_name_nonum       
                if User.objects.filter(first_name=firstname, last_name=lastname).exists():
                    messages.error(request, "Another user is using the same first name and last name. Please contact email us to finish your registration process.")
                    return render(request, "../templates/registration/register.html")
                if User.objects.filter(email=email).exists():
                    messages.error(request, "A user already exists with this email.")
                    return render(request, "../templates/registration/register.html")
                if(pasw1!=pasw2):
                    messages.error(request,"Passwords dont match")
                    return render(request, "../templates/registration/register.html")
                else:
                    unix_name=username.lower()
                    if (len(unix_name) >= 3 and unix_name in pasw1) or (unix_name in pasw2):
                        messages.error(request, 'Password may not contain username.')
                        return render(request, "../templates/registration/register.html")
                    
                    if not username.isalnum():
                        messages.error(request, 'Username should be alphanumeric.')
                        return render(request, "../templates/registration/register.html")
                    
                    for char in username:
                        if char.isupper():
                            messages.error(request, 'Please use all lower case in username.')
                            return render(request, "../templates/registration/register.html")
                    
                    if (len(unix_name) < 3) or (len(unix_name) > 8) or (unix_name[0].isdigit()):
                        messages.error(request, 'Username must not start with a number and must be 3 to 8 characters long.')
                        return render(request, "../templates/registration/register.html")
                    
                    if (len(pasw1) <10):
                        messages.error(request, 'Password need to be more than 8 Characters.')
                        return render(request, "../templates/registration/register.html")
                        
                    categories = [
                        r'[A-Z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Uppercase letters
                        r'[a-z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Lowercase letters
                        r'\d',  # Digits
                        r'[\W_]',  # Special characters
                        r'[^\W\d_a-zA-Z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Unicode alphabetic characters
                    ]
                    
                    categories_present = sum(bool(re.search(pattern, pasw1)) for pattern in categories)
                    
                    if categories_present < 3:
                        messages.error(request, 'Password must include characters from at least 3 categories.')
                        return render(request, "../templates/registration/register.html")
                    
                    user = User.objects.create_user(username,email,pasw1)
                    user.first_name = firstname
                    user.last_name = lastname
                    user.save()
                    
                    
                    updated_request = {
                        "username": username,
                        "firstname": firstname,
                        "lastname": lastname,
                        "email": email,
                        "pasw1": pasw1,
                        "pasw2": pasw2,
                    }
                    create_ldap_user(updated_request)
                    user.refresh_from_db()
                    activate_user(user)
                    user_counter = Misc.objects.get(setting='users_registered_counter')
                    user_counter.value = str(int(user_counter.value) + 1)
                    user_counter.save()
                    verification_token.is_used = True
                    verification_token.save() 
                    messages.success(request, "Your account has been activated!")
                    return redirect('login')     
            else:
                messages.error(request, "Activation link is invalid.")
                return redirect('register')
        except EmailVerificationToken.DoesNotExist:
            messages.error(request, "Activation link is invalid.")
            return redirect('register')
    
    return render(request, "../templates/registration/register.html")

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user=None

    if user is not None:
        user.is_active = True
        user.save()
        activate_user(user)
        messages.success(request, "Account activated")
        return redirect('login')
    else:
        messages.error(request, "Activation invalid !")
        return redirect('login')
        
    return redirect('login')

def activate_user(user):
    user.is_active = True
    user.save()
    obj = LDAPHelper(**{"userName": user})
    obj.unlock_ldap_account()

def check_username_availability(request):
    username = request.GET.get('username', '')
    available = not User.objects.filter(username=username).exists()
    return JsonResponse({'available': available})


def forgot_pasw_view(request, uidb64,token):
    try:
        # uid = force_str(urlsafe_base64_decode(uidb64))
        # user = User.objects.get(pk=uid)
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except:
        user=None

    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        if new_password1 == new_password2:
            unix_name=user.username.lower()
            if (len(unix_name) >= 3 and unix_name in new_password1) or (unix_name in new_password1):
                messages.error(request, 'Password may not contain username.')
                return render(request, '../templates/registration/change_password.html')
            
            if (len(new_password1) <10):
                messages.error(request, 'Password need to be more than 8 Characters.')
                return render(request, '../templates/registration/change_password.html')
                
            categories = [
                r'[A-Z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Uppercase letters
                r'[a-z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Lowercase letters
                r'\d',  # Digits
                r'[\W_]',  # Special characters
                r'[^\W\d_a-zA-Z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Unicode alphabetic characters
            ]
            
            categories_present = sum(bool(re.search(pattern, new_password1)) for pattern in categories)
            
            if categories_present < 3:
                messages.error(request, 'Password must include characters from at least 3 categories.')
                return render(request, '../templates/registration/change_password.html')
            user.set_password(new_password1)
            change_ldap_password(user, new_password1)
            user.save()
            update_session_auth_hash(request, user)
            pasw_change_counter = Misc.objects.get(setting='password_change_counter')
            pasw_change_counter.value = str(int(pasw_change_counter.value) + 1)
            pasw_change_counter.save()
            messages.success(request,'Password successfully changed.')
            return redirect('login')
        else:
            messages.error(request,'Passwords dont match.')
            return render(request, '../templates/registration/change_password.html')
    return render(request, "../templates/registration/change_password.html")

def login_view(request):
    randomobj = Random.objects.exclude(alerts__isnull=True).exclude(alerts='').first()
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        logger.info(f"{username} attempted to log in.")
        if user is not None:
            login(request, user)
            logger.info(f"{username} to logged in successfully.")
            return redirect('courses_list')

        else:
            messages.error(request, "Username or password invalid")
            logger.info(f"{username} used incorrect username or password.")
            return redirect('login')
    if randomobj is not None:
        return render(request, "home.html", {"alertmsg": randomobj.alerts})
    return render(request, 'home.html')

@login_required
def courses_list_view(request):
    course_registration = (Misc.objects.get(setting='is_course_registration_enabled').value.lower()=="true")
    current_semester = Semesters.objects.filter(is_active=True).first()
    courses = Courses.objects.filter(course_semester=current_semester).order_by("course_number")
    #courses = Courses.objects.all()
    registered_courses = UserCourses.objects.filter(semester_year=current_semester, user=request.user)
    available_courses = Courses.objects.filter(course_semester=current_semester).exclude(id__in=registered_courses.values('course')).order_by("course_number")
    return render(request,"courses.html",{"courses": available_courses, "current_semester": current_semester, "course_registration": course_registration})

def logout_view(request):
    logout(request)
    logger.info(f"{request.user.username} logged out successfully.")
    messages.success(request,"Logged out")
    return redirect('login')

@login_required
def selected_courses(request):
    current_semester = Semesters.objects.filter(is_active=True).first()
    cur_sem_abbrev= current_semester.semester_abbrev
    semester_name=sem_name(cur_sem_abbrev)
    if request.method == "POST":
        selected_course_ids = request.POST.getlist('id')
        user = request.user
        userName = request.user.username #ldap
        obj = LDAPHelper(**{"userName": userName}) #ldap
        remote_connection = RemoteConnect() #ldap
        
        for course_id in selected_course_ids:
            course = Courses.objects.get(id=course_id)
            user_course_exists = UserCourses.objects.filter(user=user, course=course, semester_year=current_semester.semester_longname).exists()
            
            if not user_course_exists:
                user_course = UserCourses.objects.create(user=user, course=course, semester_year=current_semester.semester_longname, enrolled=True)
                selectedCourse = course.course_number
                selectedCourseSection = course.course_section
                prof_unix_name= course.prof_unix_name
                ldapCourseSection = f"{selectedCourse}-{selectedCourseSection}" #ldap
                graderGroup = f"{selectedCourse}-{selectedCourseSection}G" #ldap
                uid = obj.get_uid_number() #ldap
                obj.add_user_to_courses(ldapCourseSection) #ldap
                
                # print(f"sudo python3 /srv/course_directory-vk.py -user {userName} "
                #                               f"-course {selectedCourse} -sem {semester_name} "
                #                               f"-prof {prof_unix_name} -uid {uid} -graderGroup {graderGroup}")
                courses_counter = Misc.objects.get(setting='course_registered_counter')
                courses_counter.value = str(int(courses_counter.value) + 1)
                courses_counter.save()
                remote_connection.execute_command(f"sudo python3 /srv/course_directory-vk.py -user {userName} "
                                              f"-course {selectedCourse} -sem {semester_name} "
                                              f"-prof {prof_unix_name} -uid {uid} -graderGroup {graderGroup}")
            else:
                messages.error(request, f"You already have the course {course.course_number} :  {course.course_name}  for the current semester.")
        
        
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
    return render(request,"../templates/registered_courses.html",{"current_semester": current_semester, "courses": courses_list})
    
    

@login_required
def registered_courses(request):
    current_semester = Semesters.objects.filter(is_active=True).first()
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
    return render(request,"../templates/registered_courses.html",{"current_semester": current_semester, "courses": courses_list})


@login_required
def change_password(request):
    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        if new_password1 == new_password2:
            user = request.user
            unix_name=user.username.lower()
            if (len(unix_name) >= 3 and unix_name in new_password1) or (unix_name in new_password1):
                messages.error(request, 'Password may not contain username.')
                return render(request, '../templates/registration/change_password.html')
            
            if (len(new_password1) <8):
                messages.error(request, 'Password need to be more than 8 Characters.')
                return render(request, '../templates/registration/change_password.html')
                
            categories = [
                r'[A-Z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Uppercase letters
                r'[a-z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Lowercase letters
                r'\d',  # Digits
                r'[\W_]',  # Special characters
                r'[^\W\d_a-zA-Z\u00C0-\u02AF\u0370-\u1FFF\u2C00-\uD7FF]',  # Unicode alphabetic characters
            ]
            
            categories_present = sum(bool(re.search(pattern, new_password1)) for pattern in categories)
            
            if categories_present < 3:
                messages.error(request, 'Password must include characters from at least 3 categories.')
                return render(request, '../templates/registration/change_password.html')
            

            
            user.set_password(new_password1)
            change_ldap_password(user, new_password1)
            user.save()
            update_session_auth_hash(request, user)
            pasw_change_counter = Misc.objects.get(setting='password_change_counter')
            pasw_change_counter.value = str(int(pasw_change_counter.value) + 1)
            pasw_change_counter.save()
            messages.success(request,'Password successfully changed.')
            return render(request, '../templates/registration/change_password.html')
        else:
            messages.error(request,'Passwords dont match.')
            return render(request, '../templates/registration/change_password.html')
    return render(request, '../templates/registration/change_password.html')
    
def about_us(request):
    return render(request, "../templates/about_us.html")

@login_required
def printQuota(request):
    userName = request.user.username
    if request.method == 'POST':
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # ssh_client.connect('users.cs.umb.edu', username='kyshan', password='pasww')
            # stdin, stdout, stderr = ssh_client.exec_command('cd public_html/ && ls')
            host = env("REMOTE_HOST_d301")
            rem_user = env("REMOTE_USER")
            rem_pasw = env("REMOTE_PASSWORD")
            
            ssh_client.connect(host, 22, rem_user, rem_pasw)
            cmd = f'sudo /usr/local/bin/edpykota -L {userName}'
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            
            output = stdout.read().decode('utf-8')
            
            return render(request, "../templates/printQuota.html", {'output': output})
        except Exception as e:
            return render(request, "../templates/printQuota.html", {'error_message': str(e)})
        finally:
            ssh_client.close()
        
        
        return render(request, "../templates/printQuota.html",{"output":output})
    
    return render(request, "../templates/printQuota.html")

def faq(request):
    faqs=Faq.objects.all()
    return render(request, "../templates/faq.html",{'faqs':faqs})

@login_required
def lablist(request):
    sems = reversed(Semesters.objects.all())
    
    if request.method == 'POST':
        selected_sem = request.POST["selected_sem"]
        
        # Annotate the last name and first name with proper formatting
        allusers = User.objects.filter(
            Q(usercourses__course__course_semester__semester_longname=selected_sem) | Q(is_staff=True)
        ).distinct().annotate(
            # Check if the last three characters of the last name are digits, and remove them
            cleaned_last_name=Case(
                When(last_name__regex=r'\d{3}$', then=Substr('last_name', 1, Length('last_name') - 3)),  # Remove last 3 digits
                default=F('last_name'),
                output_field=CharField()
            ),
            formatted_last_name=Concat(
                Upper(Substr('cleaned_last_name', 1, 1)),  # Capitalize the first letter
                Lower(Substr('cleaned_last_name', 2)),     # Lowercase the rest
                output_field=CharField()
            ),
            formatted_first_name=Concat(
                Upper(Substr('first_name', 1, 1)),  # Capitalize the first letter
                Lower(Substr('first_name', 2)),     # Lowercase the rest
                output_field=CharField()
            )
        ).order_by('formatted_last_name', 'formatted_first_name')

        return render(request, "../templates/lab_list.html", {
            'sems': sems, 'selected_sem': selected_sem, 'lab_list': allusers
        })
    return render(request, "../templates/lab_list.html", {'sems': sems})

def admin_view(request):
    form = AdminView()
    return render(request, "../templates/admin_view.html", {"form": form})

def check_username(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            username = user.username
            messages.success(request, "Username found.")
            return render(request, "../templates/check_username.html", {'username': username})
        except User.DoesNotExist:
            messages.error(request, "Email does not exist.")
    
    return render(request, "../templates/check_username.html")

@login_required
def add_data(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            courses = [row for row in reader if len(row) >= 5]
            request.session['courses'] = courses
            return render(request, 'confirm_courses.html', {'courses': courses})
    else:
        form = CSVUploadForm()
    return render(request, 'add_data.html', {'form': form})


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()

@login_required
def confirm_add(request):
    cur_sem = Semesters.objects.filter(is_active=True).first()
    if request.method == 'POST':
        courses = request.session.get('courses', [])
        if cur_sem is not None:
            for course in courses:
                try:
                    Courses.objects.create(
                        course_number=course[0],
                        course_section=course[3],
                        course_name=course[2],
                        course_instructor=course[4],
                        prof_unix_name=course[5],
                        course_semester=cur_sem
                    )
                except IntegrityError:
                    messages.error(request, f'Duplicate entry for {course[0]} - Section : {course[3]} - {cur_sem.semester_longname}.')
                    return redirect('add_data')

            messages.success(request, 'Courses added to the database.')
        else:
            messages.error(request, 'Current semester is not set up properly.')

        del request.session['courses']
        return redirect('add_data')

@csrf_exempt
def unix2campus(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username')

            if username:
                try:
                    user = User.objects.get(username=username)
                    email = user.email
                    return HttpResponse(email, content_type="text/plain")
                except User.DoesNotExist:
                    return HttpResponse('User not found', status=404, content_type="text/plain")
            else:
                return HttpResponse('Username is required', status=400, content_type="text/plain")
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON format', status=400, content_type="text/plain")

    return HttpResponse('Invalid request method', status=400, content_type="text/plain")