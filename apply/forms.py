import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


def text_match(text):
    patterns = '^[a-z0-9]*$'
    if re.search(patterns, text):
        return True
    else:
        return False


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(label="UMB Email")
    # POSITION_CHOICES = (
    #     ("ugrad", "Undergraduate"),
    #     ("grad", "Graduate"),
    # )
    # position = forms.ChoiceField(choices=POSITION_CHOICES, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
            # "position",
        ]
        help_texts = {"username": "Username must be lowercase letters (a-z), numbers (0-9) and 3 to 8 characters long"}

    def clean_username(self):
        username = self.cleaned_data.get("username")
        length = len(username)
        if length < 3 or length > 8:
            raise forms.ValidationError("Username must be 3 to 8 characters long")
        if not text_match(username):
            raise forms.ValidationError("Username must be lowercase letters (a-z), numbers (0-9)")
        return username.lower()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if not password2 == password1:
            raise forms.ValidationError("Both passwords do not match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email")
        umb_domain = "umb.edu"
        email_domain = email.split("@")[1]
        # also need to check if the email in already in database
        if not email_domain == umb_domain:
            raise forms.ValidationError("Please use  `umb.edu` email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Entered email is already in use.")
        return email


ACTION_CHOICES = [
    ('lock', 'Lock'),
    ('unlock', 'UnLock'),
]


class AdminView(forms.Form):
    user_name = forms.CharField(max_length=20)
    action = forms.ChoiceField(required=True,
                               choices=ACTION_CHOICES)