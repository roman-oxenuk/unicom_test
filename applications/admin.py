from django.contrib import admin

from applications.models import Application


class ApplicationAdmin(admin.ModelAdmin):

    list_display = ('status', 'customer', 'lender_offer',)
    list_filter = ('status',)
    search_fields = ('customer__surname', 'customer__name', 'lender_offer__name')
    raw_id_fields = ('customer', 'lender_offer',)


admin.site.register(Application, ApplicationAdmin)
