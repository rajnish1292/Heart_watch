# Generated by Django 3.2 on 2021-10-12 07:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heart_rate', '0002_ppg_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ppg_data',
            name='board',
        ),
    ]
