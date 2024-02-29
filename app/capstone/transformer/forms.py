from django import forms
from django.forms import Textarea, NumberInput, RadioSelect, TextInput, Select
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile


class TransformerForm(forms.Form):
    def __init__(self, *args, **kwargs):  # type: ignore
        super(TransformerForm, self).__init__(*args, **kwargs)
        self.fields["complexity"].initial = 3
        self.fields["num_slides"].initial = 10
        self.fields["image_frequency"].initial = 3

    prompt = forms.CharField(
        label="Prompt",
        required=False,
        widget=Textarea(
            attrs={
                "rows": 10,
                "cols": 40,
                "placeholder": "Enter your prompt here (optional)",
                "class": "form-control rounded custom-text-area",
                "aria-label": "Optional prompt text input",
            }
        ),
    )

    language = forms.ChoiceField(
        label="Language",
        choices=[
            ("Auto", "Auto"),
            ("English", "English"),
            ("French", "French"),
            ("Spanish", "Spanish"),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-control dropdown",
                "aria-label": "Presentation language selection",
            }
        ),
    )

    tone = forms.ChoiceField(
        label="Tone",
        choices=[
            ("Auto", "Auto"),
            ("Fun", "Fun"),
            ("Creative", "Creative"),
            ("Casual", "Casual"),
            ("Professional", "Professional"),
            ("Formal", "Formal"),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-control dropdown",
                "aria-label": "Presentation tone selection",
            }
        ),
    )

    complexity = forms.IntegerField(
        label="Complexity",
        widget=NumberInput(
            attrs={
                "type": "range",
                "min": 0,
                "max": 6,
                "class": "custom-slider",
                "aria-label": "Presentation information complexity selection",
            }
        ),
    )

    num_slides = forms.IntegerField(
        label="Number of Slides",
        widget=NumberInput(
            attrs={
                "type": "range",
                "min": 1,
                "max": 40,
                "class": "custom-slider",
                "aria-label": "Number of presentation slides",
            }
        ),
    )

    image_frequency = forms.IntegerField(
        label="Frequency of Images",
        widget=NumberInput(
            attrs={
                "type": "range",
                "min": 0,
                "max": 6,
                "class": "custom-slider",
                "aria-label": "Presentation image generation frequency",
            }
        ),
    )

    model = forms.ChoiceField(
        label="Model",
        choices=[
            ("gpt-3.5-turbo-1106", "GPT-3"),
            ("gpt-4-1106-preview", "GPT-4"),
        ],
        widget=forms.Select(attrs={"class": "form-control dropdown", "aria-label": "AI Model selection"}),
    )

    template = forms.ChoiceField(
        label="Templates",
        choices=[
            (1, "Template 1"),
            (2, "Template 2"),
            (3, "Template 3"),
            (4, "Template 4"),
            (5, "Template 5"),
            (6, "Template 6"),
        ],
        widget=RadioSelect(),
    )


class RegisterForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control form-control-lg", "aria-label": "Email"}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-lg", "aria-label": "Password"}
        ),
    )

    class Meta:
        model = User
        fields = ("email", "password")

    def clean_email(self):  # type: ignore
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def save(self, commit=True):  # type: ignore
        user = User()
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control form-control-lg", "aria-label": "Email"}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-lg", "aria-label": "Password"}
        ),
    )


class UpdateEmailForm(forms.ModelForm):  # type: ignore
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["email"]

    def clean_email(self):  # type: ignore
        new_email = self.cleaned_data.get("email")
        if not new_email:  # Add a check to ensure new_email is not None
            raise ValidationError("Email cannot be empty.")
        current_email = self.instance.email
        if User.objects.exclude(pk=self.instance.pk).filter(email=new_email).exists():
            raise ValidationError("This email address is already in use.")
        return new_email

    def save(self, commit: bool = True):  # type: ignore
        user = super(UpdateEmailForm, self).save(commit=False)
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UpdatePasswordForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = []  # type: ignore


class ProfileUpdateForm(forms.ModelForm):  # type: ignore
    class Meta:
        model = Profile
        fields = ["image"]


class AccountDeletionForm(forms.Form):
    confirm_delete = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

class SubscriptionDeletionForm(forms.Form):
    delete = forms.BooleanField(
        label = "Confirm Delete",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )