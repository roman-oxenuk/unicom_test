# encoding: utf-8
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Lender(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(verbose_name='Название кредитной организации', max_length=255)

    created_at = models.DateTimeField(verbose_name='Дата и время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата и время обновления', auto_now=True)

    class Meta:
        verbose_name = 'Кредитная организация'
        verbose_name_plural = 'Кредитные организации'

    def __str__(self):
        return self.name


class Offer(models.Model):

    CONSUMER_CREDIT = 1
    MORTGAGE = 2
    CARLOAN = 3
    OFFER_TYPES = (
        (CONSUMER_CREDIT, 'Потребительский'),
        (MORTGAGE, 'Ипотека'),
        (CARLOAN, 'Автокредит'),
    )

    name = models.CharField(verbose_name='Название предложения', max_length=255)
    offer_type = models.PositiveIntegerField(verbose_name='Тип предложения', choices=OFFER_TYPES)

    rotating_start = models.DateTimeField(verbose_name='Начало ротации', db_index=True)
    rotating_end = models.DateTimeField(verbose_name='Конец ротации', db_index=True)

    min_credit_score = models.PositiveIntegerField(verbose_name='Минимальный скоринговый балл', db_index=True)
    max_credit_score = models.PositiveIntegerField(verbose_name='Максимальный скоринговый балл', db_index=True)

    lender = models.ForeignKey(Lender, verbose_name='Кредитная организация', on_delete=models.PROTECT)

    created_at = models.DateTimeField(verbose_name='Дата и время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата и время обновления', auto_now=True)

    class Meta:
        verbose_name = 'Предложение'
        verbose_name_plural = 'Предложения'

    def __str__(self):
        return '{name} {lender}'.format(name=self.name, lender=self.lender)
