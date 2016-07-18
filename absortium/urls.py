from django.conf import settings
from django.conf.urls import url, include
from rest_framework_nested import routers

from absortium.views import \
    AccountViewSet, \
    OrderViewSet, \
    OfferViewSet, \
    WithdrawalViewSet, \
    DepositViewSet, \
    MarketInfoSet, \
    HistoryViewSet, \
    btc_notification_handler, \
    eth_notification_handler

__author__ = "andrew.shvv@gmail.com"

router = routers.SimpleRouter()
router.register(prefix=r"accounts", viewset=AccountViewSet, base_name="Account")
router.register(prefix=r"orders", viewset=OrderViewSet, base_name="Order")
router.register(prefix=r"deposits", viewset=DepositViewSet, base_name="Deposits")
router.register(prefix=r"withdrawals", viewset=WithdrawalViewSet, base_name="Withdrawals")
router.register(prefix=r"offers", viewset=OfferViewSet, base_name="Offers")
router.register(prefix=r"marketinfo", viewset=MarketInfoSet, base_name="MarketInfo")
router.register(prefix=r"history", viewset=HistoryViewSet, base_name="History")

urlpatterns = [
    url(r"^api/", include(router.urls)),
    url(r"^notifications/" + settings.ETH_NOTIFICATION_TOKEN, eth_notification_handler),
    url(r"^notifications/" + settings.BTC_NOTIFICATION_TOKEN, btc_notification_handler)
]
