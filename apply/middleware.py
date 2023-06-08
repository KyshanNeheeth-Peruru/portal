from apply.helper import change_ldap_password
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode

UserModel = get_user_model()


def get_user(uidb64):
    try:
        # urlsafe_base64_decode() decodes to bytestring
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist, ValidationError):
        user = None
    return user


class MiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method == "POST" and "set-password" in request.path:
            uidb64 = request.path.split("/")[3]  # get the encoded uid from the request path
            user = get_user(uidb64)
            password = request.POST['new_password1']
            change_ldap_password(user, password)
        return response