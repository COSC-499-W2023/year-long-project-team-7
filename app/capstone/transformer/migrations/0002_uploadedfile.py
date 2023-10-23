# Generated by Django 4.2.5 on 2023-10-12 13:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transformer", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UploadedFile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to="uploads/")),
            ],
        ),
    ]
