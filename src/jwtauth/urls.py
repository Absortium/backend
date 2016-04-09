__author__ = 'andrew.shvv@gmail.com'

from django.conf.urls import url

from jwtauth.views import ViewRefresh, ViewVerify, ViewObtainBasic, ViewObtainSocialOAuth2, ViewObtainSocialOAuth1

urlpatterns = [
    url(r'^verify', ViewVerify.as_view()),
    url(r'^refresh', ViewRefresh.as_view()),
    url(r'^social/oauth2/(?P<provider>[^/]+)$', ViewObtainSocialOAuth2.as_view()),
    url(r'^social/oauth1/(?P<provider>[^/]+)$', ViewObtainSocialOAuth1.as_view()),
    url(r'^basic', ViewObtainBasic.as_view()),
]
