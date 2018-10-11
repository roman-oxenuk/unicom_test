# encoding: utf-8
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from rest_framework.test import APIClient

from applications.models import Application
from common.test_utils import (CreateInitialDataMixin, FiltersTestMixin,
                               OrderingTestMixin)
from lenders.models import Offer
from partners.models import Customer


class CustomersApiTestCase(CreateInitialDataMixin, FiltersTestMixin, OrderingTestMixin, TestCase):

    api_url = '/api/customers/'

    def test_customer_create(self):
        self.assertEqual(Customer.objects.all().count(), 0)

        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        # Партнёр может создавать новые Анкеты
        response = client_partner.post(
            self.api_url,
            {
                'surname': 'Иванов',
                'name': 'Пётр',
                'patronymic': 'Сергеевич',
                'birth_date': '1990-01-01',
                'phone_number': '89117310203',
                'passport_number': '1901432765',
                'credit_score': '10',
                'partner': self.user1_partner.partner.id
            },
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Customer.objects.all().count(), 1)
        self.assertEqual(Customer.objects.first().partner, self.user1_partner.partner)

        # Партнёр НЕ может создавать новые Анкеты от имени других партнёров
        response = client_partner.post(
            self.api_url,
            {
                'surname': 'Иванов',
                'name': 'Пётр',
                'patronymic': 'Сергеевич',
                'birth_date': '1990-01-01',
                'phone_number': '89117310203',
                'passport_number': '1901432765',
                'credit_score': '10',
                'partner': self.user2_partner.partner.id
            },
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Customer.objects.all().count(), 2)
        self.assertEqual(Customer.objects.first().partner, self.user1_partner.partner)

        # Кредитная организация НЕ может создавать новые Анкеты
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        response = client_lender.post(
            self.api_url,
            {
                'surname': 'Иванов',
                'name': 'Пётр',
                'patronymic': 'Сергеевич',
                'birth_date': '1990-01-01',
                'phone_number': '89117310203',
                'passport_number': '1901432765',
                'credit_score': '10',
                'partner': self.user2_partner.partner.id
            },
            format='json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Customer.objects.all().count(), 2)

    def test_customer_read_list(self):
        customer1 = Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=self.user1_partner.partner,
        )

        customer2 = Customer.objects.create(
            surname='Ульянова', name='Мария', patronymic='Алексеевна',
            birth_date='1992-01-01', phone_number='89117310102', passport_number='1901432711',
            credit_score=18, partner=self.user1_partner.partner,
        )

        customer3 = Customer.objects.create(
            surname='Овчинников', name='Алексей', patronymic='Александрович',
            birth_date='1983-01-01', phone_number='89117310505', passport_number='1901432700',
            credit_score=25, partner=self.user1_partner.partner,
        )

        customer4 = Customer.objects.create(
            surname='Баушев', name='Илья', patronymic='Васильевич',
            birth_date='1993-01-01', phone_number='89117310005', passport_number='1901430000',
            credit_score=4, partner=self.user2_partner.partner,
        )

        customer5 = Customer.objects.create(
            surname='Васильев', name='Андрей', patronymic='Владиславович',
            birth_date='1985-01-01', phone_number='89234234242', passport_number='1900432776',
            credit_score=15, partner=self.user2_partner.partner,
        )

        customer6 = Customer.objects.create(
            surname='Захаров', name='Максим', patronymic='Александрович',
            birth_date='1987-09-18', phone_number='89032342349', passport_number='1901430022',
            credit_score=17, partner=self.user2_partner.partner,
        )

        # Каждый Партнёр может получить список своих Анкет
        client_partner1 = APIClient()
        client_partner1.login(username=self.user1_partner.username, password='user1_partner')

        response = client_partner1.get(self.api_url)
        response_data = response.json()

        user1_expected_customers_ids = set([customer1.id, customer2.id, customer3.id])
        self.assertEqual(
            set([item['id'] for item in response_data]),
            user1_expected_customers_ids
        )

        client_partner2 = APIClient()
        client_partner2.login(username=self.user2_partner.username, password='user2_partner')
        response = client_partner2.get(self.api_url)
        response_data = response.json()

        user2_expected_customers_ids = set([customer4.id, customer5.id, customer6.id])
        self.assertEqual(
            set([item['id'] for item in response_data]),
            user2_expected_customers_ids
        )

        # Готовим Анкеты к тестированию фильтров
        user1_partner_customers = [customer1, customer2, customer3]
        customer1.created_at = datetime.now() - relativedelta(days=3)
        customer2.created_at = datetime.now() - relativedelta(days=2)
        customer3.created_at = datetime.now() - relativedelta(days=1)

        customer1.updated_at = datetime.now() - relativedelta(days=3) + relativedelta(hours=3)
        customer2.updated_at = datetime.now() - relativedelta(days=2) + relativedelta(hours=4)
        customer3.updated_at = datetime.now() - relativedelta(days=1) + relativedelta(hours=5)

        for customer in user1_partner_customers:
            customer.save()

        for customer in user1_partner_customers:
            customer.refresh_from_db()

        # Работают фильтры
        fields = {
            'created_at': ['lt', 'gt'],
            'updated_at': ['lt', 'gt'],
            'credit_score': ['lt', 'gt'],
            'birth_date': ['lt', 'gt'],
        }
        self.check_filter_field(user1_partner_customers, client_partner1, self.api_url, fields)

        # Работает сортировка
        ordering_fields = ('credit_score', 'created_at', 'updated_at', 'birth_date')
        self.check_ordering(user1_partner_customers, client_partner1, self.api_url, ordering_fields)

        # Кредитор НЕ может просматривать список Анкет
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        response = client_lender.get(self.api_url)
        self.assertEqual(response.status_code, 403)

    def test_customer_read_detail(self):
        customer1 = Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=self.user1_partner.partner,
        )
        customer2 = Customer.objects.create(
            surname='Ульянова', name='Мария', patronymic='Алексеевна',
            birth_date='1992-01-01', phone_number='89117310102', passport_number='1901432711',
            credit_score=18, partner=self.user2_partner.partner,
        )
        customer3 = Customer.objects.create(
            surname='Овчинников', name='Алексей', patronymic='Александрович',
            birth_date='1983-01-01', phone_number='89117310505', passport_number='1901432700',
            credit_score=20, partner=self.user2_partner.partner,
        )
        offer1 = Offer.objects.create(
            name='Предложение 1', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=1, max_credit_score=25,
            lender=self.user3_lender.lender
        )
        offer2 = Offer.objects.create(
            name='Предложение 2', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(months=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=5, max_credit_score=50,
            lender=self.user4_lender.lender
        )
        app1 = Application.objects.create(customer=customer1, lender_offer=offer1)
        app2 = Application.objects.create(customer=customer2, lender_offer=offer2)

        # Партнёр может просматривать свою Анкету
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=customer1.id)
        response = client_partner.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['id'], customer1.id)

        # Партнёр НЕ может просматривать чужую Анкету
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=customer2.id)
        response = client_partner.get(url)
        self.assertEqual(response.status_code, 404)

        # Кредитная организация может просматривать Анкету, от которой есть Заявка к своему Предложению
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=customer1.id)
        response = client_lender.get(url)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['id'], customer1.id)

        # Кредитная организация НЕ может просматривать Анкету, от которой нет Заявка к своему Предложению
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=customer3.id)
        response = client_lender.get(url)
        self.assertEqual(response.status_code, 404)

        # Кредитная организация НЕ может просматривать Анкету, от которой есть Заявка к чужому Предложению
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=customer2.id)
        response = client_lender.get(url)
        self.assertEqual(response.status_code, 404)

    def test_customer_update(self):
        # Партнёр НЕ может редактировать Анкеты
        customer = Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=self.user1_partner.partner,
        )
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=customer.id)
        response = client_partner.put(
            url,
            {
                'surname': 'Иванов',
                'name': 'Михаил',
                'patronymic': 'Сергеевич',
                'birth_date': '1990-01-01',
                'phone_number': '89117310203',
                'passport_number': '1901432765',
                'credit_score': '10',
                'partner': self.user1_partner.partner.id
            },
            format='json'
        )
        self.assertEqual(response.status_code, 405)
        customer.refresh_from_db()
        self.assertEqual(customer.surname, 'Иванов')
        self.assertEqual(customer.name, 'Пётр')
        self.assertEqual(customer.patronymic, 'Сергеевич')
        self.assertEqual(customer.birth_date, date(1990, 1, 1))
        self.assertEqual(customer.phone_number, '89117310203')
        self.assertEqual(customer.passport_number, '1901432765')
        self.assertEqual(customer.credit_score, 10)
        self.assertEqual(customer.partner, self.user1_partner.partner)

    def test_customer_delete(self):
        # Партнёр НЕ может удалять Анкеты
        customer = Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=self.user1_partner.partner,
        )
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=customer.id)
        response = client_partner.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Customer.objects.all().count(), 1)
