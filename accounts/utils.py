# encoding: utf-8
from django.contrib.auth.mixins import UserPassesTestMixin


# Эти две функции используются в accounts.admin
def is_in_partners_group(user):
    return hasattr(user, 'groups') and user.groups.filter(name='Партнёры').exists()

def is_in_lenders_group(user):
    return hasattr(user, 'groups') and user.groups.filter(name='Кредитные организации').exists()


def is_partner(user):
    return is_in_partners_group(user) and hasattr(user, 'partner')

def is_lender(user):
    return is_in_lenders_group(user) and hasattr(user, 'lender')


class UserIsPartnerMixin(UserPassesTestMixin):

    def test_func(self):
        return is_partner(self.request.user)


class UserIsLenderMixin(UserPassesTestMixin):

    def test_func(self):
        return is_lender(self.request.user)
