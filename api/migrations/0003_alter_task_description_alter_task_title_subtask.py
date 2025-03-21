# Generated by Django 5.1.5 on 2025-02-08 16:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_user_ip_addr_user_port'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='description',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='task',
            name='title',
            field=models.CharField(max_length=100),
        ),
        migrations.CreateModel(
            name='SubTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=300)),
                ('status', models.CharField(choices=[('to do', 'To Do'), ('in progress', 'In Progress'), ('completed', 'Completed')], default='to do', max_length=20)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('assigned_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subtasks', to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subtasks', to='api.task')),
            ],
        ),
    ]
