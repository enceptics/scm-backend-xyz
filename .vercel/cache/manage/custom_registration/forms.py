# forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import CustomUser, UserProfile
from logistics.models import CollateralManager
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse_lazy

from django.contrib.auth.forms import AuthenticationForm

from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.forms import UserCreationForm

class CustomLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('password', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Login')
        )

class CustomUserRegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser  # Replace CustomUser with your actual user model
        fields = ['username', 'email', 'password']  # Add more fields as needed for registration

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Register'))

class CustomPasswordResetForm(PasswordResetForm):
    def save(self, domain_override=None,
             subject_template_name='auth/password_reset_subject.txt',
             email_template_name='auth/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None, extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        active_users = CustomUser._default_manager.filter(
            email__iexact=email, is_active=True)
        for user in active_users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_url = reverse_lazy(
                'password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            context = {
                'protocol': 'https' if use_https else 'http',
                'domain': domain_override,
                'uid': uid,
                'token': token,
                'user': user,
                'reset_url': reset_url,
            }
            if extra_email_context is not None:
                context.update(extra_email_context)
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                email, html_email_template_name=html_email_template_name,
            )


class BuyerRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'address', 'country']

class BreederRegistrationForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'market', 'community', 'address', 'bank_account_number', 'id_number', 'head_of_family']

class SellerRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'address', 'id_number', 'county', 'country']

class BankRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'email', 'phone_number', 'address', 'county', 'country', 'location']

class SlaughterHouseRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'address', 'id_number', 'county', 'country']

class ExportManagerRegistrationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'address', 'id_number', 'county', 'country']

class CollateralManagerRegistrationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'address', 'id_number', 'county', 'country', 'bank_branch']

class InventoryManagerRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'address', 'id_number', 'county', 'country']

class CollateralManagerForm(forms.Form):
    collateral_manager = forms.ModelChoiceField(queryset=CollateralManager.objects.all(), empty_label="Select a Collateral Manager")

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']  # Add other fields from UserProfile model as needed