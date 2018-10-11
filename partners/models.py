# encoding: utf-8
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

from lenders.models import Offer


User = get_user_model()


class Partner(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Название партнёра', max_length=255)

    created_at = models.DateTimeField(verbose_name='Дата и время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата и время обновления', auto_now=True)

    class Meta:
        verbose_name = 'Партнёр'
        verbose_name_plural = 'Партнёры'

    def __str__(self):
        return self.name


class Customer(models.Model):

    # Режимы поиска подходящих Предложений для Анкеты клиента и создания соответствующих Заявок.
    OFFER_MATCHING_MODES = (
        ('manual', 'Вручную'),      # Заявки НЕ создаются автоматически в отложенной задаче,
                                    # их содаёт Партнёр сам через API.

        ('auto', 'Авто'),           # Партнёру запрещается создавать Заявки через API.
                                    # Заявки создаются ТОЛЬКО автоматически в отложенной задаче.
    )

    surname = models.CharField(verbose_name='Фамилия', max_length=255)
    name = models.CharField(verbose_name='Имя', max_length=255)
    patronymic = models.CharField(verbose_name='Отчество', max_length=255)

    birth_date = models.DateField(verbose_name='Дата рождения')
    phone_number = models.CharField(verbose_name='Номер телефона', max_length=255)
    passport_number = models.CharField(verbose_name='Номер паспорта', max_length=10)
    credit_score = models.PositiveIntegerField(verbose_name='Скоринговый балл', db_index=True)

    partner = models.ForeignKey(Partner, verbose_name='Партнёр', on_delete=models.PROTECT)

    # Поведение по умолчанию:
    # Создание Заявок происходит автоматически в отложенной задаче,
    # а так же Партнёр может сам создавать Заявки для данной Анкеты клиента через API.
    offer_matching_mode = ArrayField(
        models.CharField(choices=OFFER_MATCHING_MODES, max_length=10),
        size=2,
        verbose_name='Режим создания заявок',
        default=list(['manual', 'auto']),
        db_index=True
    )

    created_at = models.DateTimeField(verbose_name='Дата и время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата и время обновления', auto_now=True)

    class Meta:
        verbose_name = 'Анкета клиента'
        verbose_name_plural = 'Анкеты клиентов'

    def __str__(self):
        return '{0} {1} {2} ({3}) {4}'.format(
            self.surname, self.name, self.patronymic,
            self.credit_score, self.partner
        )

    def match_with_offers(self, lender=None, return_existed=False):
        """
        Сопоставляет Анкету клиента с имеющимися актуальными Предложениями.
        Для найденных подходящих Предложений создаёт Заявки, но НЕ сохраняет их в базу.
        За сохранение в БД отвечает код, вызывающий этот метод. Это помогает оптимизировать взаимодействие с БД.

        :param lender: lenders.Lender.
                       Если задано, то подходящие Предложения ищутся только у этой Кредитной организации.

        :param return_existed: boolean, по умолчанию False.
                               Если True, то кроме новых Заявок возвращает уже существующие у этой Анкеты Заявки.

        :return: если return_existed=False (значение по умлочанию), то
                 list of applications.Application, список новых не сохранённых в базу Заявок

                 если return_existed=True, то
                 (list of applications.Application, list of applications.Application),
                 список уже имеющихся у этой Анкеты Заявок и список новых не сохранённых в базу Заявок
        """
        from applications.models import Application     # Импортируем тут, иначе получается циклический импорт.
        new_applications = []

        existed_apps_qs = self.application_set.all()
        if lender:
            existed_apps_qs = existed_apps_qs.filter(lender_offer__lender=lender)

        existed_matched_offers_ids = [app.lender_offer_id for app in existed_apps_qs]

        matched_offers_qs = Offer.objects.filter(
            min_credit_score__lte=self.credit_score,
            max_credit_score__gte=self.credit_score,
            rotating_start__lte=datetime.now(),
            rotating_end__gte=datetime.now()
        ).exclude(
            pk__in=existed_matched_offers_ids
        )
        if lender:
            matched_offers_qs = matched_offers_qs.filter(lender=lender)

        for offer in matched_offers_qs:
            new_applications.append(
                Application(
                    customer=self,
                    lender_offer=offer
                )
            )

        if return_existed:
            return existed_apps_qs, new_applications

        return new_applications
