from rest_framework import serializers

from partners.models import Customer


class CustomerSerializer(serializers.ModelSerializer):

    birth_date = serializers.DateField()
    partner = serializers.PrimaryKeyRelatedField(read_only=True)
    partner_name = serializers.CharField(source='partner.name')

    class Meta:
        model = Customer
        fields = ('__all__')


class CustomerCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        exclude = ('partner',)
