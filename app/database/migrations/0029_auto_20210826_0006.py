# Generated by Django 3.2 on 2021-08-26 00:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0028_rename_congress_id_congresstransaction_congress'),
    ]

    operations = [
        migrations.RenameField(
            model_name='congressportfolio',
            old_name='congress_id',
            new_name='congress',
        ),
        migrations.RenameField(
            model_name='congressportfolio',
            old_name='transaction_id',
            new_name='transaction',
        ),
    ]
