# encoding: utf-8
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from applications.models import Application
from lenders.models import Lender, Offer
from partners.models import Customer, Partner


User = get_user_model()


class CustomerModelTestCase(TestCase):

    def test_method_match_with_offers(self):
        partners_grp = Group.objects.get(name='Партнёры')
        lenders_grp = Group.objects.get(name='Кредитные организации')

        # Партнёр
        user1_partner = User.objects.create_user(username='Partner 1', password='user1_partner')
        partner = Partner.objects.create(user=user1_partner, name='М-Видео')
        partners_grp.user_set.add(user1_partner)
        user1_partner.refresh_from_db()

        # Кредитные организации
        user2_lender = User.objects.create_user(username='Lender 1', password='user2_lender')
        lender1 = Lender.objects.create(user=user2_lender, name='СберБанк')
        lenders_grp.user_set.add(user2_lender)

        user3_lender = User.objects.create_user(username='Lender 2', password='user3_lender')
        lender2 = Lender.objects.create(user=user3_lender, name='ВТБ')
        lenders_grp.user_set.add(user3_lender)

        # Анкета клиента
        customer1 = Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=partner,
        )

        Offer.objects.create(
            name='Предложение 1', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=1, max_credit_score=5, lender=lender1
        )
        Offer.objects.create(
            name='Предложение 2', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(months=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=7, max_credit_score=17, lender=lender1
        )
        Offer.objects.create(
            name='Предложение старое', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(months=2),
            rotating_end=datetime.now() - relativedelta(months=1),
            min_credit_score=7, max_credit_score=17, lender=lender1
        )
        Offer.objects.create(
            name='Предложение 3', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(months=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=1, max_credit_score=50, lender=lender2
        )

        self.assertEqual(Application.objects.all().count(), 0)
        applications = customer1.match_with_offers()

        self.assertEqual(len(applications), 2)
        self.assertEqual(
            set([app.lender_offer.name for app in applications]),
            set(['Предложение 2', 'Предложение 3'])
        )

        applications = customer1.match_with_offers(lender=lender1)
        self.assertEqual(len(applications), 1)
        self.assertEqual(
            set([app.lender_offer.name for app in applications]),
            set(['Предложение 2'])
        )

        Application.objects.bulk_create(applications)

        existed_apps_qs, new_applications = customer1.match_with_offers(return_existed=True)
        self.assertEqual(len(existed_apps_qs), 1)
        self.assertEqual(
            set([existed_app.lender_offer.name for existed_app in existed_apps_qs]),
            set(['Предложение 2'])
        )

        self.assertEqual(len(new_applications), 1)
        self.assertEqual(
            set([app.lender_offer.name for app in new_applications]),
            set(['Предложение 3'])
        )

        existed_apps_qs, new_applications = customer1.match_with_offers(lender=lender1, return_existed=True)
        self.assertEqual(len(existed_apps_qs), 1)
        self.assertEqual(len(new_applications), 0)
