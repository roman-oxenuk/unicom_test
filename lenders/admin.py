from django.contrib import admin

from lenders.models import Lender, Offer


class LenderAdmin(admin.ModelAdmin):

    list_display = ('name', 'user')
    search_fields = ('name', 'user__username',)
    raw_id_fields = ('user',)


class OfferAdmin(admin.ModelAdmin):

    list_display = (
        'lender', 'name',
        'rotating_start', 'rotating_end',
        'min_credit_score', 'max_credit_score',
        'offer_type',
    )
    list_filter = ('offer_type', 'lender')
    search_fields = ('name', 'lender__name',)


admin.site.register(Lender, LenderAdmin)
admin.site.register(Offer, OfferAdmin)
