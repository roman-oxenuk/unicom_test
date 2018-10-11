# encoding: utf-8
from datetime import datetime
from unittest import mock

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from applications.models import Application
from applications.tasks import match_customer_task
from common.test_utils import (CreateInitialDataMixin, FiltersTestMixin,
                               OrderingTestMixin)
from lenders.models import Offer
from partners.models import Customer


class ApplicationsApiTestCase(CreateInitialDataMixin, FiltersTestMixin, OrderingTestMixin, TestCase):

    api_url = '/api/applications/'

    def test_application_create_for_all_lenders(self):
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
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        match_customer_task.delay = mock.MagicMock()

        # Партнёр может создавать Заявки для своей Анкеты клиента во все Кредитные организации
        response = client_partner.post(
            self.api_url,
            {
                'customer_id': customer1.pk,
                'lender_id': 'all',
            }
        )
        self.assertEqual(response.status_code, 201)
        match_customer_task.delay.assert_called_once_with(customer1.pk)
        match_customer_task.delay.reset_mock()

        # Партнёр НЕ может создавать Заявки для чужой Анкеты клиента во все Кредитные организации
        response = client_partner.post(
            self.api_url,
            {
                'customer_id': customer2.pk,
                'lender_id': 'all',
            }
        )
        self.assertNotEqual(response.status_code, 200)
        match_customer_task.delay.assert_not_called()
        match_customer_task.delay.reset_mock()

        # Кредитор НЕ может создавать Заявку
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')
        response = client_lender.post(
            self.api_url,
            {
                'customer_id': customer1.pk,
                'lender_id': 'all',
            }
        )
        self.assertNotEqual(response.status_code, 200)
        match_customer_task.delay.assert_not_called()
        match_customer_task.delay.reset_mock()

        # Ошибка, если в качестве customer_id отправлена строка отличная от "all"
        response = client_partner.post(
            self.api_url,
            {
                'customer_id': customer2.pk,
                'lender_id': 'lal',
            }
        )
        self.assertNotEqual(response.status_code, 200)
        match_customer_task.delay.assert_not_called()
        match_customer_task.delay.reset_mock()

        # Партнёр НЕ может создавать Заявки на Анкету, у которой поле offer_matching_mode НЕ содержит значения manual
        customer1.offer_matching_mode = ['auto']
        customer1.save()

        response = client_partner.post(
            self.api_url,
            {
                'customer_id': customer1.pk,
                'lender_id': 'all',
            }
        )
        self.assertNotEqual(response.status_code, 200)
        match_customer_task.delay.assert_not_called()
        match_customer_task.delay.reset_mock()

    def test_application_create_for_certain_lender(self):
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
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        def fake_func(*args, **kwargs):
            if kwargs.get('return_existed', False):
                return ([], [])
            return []

        with mock.patch.object(Customer, 'match_with_offers') as match_with_offers_mock:
            match_with_offers_mock.side_effect = fake_func
            # Партнёр может создавать Заявки в конкретную организацию
            response = client_partner.post(
                self.api_url,
                {
                    'customer_id': customer1.pk,
                    'lender_id': self.user3_lender.lender.id
                }
            )
        self.assertEqual(response.status_code, 201)
        match_with_offers_mock.assert_called_once_with(self.user3_lender.lender, return_existed=True)

        with mock.patch.object(Customer, 'match_with_offers') as match_with_offers_mock:
            match_with_offers_mock.side_effect = fake_func
            # Партнёр НЕ может создавать Заявки для несуществующей Кредитной организации
            response = client_partner.post(
                self.api_url,
                {
                    'customer_id': customer1.pk,
                    'lender_id': self.user4_lender.lender.id + 10
                }
            )
        self.assertEqual(response.status_code, 404)
        match_with_offers_mock.assert_not_called()

        with mock.patch.object(Customer, 'match_with_offers') as match_with_offers_mock:
            match_with_offers_mock.side_effect = fake_func
            # Партнёр НЕ может создавать Заявки для несуществующей Анкеты клиента
            response = client_partner.post(
                self.api_url,
                {
                    'customer_id': customer2.pk + 10,
                    'lender_id': self.user3_lender.lender.id
                }
            )
        self.assertEqual(response.status_code, 404)
        match_with_offers_mock.assert_not_called()

        with mock.patch.object(Customer, 'match_with_offers') as match_with_offers_mock:
            match_with_offers_mock.side_effect = fake_func
            # Партнёр НЕ может создавать Заявки для чужой Анкеты клиента
            response = client_partner.post(
                self.api_url,
                {
                    'customer_id': customer2.pk,
                    'lender_id': self.user3_lender.lender.id
                }
            )
        self.assertNotEqual(response.status_code, 201)
        match_with_offers_mock.assert_not_called()

        customer1.offer_matching_mode = ['auto']
        customer1.save()
        with mock.patch.object(Customer, 'match_with_offers') as match_with_offers_mock:
            match_with_offers_mock.side_effect = fake_func
            # Партнёр НЕ может создавать Заявки на Анкету,
            # у которой поле offer_matching_mode НЕ содержит значения manual
            response = client_partner.post(
                self.api_url,
                {
                    'customer_id': customer1.pk,
                    'lender_id': 'all',
                }
            )
        self.assertNotEqual(response.status_code, 201)
        match_with_offers_mock.assert_not_called()

    def test_application_read(self):
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
        app2 = Application.objects.create(customer=customer1, lender_offer=offer2)
        app3 = Application.objects.create(customer=customer2, lender_offer=offer1)
        app4 = Application.objects.create(customer=customer2, lender_offer=offer2)
        app5 = Application.objects.create(customer=customer3, lender_offer=offer1)
        app6 = Application.objects.create(customer=customer3, lender_offer=offer2)

        # Партнёр может получать Заявки своих Анкет Клиентов
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        response = client_partner.get(self.api_url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(len(response_json), 4)

        customer1_url = reverse('customers_detail', kwargs={'pk': customer1.pk})
        customer2_url = reverse('customers_detail', kwargs={'pk': customer2.pk})
        app_customers_urls = [item['customer'] for item in response_json]
        for customer_url in app_customers_urls:
            self.assertTrue(
                customer_url.endswith(customer1_url) or customer_url.endswith(customer2_url)
            )

        # Кредитор может получать Заявки по своим Преложениям
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        response = client_lender.get(self.api_url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(len(response_json), 3)

        expexted_offer_url = reverse('offers_detail', kwargs={'pk': offer1.pk})
        offer_urls = [item['lender_offer'] for item in response_json]
        for offer_url in offer_urls:
            self.assertTrue(offer_url.endswith(expexted_offer_url))

        # Готовим Заявки к тестированию фильтров
        user3_lender_apps = [app1, app3, app5]
        app1.created_at = datetime.now() - relativedelta(days=3)
        app3.created_at = datetime.now() - relativedelta(days=2)
        app5.created_at = datetime.now() - relativedelta(days=1)

        app1.updated_at = datetime.now() - relativedelta(days=3) + relativedelta(hours=3)
        app3.updated_at = datetime.now() - relativedelta(days=2) + relativedelta(hours=4)
        app5.updated_at = datetime.now() - relativedelta(days=1) + relativedelta(hours=5)

        app1.status = Application.NEW
        app3.status = Application.RECEIVED
        app5.status = Application.REFUSED

        for app in user3_lender_apps:
            app.save()

        for app in user3_lender_apps:
            app.refresh_from_db()

        # Работают фильтры
        fields = {
            'created_at': ['lt', 'gt'],
            'updated_at': ['lt', 'gt'],
            'status': [''],     # Пустая строка имеет такое же значение, как 'exact'
        }
        self.check_filter_field(user3_lender_apps, client_lender, self.api_url, fields)

        # Работает сортировка
        ordering_fields = ('created_at', 'updated_at',)
        self.check_ordering(user3_lender_apps, client_lender, self.api_url, ordering_fields)

    def test_application_read_detail(self):
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
        app2 = Application.objects.create(customer=customer1, lender_offer=offer2)
        app3 = Application.objects.create(customer=customer2, lender_offer=offer1)
        app4 = Application.objects.create(customer=customer2, lender_offer=offer2)

        # Партнёр может детально просмотреть Заявку от своей Анкеты клиента
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app1.id)
        response = client_partner.get(url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json['id'], app1.pk)

        # Партнёр НЕ может детально просмотреть Заявку от чужой Анкеты клиента
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app3.id)
        response = client_partner.get(url)
        self.assertEqual(response.status_code, 404)

        # Кредитная организация может детально просмотреть Заявку от своего Предложение
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app1.id)
        response = client_lender.get(url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json['id'], app1.pk)

        # Кредитная организация НЕ может детально просмотреть Заявку от чужого Предложение
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app2.id)
        response = client_lender.get(url)
        self.assertEqual(response.status_code, 404)

    def test_application_update(self):
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
        app2 = Application.objects.create(customer=customer1, lender_offer=offer2)

        # Кредитная организация может изменить статус в Заявке к своему Предложению
        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app1.id)
        response = client_lender.patch(
            url,
            {'status': Application.APPROVED}
        )
        self.assertEqual(response.status_code, 200)
        app1.refresh_from_db()
        self.assertEqual(app1.status, Application.APPROVED)

        # Кредитная организация НЕ может изменить статус в Заявке к чужому Предложению
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app2.id)
        response = client_lender.patch(
            url,
            {'status': Application.APPROVED}
        )
        self.assertNotEqual(response.status_code, 200)
        app2.refresh_from_db()
        self.assertEqual(app2.status, Application.NEW)

        # Партнёр НЕ может изменить статус Заявки
        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app2.id)
        response = client_partner.patch(
            url,
            {'status': Application.APPROVED}
        )
        self.assertNotEqual(response.status_code, 200)
        app2.refresh_from_db()
        self.assertEqual(app2.status, Application.NEW)

        update_data = {
            'id': app1.pk,
            'customer': reverse('customers_detail', kwargs={'pk': customer2.pk}),
            'lender_offer': reverse('offers_detail', kwargs={'pk': offer1.pk}),
            'status': app1.status,
            'status_display': app1.get_status_display(),
            'created_at': datetime.now() - relativedelta(months=1),
            'updated_at': datetime.now() - relativedelta(months=1)
        }
        # Кредитная организация НЕ может произвольно редактировать Заявку
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app1.id)
        response = client_lender.put(url, update_data)
        self.assertEqual(response.status_code, 405)

        # Партнёр НЕ может произвольно редактировать Заявку
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app1.id)
        response = client_partner.put(url, update_data)
        self.assertEqual(response.status_code, 405)

    def test_application_delete(self):
        customer = Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=self.user1_partner.partner,
        )
        offer = Offer.objects.create(
            name='Предложение 1', offer_type=Offer.CONSUMER_CREDIT,
            rotating_start=datetime.now() - relativedelta(days=1),
            rotating_end=datetime.now() + relativedelta(months=1),
            min_credit_score=1, max_credit_score=25,
            lender=self.user3_lender.lender
        )
        app = Application.objects.create(customer=customer, lender_offer=offer)

        client_partner = APIClient()
        client_partner.login(username=self.user1_partner.username, password='user1_partner')

        # Партнёр НЕ может удалять Заявки
        url = '{api_url}{pk}/'.format(api_url=self.api_url, pk=app.id)
        response = client_partner.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Application.objects.all().count(), 1)

        client_lender = APIClient()
        client_lender.login(username=self.user3_lender.username, password='user3_lender')

        # Кредитная организация НЕ может удалять Заявки
        response = client_lender.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Application.objects.all().count(), 1)
