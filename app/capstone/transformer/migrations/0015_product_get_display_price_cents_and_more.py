# Generated by Django 4.2.5 on 2024-01-14 05:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transformer", "0014_product_delete_products"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="get_display_price_cents",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="product",
            name="get_display_price",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
        ),
    ]
