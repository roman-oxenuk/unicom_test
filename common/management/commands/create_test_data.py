# encoding: utf-8
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from lenders.models import Lender, Offer
from partners.models import Customer, Partner


class Command(BaseCommand):
    help = 'Create test data'

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.filter(username='Partner 1').exists():
            self.stdout.write(self.style.NOTICE('Похоже, что тестовые данные уже созданы.'))
            return

        partners_grp = Group.objects.get(name='Партнёры')
        lenders_grp = Group.objects.get(name='Кредитные организации')

        # Партнёры
        user1_partner = User.objects.create_user(username='Partner 1', password='user1_partner')
        Partner.objects.create(user=user1_partner, name='М-Видео')
        partners_grp.user_set.add(user1_partner)

        user2_partner = User.objects.create_user(username='Partner 2', password='user2_partner')
        Partner.objects.create(user=user2_partner, name='Евросеть')
        partners_grp.user_set.add(user2_partner)

        # Кредитные организации
        user3_lender = User.objects.create_user(username='Lender 1', password='user3_lender')
        Lender.objects.create(user=user3_lender, name='СберБанк')
        lenders_grp.user_set.add(user3_lender)

        user4_lender = User.objects.create_user(username='Lender 2', password='user4_lender')
        Lender.objects.create(user=user4_lender, name='ВТБ')
        lenders_grp.user_set.add(user4_lender)

        # Анкеты клиетнов
        Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=user1_partner.partner,
        )
        Customer.objects.create(
            surname='Ульянова', name='Мария', patronymic='Алексеевна',
            birth_date='1992-01-01', phone_number='89117310102', passport_number='1901432711',
            credit_score=18, partner=user1_partner.partner,
        )
        Customer.objects.create(
            surname='Овчинников', name='Алексей', patronymic='Александрович',
            birth_date='1983-01-01', phone_number='89117310505', passport_number='1901432700',
            credit_score=25, partner=user1_partner.partner,
        )

        Customer.objects.create(
            surname='Баушев', name='Илья', patronymic='Васильевич',
            birth_date='1993-01-01', phone_number='89117310005', passport_number='1901430000',
            credit_score=4, partner=user2_partner.partner,
        )
        Customer.objects.create(
            surname='Васильев', name='Андрей', patronymic='Владиславович',
            birth_date='1985-01-01', phone_number='89234234242', passport_number='1900432776',
            credit_score=15, partner=user2_partner.partner,
        )
        Customer.objects.create(
            surname='Захаров', name='Максим', patronymic='Александрович',
            birth_date='1987-09-18', phone_number='89032342349', passport_number='1901430022',
            credit_score=17, partner=user2_partner.partner,
        )

        # Предложения
        Offer.objects.create(
            name='Кредит простой', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=10, max_credit_score=20,
            lender=user3_lender.lender
        )
        Offer.objects.create(
            name='Кредит сложный', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=15, max_credit_score=25,
            lender=user3_lender.lender
        )
        Offer.objects.create(
            name='Основой кредит', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=12, max_credit_score=32,
            lender=user4_lender.lender
        )
        Offer.objects.create(
            name='Автокредит', offer_type=Offer.CARLOAN,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=17, max_credit_score=22,
            lender=user4_lender.lender
        )
        # Неактуальное предложение
        Offer.objects.create(
            name='Неактуальное предложение', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(months=1),
            rotating_end=datetime.now() - relativedelta(days=1),
            min_credit_score=5, max_credit_score=25,
            lender=user3_lender.lender
        )

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы.'))
