# Generated by Django 2.1.1 on 2018-10-11 12:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('partners', '0001_initial'),
        ('lenders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.PositiveIntegerField(choices=[(1, 'Новая'), (2, 'Отправлена'), (3, 'Получена'), (4, 'Одобрено'), (5, 'Отказано'), (6, 'Выдано')], default=1, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата и время обновления')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='partners.Customer', verbose_name='Анкета клиента')),
                ('lender_offer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='lenders.Offer', verbose_name='Предложение кредитной организации')),
            ],
            options={
                'verbose_name': 'Заявка',
                'verbose_name_plural': 'Заявки',
            },
        ),
        migrations.AlterUniqueTogether(
            name='application',
            unique_together={('lender_offer', 'customer')},
        ),
    ]
