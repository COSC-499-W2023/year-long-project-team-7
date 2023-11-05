# Generated by Django 4.2.5 on 2023-10-12 15:18

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("transformer", "0003_delete_uploadedfile_remove_file_path_file_file_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="file",
            name="conversion",
            field=models.ForeignKey(
                default=0,
                on_delete=django.db.models.deletion.CASCADE,
                to="transformer.conversion",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="conversion",
            name="date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="file",
            name="file",
            field=models.FileField(upload_to="files/"),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="user",
            name="date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.DeleteModel(
            name="FileConversion",
        ),
    ]
