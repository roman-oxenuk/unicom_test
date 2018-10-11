# encoding: utf-8
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from common.test_utils import CreateInitialDataMixin
from lenders.models import Offer


class OffersApiTestCase(CreateInitialDataMixin, TestCase):

    api_url = '/api/offers/'

    def test_offer_create(self):
        rotating_start = datetime.now() - relativedelta(months=1)
        rotating_start = rotating_start.strftime(settings.REST_FRAMEWORK['DATETIME_FORMAT'])

        rotating_end = datetime.now() - relativedelta(days=1)
        rotating_end = rotating_end.strftime(settings.REST_FRAMEWORK['DATETIME_FORMAT']),

        payload_data = {
            'name': 'Предложение 5',
            'offer_type': Offer.CONSUMER_CREDIT,
            'rotating_start': rotating_start,
            'rotating_end': rotating_end,
            'min_credit_score': 15,
            'max_credit_score': 20,
            'lender': self.user3_lender.lender.id
        }

        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        # Партнёр НЕ может создавать Предложения
        response = client_partner.post(self.api_url, payload_data)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Offer.objects.all().count(), 0)

        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        # Кредитная организация НЕ может создавать Предложения
        response = client_lender.post(self.api_url, payload_data)
        self.assertNotEqual(response.status_code, 201)
        self.assertEqual(Offer.objects.all().count(), 0)

    def test_offer_read_list(self):
        offer1 = Offer.objects.create(
            name='Предложение 1', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=10, max_credit_score=20,
            lender=self.user3_lender.lender
        )
        offer2 = Offer.objects.create(
            name='Предложение 2', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=15, max_credit_score=25,
            lender=self.user3_lender.lender
        )
        offer3 = Offer.objects.create(
            name='Предложение 3', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=12, max_credit_score=32,
            lender=self.user4_lender.lender
        )
        # Неактуальное предложение
        offer4 = Offer.objects.create(
            name='Предложение 4', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(months=1),
            rotating_end=datetime.now() - relativedelta(days=1),
            min_credit_score=15, max_credit_score=20,
            lender=self.user3_lender.lender
        )

        # Партнёр может просматривать все доступные Предложения
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')
        response = client_partner.get(self.api_url)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data), 3)

        self.assertEqual(
            set([item['id'] for item in response_data]),
            set([offer1.id, offer2.id, offer3.id])
        )

        # Кредитная организация НЕ может просматривать Предложения
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        response = client_lender.get(self.api_url)
        self.assertNotEqual(response.status_code, 200)

    def test_offer_read_detail(self):
        offer1 = Offer.objects.create(
            name='Предложение 1', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=10, max_credit_score=20,
            lender=self.user3_lender.lender
        )
        # Неактуальное предложение
        offer2 = Offer.objects.create(
            name='Предложение 2', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(months=1),
            rotating_end=datetime.now() - relativedelta(days=1),
            min_credit_score=15, max_credit_score=20,
            lender=self.user3_lender.lender
        )
        offer3 = Offer.objects.create(
            name='Предложение 3', offer_type=Offer.CARLOAN,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=5, max_credit_score=25,
            lender=self.user4_lender.lender
        )

        # Партнёр может детально просматривать актуальное Предложение
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=offer1.id)
        response = client_partner.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['id'], offer1.id)

        # Партнёр может детально просматривать неактуальное Предложение
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=offer2.id)
        response = client_partner.get(url)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['id'], offer2.id)

        # Кредитная организация может просматривать своё Предложение
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=offer1.id)
        response = client_lender.get(url)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['id'], offer1.id)

        # Кредитная организация НЕ может просматривать чужое Предложение
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=offer3.id)
        response = client_lender.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_offer_update(self):
        rotating_start = datetime.now() - relativedelta(days=1)
        rotating_end = datetime.now() + relativedelta(months=1)
        offer = Offer.objects.create(
            name='Предложение 1', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=rotating_start, rotating_end=rotating_end,
            min_credit_score=10, max_credit_score=20,
            lender=self.user3_lender.lender
        )
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        # Партнёр НЕ может редактировать Предложения
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=offer.id)
        response = client_partner.put(
            url,
            {
                'name': 'Предложение Новое',
                'offer_type': Offer.CARLOAN,
                'rotating_start': (datetime.now() - relativedelta(days=1)).strftime(settings.DATETIME_FORMAT),
                'rotating_end': (datetime.now() + relativedelta(months=1)).strftime(settings.DATETIME_FORMAT),
                'min_credit_score': 5,
                'max_credit_score': 25,
                'lender': self.user3_lender.lender.id
            },
            format='json'
        )
        self.assertEqual(response.status_code, 405)
        offer.refresh_from_db()
        self.assertEqual(offer.name, 'Предложение 1')
        self.assertEqual(offer.offer_type, Offer.CONSUMER_CREDIT)
        self.assertEqual(offer.rotating_start, rotating_start)
        self.assertEqual(offer.rotating_end, rotating_end)
        self.assertEqual(offer.min_credit_score, 10)
        self.assertEqual(offer.max_credit_score, 20)
        self.assertEqual(offer.lender, self.user3_lender.lender)

    def test_offer_delete(self):
        offer = Offer.objects.create(
            name='Предложение 1', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=10, max_credit_score=20,
            lender=self.user3_lender.lender
        )
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        # Партнёр НЕ может удалять Предложения
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=offer.id)
        response = client_partner.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Offer.objects.all().count(), 1)
