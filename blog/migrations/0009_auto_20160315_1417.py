# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-15 14:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_auto_20160315_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='data',
            name='source_location',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='image',
            name='source_location',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
