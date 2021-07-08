from django.conf.urls import url
from django.urls import path
from . import views

urlpatterns = [
    # path('users/', views.RegisterView),
    # path('session/',views.LoginView),
    # 注册
    url(r'^users$', views.RegisterView.as_view()),
    # 登录
    url(r'^session$', views.LoginView.as_view()),
    # 用户中心
    url(r'^user$', views.UserInfoView.as_view()),
    # 修改用户头像
    url(r'^user/avatar$', views.AvatarView.as_view()),
    # 修改用户名
    url(r'^user/name$', views.ModifyNameView.as_view()),
    # 用户实名制认证
    url(r'^user/auth$', views.UserAuthView.as_view()),
    # 获取订单列表
    url(r'^user/orders$', views.UserOrderView.as_view()),
]
