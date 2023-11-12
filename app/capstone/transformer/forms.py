from django import forms
from django.forms import TextInput, Select
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class TransformerForm(forms.Form):
    text_input = forms.CharField(label="Prompt", widget=TextInput())
    language = forms.ChoiceField(
        choices=[("English", "English"), ("French", "French"), ("Spanish", "Spanish")],
        widget=Select(),
    )
    complexity = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={"type": "range", "min": 0, "max": 100, "class": "custom-slider"}
        )
    )
    length = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={"type": "range", "min": 0, "max": 100, "class": "custom-slider"}
        )
    )


class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True, help_text="Required.")
    last_name = forms.CharField(max_length=30, required=True, help_text="Required.")
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text="Required. Enter a valid email address.",
    )
    model = User
    fields = ("username", "first_name", "last_name", "email", "password1", "password2")


class SignInForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
