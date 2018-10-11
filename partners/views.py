# encoding: utf-8
from django_filters import rest_framework as django_filters
from rest_framework import filters, generics, mixins

from accounts.utils import UserIsPartnerMixin, is_lender, is_partner
from applications.models import Application
from partners.models import Customer
from partners.serializers import CustomerCreateSerializer, CustomerSerializer


class CustomerFilter(django_filters.FilterSet):

    class Meta:
        model = Customer
        fields = {
            'created_at': ['lt', 'gt'],
            'updated_at': ['lt', 'gt'],
            'credit_score': ['lt', 'gt'],
            'birth_date': ['lt', 'gt'],
        }


class CustomerView(UserIsPartnerMixin,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   generics.GenericAPIView):

    serializer_class = CustomerSerializer
    serializer_create_class = CustomerCreateSerializer
    filter_backends = (
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = CustomerFilter
    search_fields = ('surname',)
    ordering_fields = ('credit_score', 'created_at', 'updated_at', 'birth_date')

    def get_queryset(self):
        return Customer.objects.select_related(
            'partner__user'
        ).filter(
            partner__user=self.request.user
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return self.serializer_create_class
        return super().get_serializer_class()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(partner=self.request.user.partner)


class CustomerDetailView(mixins.RetrieveModelMixin,
                         generics.GenericAPIView):

    serializer_class = CustomerSerializer

    def get_queryset(self):
        customers_qs = Customer.objects.select_related('partner__user')

        if is_partner(self.request.user):
            customers_qs = customers_qs.filter(partner__user=self.request.user)

        if is_lender(self.request.user):
            # Показывает только те Анкеты, от которых есть Заявки к Предложениям текущей Кредитной организации
            customers_ids = Application.objects.filter(
                lender_offer__lender__user=self.request.user
            ).select_related(
                'customer'
            ).values_list('customer_id', flat=True)

            customers_qs = customers_qs.filter(pk__in=customers_ids)

        return customers_qs

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
