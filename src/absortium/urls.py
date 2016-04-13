__author__ = 'andrew.shvv@gmail.com'

from django.conf.urls import url, include
from rest_framework_nested import routers

from absortium.views import AccountViewSet, ExchangeViewSet

router = routers.SimpleRouter()
router.register(prefix=r'accounts', viewset=AccountViewSet, base_name="Account")

accounts_router = routers.NestedSimpleRouter(router, "accounts", lookup="accounts")
accounts_router.register(r"exchanges", ExchangeViewSet, base_name='Exchange')

urlpatterns = [

    url(r'^api/', include(router.urls)),
    url(r'^api/', include(accounts_router.urls)),
    url(r'^auth/', include('jwtauth.urls')),
]
