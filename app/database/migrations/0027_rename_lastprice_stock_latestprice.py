# Generated by Django 3.2 on 2021-08-25 23:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0026_congressportfolio_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stock',
            old_name='lastPrice',
            new_name='latestPrice',
        ),
    ]
