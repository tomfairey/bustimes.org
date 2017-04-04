# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-03 21:37
from __future__ import unicode_literals

import autoslug.fields
from django.utils.text import slugify
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('busstops', '0005_auto_20170315_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='locality',
            name='slug',
            field=autoslug.fields.AutoSlugField(default='', editable=True, populate_from='name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='operator',
            name='slug',
            field=autoslug.fields.AutoSlugField(default='', editable=True, populate_from='name'),
            preserve_default=False,
        ),
        migrations.RunPython(update_operator_slugs),
        migrations.AddField(
            model_name='service',
            name='slug',
            field=autoslug.fields.AutoSlugField(default='', editable=True, populate_from='description'),
            preserve_default=False,
        ),
    ]
