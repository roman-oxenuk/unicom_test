# encoding: utf-8
from rest_framework import serializers

from lenders.models import Offer


class OfferSerializer(serializers.ModelSerializer):

    lender_name = serializers.CharField(source='lender.name')

    class Meta:
        model = Offer
        fields = ('__all__')
