from django.conf import settings
from django.contrib.auth.views import LoginView
from django.shortcuts import resolve_url

from accounts.utils import is_lender, is_partner


class UnicomLoginView(LoginView):

    def get_success_url(self):
        url = self.get_redirect_url()

        if is_partner(self.request.user):
            custome_url = settings.LOGIN_REDIRECT_URL_PARTNER

        if is_lender(self.request.user):
            custome_url = settings.LOGIN_REDIRECT_URL_LENDER

        return url or resolve_url(custome_url)
