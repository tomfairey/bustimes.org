# Generated by Django 2.2.10 on 2020-02-29 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0025_auto_20200209_1813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='livery',
            name='name',
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
