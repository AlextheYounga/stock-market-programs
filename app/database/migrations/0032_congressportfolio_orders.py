# Generated by Django 3.2 on 2021-08-27 02:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0031_auto_20210826_0043'),
    ]

    operations = [
        migrations.AddField(
            model_name='congressportfolio',
            name='orders',
            field=models.JSONField(null=True),
        ),
    ]
