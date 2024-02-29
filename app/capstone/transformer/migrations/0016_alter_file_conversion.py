# Generated by Django 4.2.5 on 2024-02-23 21:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("transformer", "0015_alter_conversion_date_alter_file_date_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="conversion",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="transformer.conversion",
            ),
        ),
    ]
