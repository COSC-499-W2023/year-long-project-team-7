import os
from django import forms
from django.forms import Textarea, NumberInput, RadioSelect, TextInput, Select
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from .models import *


class TransformerForm(forms.Form):
    def __init__(self, *args, **kwargs):  # type: ignore
        super(TransformerForm, self).__init__(*args, **kwargs)
        self.fields["complexity"].initial = 3
        self.fields["num_slides"].initial = 10
        self.fields["image_frequency"].initial = 3

    model = forms.ChoiceField(
        label="Model",
        choices=ModelChoice.choices,
        widget=forms.Select(attrs={"class": "form-control dropdown"}),
    )

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
        choices=LanguageChoice.choices,
        widget=forms.Select(
            attrs={
                "class": "form-control dropdown",
                "aria-label": "Presentation language selection",
            }
        ),
    )

    tone = forms.ChoiceField(
        label="Tone",
        choices=ToneChoice.choices,
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

    template = forms.ChoiceField(
        label="Templates",
        choices=TemplateChoice.choices,
        widget=RadioSelect(),
        required=False,
    )


class RegisterForm(UserCreationForm):  # type: ignore
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control form-control-lg"}),
        required=True,
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg"}),
        required=True,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg"}),
        required=True,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):  # type: ignore
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def save(self, commit=True):  # type: ignore
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
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

    def clean_image(self):  # type: ignore
        image = self.cleaned_data.get("image")
        if image:  # Proceed if there's an image
            valid_extensions = [".jpg", ".jpeg", ".png"]
            # Check file extension
            ext = os.path.splitext(image.name)[1]
            if ext.lower() not in valid_extensions:
                raise ValidationError(_("Unsupported file extension."))
            # Define max file size
            max_size = 5 * 1024 * 1024
            if image.size > max_size:
                raise ValidationError(_("Please keep filesize under 5MB."))
        return image


class AccountDeletionForm(forms.Form):
    confirm_delete = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class SubscriptionDeletionForm(forms.Form):
    delete = forms.BooleanField(
        label="Confirm Delete",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class RepromptForm(forms.Form):
    def __init__(self, *args, num_slides: int, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)
        slide_choices = [(str(i), str(i)) for i in range(1, num_slides + 1)]
        self.fields["slide"] = forms.ChoiceField(
            choices=slide_choices, label="Slide", initial="1"
        )

    prompt = forms.CharField(required=False, max_length=100, label="Prompt")
    image_slide = forms.BooleanField(required=False, label="Image Slide")

    def clean_prompt(self):
        prompt = self.cleaned_data.get("prompt")
        if not prompt:
            raise forms.ValidationError("The prompt field is required.")
        return prompt

    def clean_slide(self):
        slide = self.cleaned_data.get("slide")
        if not slide:
            raise forms.ValidationError("The slide number is required.")
        return slide


# converts reset email from plain text to html
class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(  # type: ignore
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject = render_to_string(subject_template_name, context)
        # Email subject must not contain newlines
        subject = "".join(subject.splitlines())
        body = render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        email_message.send()
