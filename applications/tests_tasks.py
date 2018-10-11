# encoding: utf-8
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from applications.models import Application
from applications.tasks import match_customers_with_offers_task
from partners.models import Customer, Partner


User = get_user_model()


class ApplicationsTasksTestCase(TestCase):

    def test_task_match_customers_with_offers_task(self):
        partners_grp = Group.objects.get(name='Партнёры')

        # Создаём партнёра
        user1_partner = User.objects.create_user(username='Partner 1', password='user1_partner')
        partner = Partner.objects.create(user=user1_partner, name='М-Видео')
        partners_grp.user_set.add(user1_partner)
        user1_partner.refresh_from_db()

        customer1 = Customer.objects.create(
            surname='Иванов', name='Пётр', patronymic='Сергеевич',
            birth_date='1990-01-01', phone_number='89117310203', passport_number='1901432765',
            credit_score=10, partner=partner, offer_matching_mode=['auto']
        )
        customer2 = Customer.objects.create(
            surname='Ульянова', name='Мария', patronymic='Алексеевна',
            birth_date='1992-01-01', phone_number='89117310102', passport_number='1901432711',
            credit_score=18, partner=partner, offer_matching_mode=['manual', 'auto']
        )
        customer3 = Customer.objects.create(
            surname='Овчинников', name='Алексей', patronymic='Александрович',
            birth_date='1983-01-01', phone_number='89117310505', passport_number='1901432700',
            credit_score=25, partner=partner, offer_matching_mode=['manual']
        )

        with mock.patch.object(Application.objects, 'bulk_create') as bulk_create_mock:
            with mock.patch.object(Customer, 'match_with_offers', autospec=True) as match_with_offers_mock:
                match_with_offers_mock.side_effect = lambda *args, **kwargs: ['fake_data']
                match_customers_with_offers_task()

        self.assertEqual(match_with_offers_mock.call_count, 2)
        match_with_offers_mock.assert_has_calls([mock.call(customer1), mock.call(customer2)])
        bulk_create_mock.assert_called_once_with(['fake_data', 'fake_data'])
