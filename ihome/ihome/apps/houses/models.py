from django.conf import settings
from django.db import models

# Create your models here.
from orders.models import Order
from utils.model import BaseModel


class Areas(BaseModel):
    '''城区'''
    name = models.CharField(max_length=32, null=False, verbose_name='区域名字')

    class Meta:
        db_table = 'tb_areas'

    def to_dict(self):
        '''将对象转化为字典'''
        areas_dict = {
            'aid': self.pk,
            'aname': self.name
        }
        return areas_dict


class Facility(BaseModel):
    '''设施信息'''
    name = models.CharField(max_length=32, null=False, verbose_name='设施名字')

    class Meta:
        db_table = 'tb_facility'


class House(BaseModel):
    '''房屋信息'''
    user = models.ForeignKey("users.User", related_name="houses", on_delete=models.CASCADE, verbose_name="房屋主人编号")
    area = models.ForeignKey(Areas, null=False, on_delete=models.CASCADE, verbose_name="归属地的区域编号")
    title = models.CharField(max_length=64, null=False, verbose_name='标题')
    price = models.IntegerField(default=0)  # 单价是分
    address = models.CharField(max_length=512, default="")  # 地址
    room_count = models.IntegerField(default=1)  # 房间数
    acreage = models.IntegerField(default=0)  # 房间面积
    unit = models.CharField(max_length=32, default="")  # 几室几厅
    capacity = models.IntegerField(default=1)  # 能容纳人数
    beds = models.CharField(max_length=64, default="")  # 房屋床铺的配置
    deposit = models.IntegerField(default=0)  # 房屋押金
    min_days = models.IntegerField(default=1)  # 最少入住天数
    max_days = models.IntegerField(default=0)  # 最多入住天数，0表示不限制
    order_count = models.IntegerField(default=0)  # 预订完成的该房房屋的订单数
    index_image_url = models.CharField(max_length=256, default="")  # 房屋图片的路径
    facility = models.ManyToManyField(Facility, verbose_name='和设施表之间是多对多的关系')

    class Meta:
        db_table = "tb_house"

    def to_basic_dict(self):
        '''将基本的信息转换为字典数据'''
        '''
        {
        "address": "地址地址",
        "area_name": "东城区",
        "ctime": "2017-11-12",
        "house_id": 5,
        "img_url": "http://oyucyko3w.bkt.clouddn.com/FhxrJOpjswkGN2bUgufuXPdXcV6w",
        "order_count": 0,
        "price": 10000,
        "room_count": 1,
        "title": "我是房屋标题",
        "user_avatar": "http://oyucyko3w.bkt.clouddn.com/FmWZRObXNX6TdC8D688AjmDAoVrS"
        },
        '''
        house_dict = {
            "house_id": self.pk,
            "order_count": self.order_count,
            "title": self.title,
            "ctime": self.create_time.strftime("%Y-%m-%d"),
            "price": self.price,
            "area_name": self.area.name,
            "address": self.address,
            "room_count": self.room_count,
            "img_url": settings.QINIU_URL + self.index_image_url if self.index_image_url else "",
            "user_avatar": settings.QINIU_URL + self.user.avatar.name if self.user.avatar.name else "",
        }
        return house_dict

    def to_full_dict(self):
        # 将详细信息转化为字典数据
        '''
        "house": {
            "acreage": 5,
            "address": "我是地址",
            "beds": "5张床",
            "capacity": 5,
            "comments": [
                {
                    "comment": "哎哟不错哟",
                    "ctime": "2017-11-14 11:17:07",
                    "user_name": "匿名用户"
                }
            ],
            "deposit": 500,
            "facilities": [
                1
            ],
            "hid": 4,
            "img_urls": [
                "http://oyucyko3w.bkt.clouddn.com/FhgvJiGF9Wfjse8ZhAXb_pYObECQ",
                "http://oyucyko3w.bkt.clouddn.com/FkagyA8TiuxnLsz7ofLfA_CY34Nw"
            ],
            "max_days": 5,
            "min_days": 5,
            "price": 500,
            "room_count": 5,
            "title": "555",
            "unit": "5",
            "user_avatar": "http://oyucyko3w.bkt.clouddn.com/FmWZRObXNX6TdC8D688AjmDAoVrS",
            "user_id": 1,
            "user_name": "哈哈哈哈哈哈"
        },
        '''
        house_dict = {
            'acreage': self.acreage,
            'address': self.address,
            'beds': self.beds,
            'capacity': self.capacity,
            'deposit': self.deposit,
            'hid': self.pk,
            'max_days': self.max_days,
            'min_days': self.min_days,
            'price': self.price,
            'room_count': self.room_count,
            'title': self.title,
            'unit': self.unit,
            'user_id': self.user.id,
            'user_name': self.user.username,
            'user_avatar': settings.QINIU_URL + self.user.avatar.name if self.user.avatar.name else '',
        }
        # 房屋图片
        img_urls = []
        for image in self.houseimage_set.all():
            img_urls.append(settings.QINIU_URL + image.url)
        house_dict['img_urls'] = img_urls
        # 房屋设施
        facilities = []
        for facility in self.facility.all():
            facilities.append(facility.id)
        house_dict['facilities'] = facilities
        # 评论信息
        comments = []
        orders = Order.objects.filter(house=self, status=Order.ORDER_STATUS["COMPLETE"],
                                      comment__isnull=False).order_by("-update_time")[0:30]
        for order in orders:
            comment = {
                "comment": order.comment,  # 评论内容
                "user_name": order.user.username if order.user.username != order.user.mobile else "匿名用户",
                "ctime": order.update_time.strftime("%Y-%m-%d %H-%M-%S")
            }
            comments.append(comment)
        house_dict["comments"] = comments
        return house_dict


class HouseImage(BaseModel):
    '''房屋图片表'''
    house = models.ForeignKey(House, on_delete=models.CASCADE)  # 房屋编号
    url = models.CharField(max_length=256, null=False)  # 图片的路径

    class Meta:
        db_table = 'tb_house_image'
