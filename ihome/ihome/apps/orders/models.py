from django.conf import settings
from django.db import models

# Create your models here.
from utils.model import BaseModel


class Order(BaseModel):
    '''订单'''
    ORDER_STATUS = {
        "WAIT_ACCEPT": 0,
        "WAIT_PAYMENT": 1,
        "PAID": 2,
        "WAIT_COMMENT": 3,
        "COMPLETE": 4,
        "CANCELED": 5,
        "REJECTED": 6
    }

    ORDER_STATUS_ENUM = {
        0: "WAIT_ACCEPT",  # 待接单
        1: "WAIT_PAYMENT",  # 待支付
        2: "PAID",  # 已支付
        3: "WAIT_COMMENT",  # 待评价
        4: "COMPLETE",  # 已完成
        5: "CANCELED",  # 已取消
        6: "REJECTED",  # 已拒单
    }

    ORDER_STATUS_CHOICES = (
        (0, "WAIT_ACCEPT"),  # 待接单
        (1, "WAIT_PAYMENT"),  # 带支付
        (2, "PAID"),  # 已支付
        (3, "WAIT_COMMENT"),  # 待评价
        (4, "COMPLETE"),  # 已完成
        (5, "CANCELED"),  # 已取消
        (6, "REJECTED"),  # 已拒单

    )
    user = models.ForeignKey('users.User', related_name='orders', on_delete=models.CASCADE, verbose_name='下单的用户编号')
    house = models.ForeignKey('houses.House', on_delete=models.CASCADE, verbose_name='预订的房间编号')
    start_date = models.DateField(null=False, verbose_name='预订的起始时间')
    end_date = models.DateField(null=False, verbose_name='结束时间')
    days = models.IntegerField(null=False, verbose_name='预订的总天数')
    house_price = models.IntegerField(null=False, verbose_name='房屋单价')
    amount = models.IntegerField(null=False, verbose_name='订单总金额')
    status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=0, db_index=True, verbose_name='订单状态')
    comment = models.TextField(null=True, verbose_name='订单的评论信息或拒单原因')

    class Meta:
        db_table = 'tb_order'

    '''
    {
    "data": {
        "orders": [
            {
                "amount": 1000,
                "comment": "哎哟不错哟",
                "ctime": "2017-11-14 09:59:35",
                "days": 2,
                "end_date": "2017-11-15",
                "img_url": "http://oyucyko3w.bkt.clouddn.com/FhgvJiGF9Wfjse8ZhAXb_pYObECQ",
                "order_id": 1,
                "start_date": "2017-11-14",
                "status": "COMPLETE",
                "title": "555"
            },
            {
                "amount": 20000,
                "comment": "不约",
                "ctime": "2017-11-14 10:59:12",
                "days": 2,
                "end_date": "2017-11-17",
                "img_url": "http://oyucyko3w.bkt.clouddn.com/FhxrJOpjswkGN2bUgufuXPdXcV6w",
                "order_id": 2,
                "start_date": "2017-11-16",
                "status": "REJECTED",
                "title": "我是房屋标题"
                }
            ]
        },
        "errmsg": "OK",
        "errno": "0"
    }
    '''

    def to_dict(self):
        '''将订单信息转换为字典数据'''
        order_dict = {
            "order_id": self.pk,
            "title": self.house.title,
            "status": Order.ORDER_STATUS_ENUM[self.status],
            "ctime": self.create_time.strftime("%Y-%m-%d %H:%M"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "days": self.days,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "img_url": settings.QINIU_URL + self.house.index_image_url if self.house.index_image_url else "",
            "comment": self.comment,
            "amount": self.amount,
        }
        return order_dict
