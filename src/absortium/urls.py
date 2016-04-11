__author__ = 'andrew.shvv@gmail.com'

from django.conf.urls import url, include

from absortium import views

urlpatterns = [
    url(r'^api/orders/$', views.OrderListView.as_view()),
    url(r'^api/offers/(?P<pair>[^/]+)/(?P<type>[^/]+)$', views.OfferListView.as_view()),
    url(r'^auth/', include('jwtauth.urls')),
]