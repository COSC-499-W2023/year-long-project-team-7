import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "capstone.settings_env")
django.setup()


from transformer.models import Conversion, File, Products, Transaction
from django.contrib.auth.models import User


def main() -> None:
    Conversion.objects.all().delete()
    File.objects.all().delete()
    Transaction.objects.all().delete()
    Products.objects.all().delete()
    User.objects.all().delete()

    User.objects.create_user(
        username="user@email.com",
        email="user@email.com",
        password="password",
        is_active=True,
    ).save()

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

    print("#####################################################")
    print("Seeding complete")
    print("#####################################################")


if __name__ == "__main__":
    main()
