# Generated by Django 3.2 on 2021-08-21 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0013_rename_stock_senate_ticker'),
    ]

    operations = [
        migrations.AddField(
            model_name='senate',
            name='owner',
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='senate',
            name='sale_type',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='senate',
            name='amount',
            field=models.CharField(max_length=500, null=True),
        ),
    ]
