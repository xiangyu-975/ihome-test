from django.conf.urls import url
from . import views

urlpatterns = [
    # 订单
    url('^orders$', views.OrdersView.as_view()),
    # 订单状态
    url('^orders/(?P<order_id>\d+)/status$', views.OrderStatusView.as_view()),
    # 订单评论
    url('^orders/(?P<order_id>\d+)/comment$', views.OrderCommentView.as_view()),
]
