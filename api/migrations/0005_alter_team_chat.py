# Generated by Django 5.1.5 on 2025-02-08 16:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_subtask_assigned_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='chat',
            field=models.OneToOneField(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='team', to='api.chat'),
        ),
    ]
