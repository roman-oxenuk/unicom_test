# encoding: utf-8
from datetime import datetime

from rest_framework import generics, mixins

from accounts.utils import UserIsPartnerMixin, is_lender
from lenders.models import Offer
from lenders.serializers import OfferSerializer


class BaseOffersView(generics.GenericAPIView):

    serializer_class = OfferSerializer


class OffersView(UserIsPartnerMixin,
                 mixins.ListModelMixin,
                 BaseOffersView):

    def get_queryset(self):
        return Offer.objects.select_related(
            'lender'
        ).filter(
            rotating_start__lte=datetime.now(),
            rotating_end__gte=datetime.now()
        )

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class OffersDetailView(mixins.RetrieveModelMixin,
                       BaseOffersView):

    def get_queryset(self):
        offers_qs = Offer.objects.select_related('lender__user')

        if is_lender(self.request.user):
            offers_qs = offers_qs.filter(lender__user=self.request.user)

        return offers_qs

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
