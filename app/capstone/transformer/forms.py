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


class SignUpForm(UserCreationForm):  # type: ignore
    email = forms.EmailField(max_length=200, help_text="Required")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class SignInForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
