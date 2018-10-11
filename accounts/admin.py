from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from accounts.utils import is_in_lenders_group, is_in_partners_group
from lenders.models import Lender
from partners.models import Partner


class PartnerInline(admin.StackedInline):
    model = Partner
    can_delete = False
    verbose_name_plural = 'partners'


class LenderInline(admin.StackedInline):
    model = Lender
    can_delete = False
    verbose_name_plural = 'lenders'


class UserAdmin(BaseUserAdmin):

    def get_inline_instances(self, request, obj=None):

        if is_in_partners_group(obj):
            self.inlines = (PartnerInline,)

        if is_in_lenders_group(obj):
            self.inlines = (LenderInline,)

        return super().get_inline_instances(request, obj=None)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
