# Generated by Django 2.1 on 2018-08-04 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20180804_0659'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditcard',
            name='card_token',
            field=models.UUIDField(),
        ),
    ]