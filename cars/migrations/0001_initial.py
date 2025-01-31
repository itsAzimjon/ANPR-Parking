# Generated by Django 4.2.8 on 2023-12-13 10:15

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Car',
            fields=[
                ('id', models.UUIDField(default=uuid.UUID('0b27bcd6-0192-406d-b5ab-04a9e81ad499'), editable=False, primary_key=True, serialize=False)),
                ('number', models.CharField(max_length=8)),
                ('plate_image', models.ImageField(upload_to='plate_images')),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('finish_time', models.DateTimeField(blank=True, null=True)),
                ('price', models.FloatField(default=0)),
                ('active', models.BooleanField(default=True)),
                ('been', models.CharField(max_length=10)),
            ],
        ),
    ]
