from django.conf.urls import url

from . import views

urlpatterns = [
    # 地区列表
    url(r'^areas$', views.AreasView.as_view()),
    # 发布房源
    url(r'^houses$', views.HouseView.as_view()),
    # 上传房源图片
    url(r'^houses/(?P<house_id>\d+)/images$', views.HouseImageView.as_view()),
    # 用户房源
    url(r'^user/houses$', views.UserHouseView.as_view()),
    # 首页房屋推荐
    url(r'^houses/index$', views.HouseIndexView.as_view()),
    # 房屋详情
    url(r'^houses/(?P<house_id>\d+)$', views.HouseDetailView.as_view()),
]
