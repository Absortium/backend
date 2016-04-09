__author__ = 'andrew.shvv@gmail.com'

from django.conf.urls import url

from absortium import views

urlpatterns = [
    url(r'^orders/$', views.OrderListView.as_view()),
    url(r'^offers/(?P<pair>[^/]+)/(?P<type>[^/]+)$', views.OfferListView.as_view()),

]
