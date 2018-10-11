# encoding: utf-8
from django.db import models

from lenders.models import Offer
from partners.models import Customer


class Application(models.Model):

    NEW = 1
    SENT = 2
    RECEIVED = 3
    APPROVED = 4
    REFUSED = 5
    FUNDED = 6

    STATUSES = (
        (NEW, 'Новая'),
        (SENT, 'Отправлена'),
        (RECEIVED, 'Получена'),
        (APPROVED, 'Одобрено'),
        (REFUSED, 'Отказано'),
        (FUNDED, 'Выдано'),
    )

    lender_offer = models.ForeignKey(Offer, verbose_name='Предложение кредитной организации', on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, verbose_name='Анкета клиента', on_delete=models.PROTECT)

    status = models.PositiveIntegerField(verbose_name='Статус', choices=STATUSES, default=NEW)

    created_at = models.DateTimeField(verbose_name='Дата и время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата и время обновления', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        unique_together = ('lender_offer', 'customer')

    def __str__(self):
        return '{0} | {1}'.format(self.customer, self.lender_offer)
