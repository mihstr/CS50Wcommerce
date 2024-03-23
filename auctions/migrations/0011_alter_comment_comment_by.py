# Generated by Django 5.0.3 on 2024-03-21 15:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0010_comment_comment_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]