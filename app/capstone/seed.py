import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "capstone.settings_env")
django.setup()


from transformer.models import Conversion, File, Product, Subscription, Transaction
from django.contrib.auth.models import User


def main() -> None:
    Conversion.objects.all().delete()
    File.objects.all().delete()
    Transaction.objects.all().delete()
    Product.objects.all().delete()
    User.objects.all().delete()

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
        name="Basic",
        get_display_price_cents=500,
        get_display_price=5.00,
        length_days=30,
        phrase="1 month",
        description="1 month of access to the service",
    ).save()

    Product.objects.create(
        name="Longer",
        get_display_price_cents=2500,
        get_display_price=25.00,
        length_days=180,
        phrase="6 month",
        description="6 months of access to the service",
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
