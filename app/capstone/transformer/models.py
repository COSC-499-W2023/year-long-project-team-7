from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from django.contrib.auth.models import User
from PIL import Image
import os


class TemplateChoice(models.IntegerChoices):
    TEMPLATE_1 = 1, "Template 1"
    TEMPLATE_2 = 2, "Template 2"
    TEMPLATE_3 = 3, "Template 3"
    TEMPLATE_4 = 4, "Template 4"
    TEMPLATE_5 = 5, "Template 5"
    TEMPLATE_6 = 6, "Template 6"


class LanguageChoice(models.TextChoices):
    AUTO = "Auto", "Auto"
    ENGLISH = "English", "English"
    FRENCH = "French", "French"
    SPANISH = "Spanish", "Spanish"


class ToneChoice(models.TextChoices):
    AUTO = "Auto", "Auto"
    FUN = "Fun", "Fun"
    CREATIVE = "Creative", "Creative"
    CASUAL = "Casual", "Casual"
    PROFESSIONAL = "Professional", "Professional"
    FORMAL = "Formal", "Formal"


class ModelChoice(models.TextChoices):
    GPT_3_5 = "gpt-3.5-turbo-0125", "GPT-3.5"
    GPT_4 = "gpt-4-0125-preview", "GPT-4"


class ComplexityLevelChoice(models.IntegerChoices):
    VERY_BASIC = 0, "Very Basic"
    BASIC = 1, "Basic"
    MODERATE = 2, "Moderate"
    DEFAULT = 3, "Default"
    HIGHLY_ADVANCED = 4, "Highly Advanced"
    VERY_DETAILED = 5, "Very Detailed"
    EXTREMELY_DETAILED = 6, "Extremely Detailed"


class ImageFrequencyChoice(models.IntegerChoices):
    NONE = 0, "None"
    FEW = 1, "A Few"
    SOME = 2, "Some"
    DEFAULT = 3, "Default"
    MANY = 4, "Many"
    NUMEROUS = 5, "Numerous"
    LOTS = 6, "Lots"


class Conversion(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    prompt = models.TextField(default="")
    num_slides = models.IntegerField(default=10)

    template = models.ForeignKey(
        "File", null=True, on_delete=models.CASCADE, related_name="template_conversions"
    )
    language = models.CharField(
        max_length=50, choices=LanguageChoice.choices, default=LanguageChoice.AUTO
    )
    tone = models.CharField(
        max_length=50, choices=ToneChoice.choices, default=ToneChoice.AUTO
    )
    model = models.CharField(
        max_length=50, choices=ModelChoice.choices, default=ModelChoice.GPT_3_5
    )
    complexity = models.IntegerField(
        choices=ComplexityLevelChoice.choices, default=ComplexityLevelChoice.DEFAULT
    )
    image_frequency = models.IntegerField(
        choices=ImageFrequencyChoice.choices, default=ImageFrequencyChoice.DEFAULT
    )

    slides_contents = JSONField(default=dict)


class Exercise(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    prompt = models.TextField(default="")
    num_true_false = models.IntegerField(default=3)
    num_multiple_choice = models.IntegerField(default=3)
    num_short_ans = models.IntegerField(default=3)
    template = models.ForeignKey(
        "File", null=True, on_delete=models.CASCADE, related_name="template_exercise"
    )
    model = models.CharField(
        max_length=50, choices=ModelChoice.choices, default=ModelChoice.GPT_3_5
    )
    complexity = models.IntegerField(
        choices=ComplexityLevelChoice.choices, default=ComplexityLevelChoice.DEFAULT
    )
    language = models.CharField(
        max_length=50, choices=LanguageChoice.choices, default=LanguageChoice.AUTO
    )

    slides_contents = JSONField(default=dict)


class File(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    conversion = models.ForeignKey(Conversion, null=True, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, null=True, on_delete=models.CASCADE)
    is_output = models.BooleanField(default=False)
    is_input = models.BooleanField(default=False)
    type = models.TextField()
    file = models.FileField(upload_to="", max_length=500)


class Transaction(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()


class Product(models.Model):
    name = models.TextField()
    get_display_price_cents = models.IntegerField(
        default=0
    )  # stored in cents for stripe
    get_display_price = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.00
    )
    description = models.TextField()
    phrase = models.TextField()
    length_days = models.IntegerField(default=0)


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    has_subscription = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_premium = models.BooleanField(default=False)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default="default_pfp.jpg", upload_to="profile_pics")

    def __str__(self):
        return f"{self.user.username} Profile"

    # Override the save method of the model
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)  # Open image

        # resize image
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)  # Resize image
            img.save(self.image.path)  # Save it again and override the larger image

    def delete(self, *args, **kwargs):
        # Check if profile has an image other than the default
        if self.image.name not in ["", "default_pfp.jpg"]:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)  # Delete the image file
        super().delete(*args, **kwargs)
