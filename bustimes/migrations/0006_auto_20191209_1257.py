# Generated by Django 2.2.8 on 2019-12-09 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bustimes', '0005_auto_20191209_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='route',
            name='line_brand',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
