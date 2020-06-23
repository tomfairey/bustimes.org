# Generated by Django 3.0.7 on 2020-06-23 15:33

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('busstops', '0003_auto_20200615_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasource',
            name='settings',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
