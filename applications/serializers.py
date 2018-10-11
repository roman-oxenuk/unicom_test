# encoding: utf-8
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from applications.models import Application
from applications.tasks import match_customer_task
from lenders.models import Lender
from partners.models import Customer


class ApplicationSerializer(serializers.ModelSerializer):

    customer = serializers.HyperlinkedRelatedField(read_only=True, view_name='customers_detail')
    lender_offer = serializers.HyperlinkedRelatedField(read_only=True, view_name='offers_detail')
    status = serializers.IntegerField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ('__all__')

    def get_status_display(self, obj):
        return obj.get_status_display()


class BaseApplicationSerializer(serializers.Serializer):

    customer_id = serializers.IntegerField()
    request_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_customer_id(self, value):
        customer = get_object_or_404(Customer, pk=value)
        self.customer = customer

        if 'manual' not in customer.offer_matching_mode:
            manual_verbous = filter(lambda x: x[0] == 'manual', Customer.OFFER_MATCHING_MODES)
            manual_verbous = list(manual_verbous)[0][1]
            raise serializers.ValidationError(
                'Анкету "{customer}" нельзя отправить на заявку в кредитные организации, '
                'т.к. у этой анкеты нет режима создания заявок "{mode}".'\
                .format(customer=customer, mode=manual_verbous),
            )
        return value

    def validate(self, data):
        if not hasattr(data['request_user'], 'partner'):
            raise serializers.ValidationError(
                'Создавать заявки могу только партнёры. Ползователь "{user}" не является партнёром.'\
                .format(user=data['request_user'])
            )

        if not data['request_user'].partner.customer_set.filter(pk=data['customer_id']).exists():
            raise serializers.ValidationError(
                'У партнёра "{partner}" нет анкеты с id "{customer_id}".'\
                .format(partner=data['request_user'], customer_id=data['customer_id'])
            )

        return data


class ApplicationToCertainLenderSerializer(BaseApplicationSerializer):

    lender_id = serializers.IntegerField()

    def validate_lender_id(self, value):
        lender = get_object_or_404(Lender, pk=value)
        self.lender = lender
        return value

    def save(self):
        existed_applications, new_applications = self.customer.match_with_offers(self.lender, return_existed=True)

        # Сохраняем новые Заявки в базу
        Application.objects.bulk_create(new_applications)

        self.existed_applications = existed_applications
        self.new_applications = new_applications


class ApplicationToAllLendersSerializer(BaseApplicationSerializer):

    lender_id = serializers.CharField()

    def validate_lender_id(self, value):
        if value != 'all':
            raise serializers.ValidationError(
                'Значение "lender_id" должно быть "all" или id анкеты. Передано "{value}".'\
                .format(value=value)
            )
        return value

    def save(self):
        match_customer_task.delay(self.validated_data['customer_id'])
