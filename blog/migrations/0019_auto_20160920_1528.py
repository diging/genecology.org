# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-09-20 15:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0018_auto_20160920_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalnotebook',
            name='external_id',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]