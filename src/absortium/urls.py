__author__ = 'andrew.shvv@gmail.com'

from django.conf import settings
from django.conf.urls import url, include
from rest_framework_nested import routers

from absortium.views import \
    AccountViewSet, \
    ExchangeViewSet, \
    OfferListView, \
    WithdrawalViewSet, \
    DepositViewSet, \
    MarketInfoSet, \
    HistoryViewSet, \
    btc_notification_handler, \
    eth_notification_handler

router = routers.SimpleRouter()
router.register(prefix=r'accounts', viewset=AccountViewSet, base_name="Account")
router.register(prefix=r'exchanges', viewset=ExchangeViewSet, base_name='Exchange')

accounts_router = routers.NestedSimpleRouter(router, "accounts", lookup="accounts")
accounts_router.register(r"deposits", DepositViewSet, base_name='Deposits')
accounts_router.register(r"withdrawals", WithdrawalViewSet, base_name='Withdrawals')

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/', include(accounts_router.urls)),
    url(r'^api/offers/$', OfferListView.as_view()),
    url(r'^api/marketinfo/$', MarketInfoSet.as_view()),
    url(r'^api/history/$', HistoryViewSet.as_view()),
    url(r'^notifications/' + settings.ETH_NOTIFICATION_TOKEN, eth_notification_handler),
    url(r'^notifications/' + settings.BTC_NOTIFICATION_TOKEN, btc_notification_handler)
]
