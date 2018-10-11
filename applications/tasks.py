# encoding: utf-8
import numbers

from celery import shared_task
from django.conf import settings
from django.db.models import Prefetch

from applications.models import Application
from partners.models import Customer


@shared_task
def match_customer_task(customer):
    if not isinstance(customer, Customer) and isinstance(customer, numbers.Number):
        try:
            customer = Customer.objects.prefetch_related(
                'application_set'
            ).get(
                id=customer
            )
        except Customer.DoesNotExists:
            return

    new_applications = customer.match_with_offers()
    Application.objects.bulk_create(new_applications)


@shared_task
def match_customers_with_offers_task():
    new_applications = []

    customers = Customer.objects.prefetch_related(
        'application_set'
    ).filter(
        offer_matching_mode__contains=['auto']
    )
    for customer in customers:
        new_applications += customer.match_with_offers()

    Application.objects.bulk_create(new_applications)
