# encoding: utf-8
from django_filters import rest_framework as django_filters
from rest_framework import filters, generics, mixins, status
from rest_framework.response import Response

from accounts.utils import is_lender, is_partner
from applications.models import Application
from applications.serializers import (ApplicationSerializer,
                                      ApplicationToAllLendersSerializer,
                                      ApplicationToCertainLenderSerializer)


class ApplicationsFilter(django_filters.FilterSet):

    class Meta:
        model = Application
        fields = {
            'created_at': ['lt', 'gt'],
            'updated_at': ['lt', 'gt'],
            'status': ['exact'],
        }


class ApplicationsView(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       generics.GenericAPIView):

    filter_backends = (
        django_filters.DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filterset_class = ApplicationsFilter
    ordering_fields = ('created_at', 'updated_at',)

    serializer_class = ApplicationSerializer
    serializer_class_create_for_certain = ApplicationToCertainLenderSerializer
    serializer_class_create_for_all = ApplicationToAllLendersSerializer

    def get_queryset(self):
        apps_qs = Application.objects.select_related(
            'customer__partner',
            'lender_offer__lender'
        ).all()

        if is_partner(self.request.user):
            apps_qs = apps_qs.filter(customer__partner=self.request.user.partner)

        if is_lender(self.request.user):
            apps_qs = apps_qs.filter(lender_offer__lender=self.request.user.lender)

        return apps_qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            if 'lender_id' in self.request.data:
                if self.request.data['lender_id'] == 'all':
                    return self.serializer_class_create_for_all
                return self.serializer_class_create_for_certain

        return super().get_serializer_class()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        output = self.get_output(serializer)
        return Response(output, status=status.HTTP_201_CREATED, headers=headers)

    def get_output(self, serializer):

        if isinstance(serializer, self.serializer_class_create_for_all):
            msg = 'Анкета {customer} отправлена на рассмотрение во все кредитные организации.'\
                        .format(customer=serializer.customer)
            return {'message': msg}

        if isinstance(serializer, self.serializer_class_create_for_certain):

            if not serializer.new_applications:
                if serializer.existed_applications:
                    msg = 'У кредитной организации "{lender}" нет новых подходящих предложений для {customer}'\
                            .format(lender=serializer.lender, customer=serializer.customer)
                else:
                    msg = 'У кредитной организации "{lender}" нет подходящих предложений для {customer}'\
                        .format(lender=serializer.lender, customer=serializer.customer)

                return {'message': msg}

            # Используем сериалайзер для чтения чтобы вернуть только что созданные Заявки
            read_serializer = self.serializer_class(
                serializer.new_applications,
                many=True,
                context={'request': self.request}
            )
            return read_serializer.data


class ApplicationsDetailView(mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             generics.GenericAPIView):

    serializer_class = ApplicationSerializer

    def get_queryset(self):
        apps_qs = Application.objects.select_related(
            'customer__partner',
            'lender_offer__lender'
        ).all()

        if is_partner(self.request.user):
            apps_qs = apps_qs.filter(customer__partner=self.request.user.partner)

        if is_lender(self.request.user):
            apps_qs = apps_qs.filter(lender_offer__lender=self.request.user.lender)

        return apps_qs

    def patch(self, request, *args, **kwargs):
        if not is_lender(request.user):
            msg = 'Меня статус заявки могу только кредитные организации. '\
                  'Ползователь "{user}" не является кредитной организацией.'\
                  .format(user=request.user)
            return Response({'message': msg}, status=status.HTTP_400_BAD_REQUEST)

        return self.partial_update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
