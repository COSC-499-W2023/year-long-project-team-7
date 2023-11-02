from django import forms
from django.forms import TextInput, Select


class TransformerForm(forms.Form):
    text_input = forms.CharField(label="Prompt", widget=TextInput())
    language = forms.ChoiceField(
        choices=[("en", "English"), ("fr", "French"), ("es", "Spanish")],
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
