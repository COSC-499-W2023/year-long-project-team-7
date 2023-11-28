from django import forms
from django.forms import Textarea, NumberInput, RadioSelect, TextInput, Select
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
                "class": "form-control rounded",
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
        widget=forms.Select(attrs={"class": "form-control dropdown"}),
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
        widget=forms.Select(attrs={"class": "form-control dropdown"}),
    )

    complexity = forms.IntegerField(
        label="Complexity",
        widget=NumberInput(
            attrs={
                "type": "range",
                "min": 0,
                "max": 6,
                "class": "custom-slider",
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
            }
        ),
    )

    template = forms.ChoiceField(
        label="Templates",
        choices=[(1, "Template 1"), (2, "Template 2"), (3, "Template 3")],
        widget=RadioSelect(),
    )


class SignUpForm(UserCreationForm):  # type: ignore
    email = forms.EmailField(max_length=200, help_text="Required")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class SignInForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
