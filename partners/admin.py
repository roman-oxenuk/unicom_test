from django.contrib import admin

from partners.models import Customer, Partner


class PartnerAdmin(admin.ModelAdmin):

    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username',)
    raw_id_fields = ('user',)


class CustomerAdmin(admin.ModelAdmin):

    list_display = ('surname', 'name', 'patronymic', 'passport_number', 'phone_number', 'birth_date', 'partner')
    search_fields = ('name', 'surname', 'patronymic', 'passport_number', 'phone_number', 'partner__name')
    raw_id_fields = ('partner',)
    list_filter = ('partner',)


admin.site.register(Partner, PartnerAdmin)
admin.site.register(Customer, CustomerAdmin)
