import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "capstone.settings_env")
django.setup()


from transformer.models import Conversion, File, Product, Subscription, Transaction, Profile
from django.contrib.auth.models import User


def main() -> None:
    Conversion.objects.all().delete()
    File.objects.all().delete()
    Transaction.objects.all().delete()
    Product.objects.all().delete()
    User.objects.all().delete()
    Profile.objects.all().delete()

    test_user = User.objects.create_user(
        username="user@email.com",
        email="user@email.com",
        password="password",
        is_active=True,
    )
    test_user.save()

    file_names = [
        "template_1.pptx",
        "template_2.pptx",
        "template_3.pptx",
        "template_4.pptx",
        "template_5.pptx",
        "template_6.pptx",
    ]

    for file_name in file_names:
        File(
            user=None,
            conversion=None,
            type="pptx",
            file=file_name,
            is_output=False,
            is_input=False,
        ).save()

    Product.objects.create(
        name="Daily Subscription",
        get_display_price_cents=99,
        get_display_price=0.99,
        description="Get access to Platonix for 1 day",
        phrase="Most Flexible!",
        length_days=1,
    ).save()

    Product.objects.create(
        name="Monthly Subscription",
        get_display_price_cents=499,
        get_display_price=4.99,
        description="Get access to Platonix for 1 month",
        phrase="Most Popular!",
        length_days=30,
    ).save()

    Product.objects.create(
        name="Premium Subscription",
        get_display_price_cents=999,
        get_display_price=9.99,
        length_days=30,
        phrase="Get access to Platonix for 1 month",
        description="Unlock the power of GPT-4!",
    ).save()

    Subscription.objects.create(
        user=test_user,
        has_subscription=True,
        start_date="2021-01-01",
        end_date="2100-01-31",
        is_premium=True,
    ).save()

    print("#####################################################")
    print("Seeding complete")
    print("#####################################################")


if __name__ == "__main__":
    main()