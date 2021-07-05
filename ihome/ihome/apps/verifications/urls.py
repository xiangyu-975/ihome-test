from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    # path('imagecode/', views.ImageCodeView),
    # path('sms/', views.SMSCodeView)
    url(r'^imagecode$', views.ImageCodeView.as_view()),
    url(r'^sms$', views.SMSCodeView.as_view()),
]
