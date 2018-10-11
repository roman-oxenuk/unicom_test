# encoding: utf-8
from django.db import migrations


def add_user_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')

    Group.objects.create(name='Партнёры')
    Group.objects.create(name='Кредитные организации')


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.RunPython(add_user_groups)
    ]
