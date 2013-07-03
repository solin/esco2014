from django import forms

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from django.core.exceptions import ObjectDoesNotExist

from conference.contrib.captcha import CaptchaField
from conference.settings import MIN_PASSWORD_LEN, CHECK_STRENGTH

class LoginForm(forms.Form):
    """Form for logging in users. """

    username = forms.CharField(
        required  = True,
        label     = "Login",
    )

    password = forms.CharField(
        required  = True,
        label     = "Password",
        widget    = forms.PasswordInput(),
    )

    def clean(self):
        """Authenticate and login user, if possible. """
        cleaned_data = self.cleaned_data

        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            self.user = authenticate(username=username, # XXX: actually email
                                     password=password)

            if self.user is not None:
                if self.user.is_active:
                    return cleaned_data
                else:
                    raise forms.ValidationError('Your account was disabled.')

        raise forms.ValidationError('Incorrect login name or password. Please try again.')

class ReminderForm(forms.Form):
    """Password reminder form. """

    username = forms.CharField(
        required = True,
        label    = "Login",
    )
    captcha = CaptchaField(
        required = True,
        label    = "Security Code",
    )

    def clean_username(self):
        """Make sure that `username` is registred in the system. """
        username = self.cleaned_data['username']

        try:
            User.objects.get(email=username)
        except ObjectDoesNotExist:
            raise forms.ValidationError('Selected user does not exist.')

        return username

_digit = set(map(chr, range(48, 58)))
_upper = set(map(chr, range(65, 91)))
_lower = set(map(chr, range(97,123)))


class RegistrationForm(forms.Form):
    """Form for creating new users. """

    username = forms.EmailField(
        required   = True,
        label      = "E-mail",
        help_text  = "This will be your login name.",
    )
    username_again = forms.EmailField(
        required   = True,
        label      = "E-mail (again)",
        help_text  = "Make sure that this is a valid E-mail address.",
    )

    password = forms.CharField(
        required   = True,
        label      = "Password",
        widget     = forms.PasswordInput(),
        help_text  = "Use lower and upper case letters, numbers, etc.",
    )
    password_again = forms.CharField(
        required   = True,
        label      = "Password (again)",
        widget     = forms.PasswordInput(),
    )

    first_name = forms.CharField(
        required   = True,
        label      = "First Name",
        help_text  = "Enter your first name + middle name.",
    )

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        
        all_symbols = set(first_name)
        first_symbol = set(first_name[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')

        elif not ( all_symbols & _lower ):
            raise forms.ValidationError('Only CAPITALS are not allowed.')

        elif ( all_symbols & _digit ):
            raise forms.ValidationError('Digits are not allowed in first name.')

        return first_name

    last_name = forms.CharField(
        required   = True,
        label      = "Last Name",
        help_text  = "Enter your last name.",
    )

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        
        all_symbols = set(last_name)
        first_symbol = set(last_name[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')
                 
        elif not ( all_symbols & _lower ):
            raise forms.ValidationError('Only CAPITALS are not allowed.')

        elif ( all_symbols & _digit ):
            raise forms.ValidationError('Digits are not allowed in last name.')

        return last_name

    captcha = CaptchaField(
        required   = True,
        label      = "Security Code",
    )

    def clean_username(self):
        """Make sure that `login` is unique in the system. """
        username = self.cleaned_data['username']

        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username

        raise forms.ValidationError('Login name already in use.')

    def clean_username_again(self):
        """Make sure that user verified `login` that he entered. """
        if 'username' in self.cleaned_data:
            username       = self.cleaned_data['username']
            username_again = self.cleaned_data['username_again']

            if username == username_again:
                return username
        else:
            return None

        raise forms.ValidationError('Login names do not match.')

    def clean_password(self):
        """Make sure `password` isn't too easy to break. """
        password = self.cleaned_data['password']

        if CHECK_STRENGTH:
            if len(password) < MIN_PASSWORD_LEN:
                raise forms.ValidationError('Password must have at least %i characters.' % MIN_PASSWORD_LEN)

            symbols = set(password)

            if not ((_digit & symbols and _upper & symbols) or \
                    (_digit & symbols and _lower & symbols) or \
                    (_lower & symbols and _upper & symbols)):
                raise forms.ValidationError('Password is too weak, please choose a better one.')

        return password

    def clean_password_again(self):
        """Make sure that the user verified the `password` he entered. """
        if 'password' in self.cleaned_data:
            password       = self.cleaned_data['password']
            password_again = self.cleaned_data['password_again']

            if password == password_again:
                return password
        else:
            return None

        raise forms.ValidationError('Passwords do not match.')

class ChangePasswordForm(forms.Form):
    """Password change form for authenticated users. """

    password_new = forms.CharField(
        required   = True,
        label      = "New Password",
        widget     = forms.PasswordInput(),
        help_text  = "Use lower and upper case letters, numbers, etc.",
    )

    password_new_again = forms.CharField(
        required   = True,
        label      = "New Password (again)",
        widget     = forms.PasswordInput(),
    )

    def clean_password_new(self):
        """Make sure `password_new` isn't too easy to break. """
        password_new = self.cleaned_data['password_new']

        if CHECK_STRENGTH:
            if len(password_new) < MIN_PASSWORD_LEN:
                raise forms.ValidationError('Password must have at least %i characters.' % MIN_PASSWORD_LEN)

            symbols = set(password_new)

            if not ((_digit & symbols and _upper & symbols) or \
                    (_digit & symbols and _lower & symbols) or \
                    (_lower & symbols and _upper & symbols)):
                raise forms.ValidationError('Password is too weak, please enter a better one.')

        return password_new

    def clean_password_new_again(self):
        """Make sure user verified `password` he entered. """
        if 'password_new' in self.cleaned_data:
            password_new       = self.cleaned_data['password_new']
            password_new_again = self.cleaned_data['password_new_again']

            if password_new == password_new_again:
                return password_new
        else:
            return None

        raise forms.ValidationError('Passwords do not match.')

class UserProfileForm(forms.Form):
    """User profile form. """

    first_name = forms.CharField(
        required  = True,
        label     = "First Name",
        help_text = "Enter your first name + middle names.",
    )

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        
        all_symbols = set(first_name)
        first_symbol = set(first_name[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')

        elif not ( all_symbols & _lower ):
            raise forms.ValidationError('Only CAPITALS are not allowed.')

        elif ( all_symbols & _digit ):
            raise forms.ValidationError('Digits are not allowed in first name.')

        return first_name

    last_name = forms.CharField(
        required  = True,
        label     = "Last Name",
        help_text = "Enter your last name.",
    )

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        
        all_symbols = set(last_name)
        first_symbol = set(last_name[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')
                 
        elif not ( all_symbols & _lower ):
            raise forms.ValidationError('Only CAPITALS are not allowed.')

        elif ( all_symbols & _digit ):
            raise forms.ValidationError('Digits are not allowed in last name.')

        return last_name

    affiliation = forms.CharField(
        required  = True,
        label     = "Affiliation",
        help_text = "Your institution, in English (for example: Technical University of Munich)",
    )

    def clean_affiliation(self):
        affiliation = self.cleaned_data['affiliation']
        
        all_symbols = set(affiliation)
        first_symbol = set(affiliation[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')
                 
        elif ( all_symbols & _digit ):
            raise forms.ValidationError('Digits are not allowed in last name.')

        return affiliation

    address = forms.CharField(
        required  = True,
        label     = "Street Address",
        help_text = "",
    )

    def clean_address(self):
        address = self.cleaned_data['address']
        
        all_symbols = set(address)
        first_symbol = set(address[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')
                 
        elif not ( (all_symbols & _lower) or (all_symbols & _digit) ):
            raise forms.ValidationError('Only CAPITALS are not allowed.')

        return address

    city = forms.CharField(
        required  = True,
        label     = "City",
        help_text = "",
    )

    def clean_city(self):
        city = self.cleaned_data['city']
        
        all_symbols = set(city)
        first_symbol = set(city[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')
                 
        elif not ( (all_symbols & _lower) or (all_symbols & _digit) ):
            raise forms.ValidationError('Only CAPITALS are not allowed.')

        return city

    postal_code = forms.CharField(
        required  = True,
        label     = "Postal Code",
        help_text = "",
    )

    country = forms.CharField(
        required  = True,
        label     = "Country",
        help_text = "Enter the name of your country in English.",
    )

    def clean_country(self):
        country = self.cleaned_data['country']
        
        all_symbols = set(country)
        first_symbol = set(country[0])
        
        if ( first_symbol & _lower):
            raise forms.ValidationError('First letter must be Uppercase.')
                 
        elif ( all_symbols & _digit ):
            raise forms.ValidationError('Digits are not allowed in country field.')

        return country

    speaker = forms.ChoiceField(
        required  = True,
        label     = "Are you going to present a paper?",
        help_text = "Select 'Yes' to be able to upload an abstract.",
        choices   = [
            (1, 'Yes'),
            (0, 'No'),
        ],
        initial   = 0,
    )

    student = forms.ChoiceField(
        required  = True,
        label     = "Are you a student?",
        help_text = "If you choose 'Yes', you will need to send us your student ID.",
        choices   = [
            (1, 'Yes'),
            (0, 'No'),
        ],
        initial   = 0,
    )

    vegeterian = forms.ChoiceField(
        required  = True,
        label     = "Do you require vegetarian food?",
        help_text = "",
        choices   = [
            (1, 'Yes'),
            (0, 'No'),
        ],
        initial   = 0,
    )

    postconf = forms.ChoiceField(
        required  = True,
        label     = "Interested in post-conference program?",
        help_text = "",
        choices   = [
            (1, 'Yes'),
            (0, 'No'),
        ],
        initial   = 0,
    )

    arrival = forms.DateField(
        required  = True,
        label     = "Arrival Date",
        help_text = "MM/DD/YYYY, e.g., 05/19/2013",
        input_formats = [
            '%m/%d/%Y',      # '05/19/2013'
        ],
        error_messages = {
            'required': 'Enter arrival date, e.g., 05/19/2013',
            'invalid': 'Enter a valid arrival date, e.g., 05/19/2013',
        },
    )
    departure = forms.DateField(
        required  = True,
        label     = "Departure Date",
        help_text = "MM/DD/YYYY, e.g., 05/24/2013",
        input_formats = [
            '%m/%d/%Y',      # '05/24/2013'
        ],
        error_messages = {
            'required': 'Enter departure date, e.g., 05/24/2013',
            'invalid': 'Enter a valid departure date, e.g., 05/24/2013',
        },
    )

    accompanying = forms.IntegerField(
        required  = True,
        label     = "Number of accompanying persons",
        help_text = "",
        min_value = 0,
        initial   = 0,
    )

    tshirt = forms.ChoiceField(
        required  = True,
        label     = "T-Shirt Size",
        help_text = "",
        choices   = [
            ('S', 'S (small)'),
            ('M', 'M (medium)'),
            ('L', 'L (large)'),
            ('XL', 'XL (extra large)'),
            ('XXL', 'XXL (double extra large)'),
        ],
        initial   = 'M',
    )

