# Generated by Django 3.2 on 2021-08-20 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0007_rename_companyname_stocknews_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Senate',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=300, null=True)),
                ('last_name', models.CharField(max_length=300)),
                ('office', models.CharField(max_length=300, null=True)),
                ('link', models.TextField(null=True)),
                ('date', models.DateField()),
                ('transactions', models.JSONField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'senate',
            },
        ),
    ]
