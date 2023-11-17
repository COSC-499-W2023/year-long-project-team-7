from django import forms
from django.forms import Textarea, NumberInput, RadioSelect


class TransformerForm(forms.Form):
    def __init__(self, *args, **kwargs):  # type: ignore
        super(TransformerForm, self).__init__(*args, **kwargs)
        self.fields["complexity"].initial = 3
        self.fields["num_slides"].initial = 10
        self.fields["num_images"].initial = 3

    prompt = forms.CharField(
        label="Prompt",
        widget=Textarea(
            attrs={
                "rows": 4,
                "cols": 40,
                "placeholder": "Enter your prompt here (optional)",
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
        label="Length",
        widget=NumberInput(
            attrs={
                "type": "range",
                "min": 1,
                "max": 40,
                "class": "custom-slider",
            }
        ),
    )

    num_images = forms.IntegerField(
        label="Number of Images",
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
        choices=[(1, "Template 1"), (2, "Template 2")],
        widget=RadioSelect(),
    )
