import re
from django.utils.translation import ngettext
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


class MinimumLengthValidator:
    """
    Validate whether the password is of a minimum length.
    """

    def __init__(self, min_length=10, max_length=16):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                ngettext(
                    "This password is too short. It must contain at least %(min_length)d character.",
                    "This password is too short. It must contain at least %(min_length)d characters.",
                    self.min_length
                ),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
        elif len(password) > self.max_length:
            raise ValidationError(
                ngettext(
                    "This password is too long. It must contain at least %(max_length)d character.",
                    "This password is too short. It must contain at least %(max_length)d characters.",
                    self.max_length
                ),
                code='password_too_long',
                params={'max_length': self.max_length},
            )

    def get_help_text(self):
        return _(
            f"Password must be between {self.min_length} and {self.max_length} characters."
        )


class NumberValidator(object):
    def __init__(self, min_digits=1):
        self.min_digits = min_digits

    def validate(self, password, user=None):
        if not len(re.findall('\d', password)) >= self.min_digits:
            raise ValidationError(
                _("Password must have at least %(min_digits)d numerical digits." % {'min_digits': self.min_digits}),
                code='password_no_number',
                params={'min_digits': self.min_digits},
            )

    def get_help_text(self):
        return _(
            "Password must have at least %(min_digits)d numerical digits." % {'min_digits': self.min_digits}
        )


class UppercaseValidator(object):
    def __init__(self, min_digits=1):
        self.min_digits = min_digits

    def validate(self, password, user=None):
        if not len(re.findall('[A-Z]', password)) >= self.min_digits:
            raise ValidationError(
                _("Password must have at least one uppercase letters"),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _(
            "Password must have at least one uppercase letters"
        )


class LowercaseValidator(object):
    def __init__(self, min_digits=1):
        self.min_digits = min_digits

    def validate(self, password, user=None):
        if not len(re.findall('[a-z]', password)) >= self.min_digits:
            raise ValidationError(
                _("Password must have at least one lowercase letters"),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _(
            "Password must have at least one lowercase letters"
        )


class SymbolValidator(object):
    def __init__(self, min_digits=1):
        self.min_digits = min_digits

    def validate(self, password, user=None):
        if not len(re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', password)) >= self.min_digits:
            raise ValidationError(
                _("Password must have at least 1 special symbols: " +
                  "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Password must have at least 1 special symbols: " +
            "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"
        )