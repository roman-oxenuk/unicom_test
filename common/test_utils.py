# encoding: utf-8
import random
from datetime import date, datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.dateparse import parse_date, parse_datetime

from lenders.models import Lender
from partners.models import Partner


User = get_user_model()


class CreateInitialDataMixin:
    """
    Миксин для создания базовых тестовх данных.
    """

    def setUp(self):
        super().setUp()
        partners_grp = Group.objects.get(name='Партнёры')
        lenders_grp = Group.objects.get(name='Кредитные организации')

        # Партнёры
        self.user1_partner = User.objects.create_user(username='Partner 1', password='user1_partner')
        Partner.objects.create(user=self.user1_partner, name='М-Видео')
        partners_grp.user_set.add(self.user1_partner)
        self.user1_partner.refresh_from_db()

        self.user2_partner = User.objects.create_user(username='Partner 2', password='user2_partner')
        Partner.objects.create(user=self.user2_partner, name='Евросеть')
        partners_grp.user_set.add(self.user2_partner)

        # Кредитные организации
        self.user3_lender = User.objects.create_user(username='Lender 1', password='user3_lender')
        Lender.objects.create(user=self.user3_lender, name='СберБанк')
        lenders_grp.user_set.add(self.user3_lender)

        self.user4_lender = User.objects.create_user(username='Lender 2', password='user4_lender')
        Lender.objects.create(user=self.user4_lender, name='ВТБ')
        lenders_grp.user_set.add(self.user4_lender)


class FiltersTestMixin:
    """
    Миксин для проверки работы фильтров в API.
    """

    def check_filter_field(self, all_objects, client, api_url, fields):
        """
        Пример использования метода:
        fields = {
            'created_at': ['lt', 'gt'],
            'updated_at': ['lt', 'gt'],
            'status': [''],             # Пустая строка имеет такое же значение, как 'exact'
        }
        self.check_filter_field([app1, app3, app5], client_lender, self.api_url, fields)

        :param all_objects: list of objects, список объектов, которые должны вернуться по API
        :param client: rest_framework.test.APIClient
        :param api_url: str, url, по которому делается запрос к API через переданный client
        :fields dict: словарь полей, по которым можно фильтровать
        """
        field_types = {
            int: {
                'to_string': lambda x: str(x),
                'from_string': lambda x: int(x)
            },
            str: {
                'to_string': lambda x: x,
                'from_string': lambda x: x
            },
            date: {
                'to_string': lambda x: x.strftime(settings.REST_FRAMEWORK['DATE_FORMAT']),
                'from_string': lambda x: parse_date(x),
            },
            datetime: {
                'to_string': lambda x: x.strftime(settings.REST_FRAMEWORK['DATETIME_FORMAT']),
                'from_string': lambda x: parse_datetime(x).replace(microsecond=0),
            }
        }

        for field, lookups in fields.items():

            field_type = None
            random_value = getattr(random.choice(all_objects), field)

            if isinstance(random_value, datetime):
                field_type = datetime
                random_value = random_value.replace(microsecond=0)

            elif isinstance(random_value, date):
                field_type = date

            elif isinstance(random_value, str):
                field_type = str

            elif isinstance(random_value, int):
                field_type = int

            for lookup in lookups:

                if lookup == '':
                    url = '{url}?{field}={value}'.format(
                        url=api_url, field=field,
                        value=field_types[field_type]['to_string'](random_value)
                    )
                else:
                    url = '{url}?{field}__{lookup}={value}'.format(
                        url=api_url, field=field, lookup=lookup,
                        value=field_types[field_type]['to_string'](random_value)
                    )

                response = client.get(url)
                response_data = response.json()
                response_values = [item[field] for item in response_data]

                if lookup == 'lt':
                    for value in response_values:
                        self.assertTrue(
                            # Из-за округления до микросекунд сравниваем как "<=", а не строко "<"
                            field_types[field_type]['from_string'](value) <= random_value
                        )

                if lookup == 'gt':
                    for value in response_values:
                        self.assertTrue(
                            # Из-за округления до микросекунд сравниваем как ">=", а не строко ">"
                            field_types[field_type]['from_string'](value) >= random_value
                        )

                if lookup == '':    # Пустая строка имеет такое же значение, как 'exact'
                    for value in response_values:
                        self.assertTrue(
                            field_types[field_type]['from_string'](value) == random_value
                        )


class OrderingTestMixin:
    """
    Миксин для проверки работы сортировок в API.
    """

    def check_ordering(self, all_objects, client, api_url, ordering_fields):
        """
        Пример использования метода:
        ordering_fields = ('credit_score', 'created_at', 'updated_at', 'birth_date')
        self.check_ordering([customer1, customer2, customer3], client_partner, self.api_url, ordering_fields)

        :param all_objects: list of objects, список объектов, которые должны вернуться по API
        :param client: rest_framework.test.APIClient
        :param api_url: str, url, по которому делается запрос к API через переданный client
        :fields list: список полей, по которым можно сортировать
        """
        for field in ordering_fields:

            for modifier in ['', '-']:

                reverse = False
                if modifier == '-':
                    reverse = True

                url = '{url}?ordering={mod}{field}'.format(
                    url=api_url, mod=modifier, field=field
                )

                response = client.get(url)
                response_data = response.json()
                response_ids = [item['id'] for item in response_data]

                reverse = False
                if modifier == '-':
                    reverse = True

                expected_order = sorted(all_objects, key=lambda x: getattr(x, field), reverse=reverse)
                expected_order_ids = [cust.id for cust in expected_order]

                self.assertEqual(response_ids, expected_order_ids)
