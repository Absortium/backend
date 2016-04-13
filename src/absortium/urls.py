__author__ = 'andrew.shvv@gmail.com'

from django.conf.urls import url, include
from rest_framework_nested import routers

from absortium.views import AccountViewSet, ExchangeViewSet, OfferListView, DepositViewSet, WithdrawViewSet

router = routers.SimpleRouter()
router.register(prefix=r'accounts', viewset=AccountViewSet, base_name="Account")

accounts_router = routers.NestedSimpleRouter(router, "accounts", lookup="accounts")
accounts_router.register(r"exchanges", ExchangeViewSet, base_name='Exchange')
accounts_router.register(r"deposits", DepositViewSet, base_name='Deposits')
accounts_router.register(r"withdrawals", WithdrawViewSet, base_name='Withdrawals')


urlpatterns = [

    url(r'^api/', include(router.urls)),
    url(r'^api/', include(accounts_router.urls)),
    url(r'^api/offers/$', OfferListView.as_view()),
    url(r'^auth/', include('jwtauth.urls')),
]
