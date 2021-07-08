import json
import logging
from datetime import datetime

from django import http
from django.shortcuts import render

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View
from django_redis import get_redis_connection

from houses.models import House
from orders.models import Order
from utils.decorators import login_required
from utils.response_code import RET

logger = logging.getLogger('django')


class OrdersView(View):
    '''订单'''

    def get(self, request):
        # 获取当前用户的id
        user = request.user
        role = request.GET.get('role')
        # 校验参数
        if not role:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        if role not in ["custom", "landlord"]:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        if role == "custom":
            # 查询自己下了哪些订单
            orders = Order.objects.filter(user=user).order_by("-create_time")
        if role == 'landlord':
            # 查询自己的房屋都有哪些订单
            houses = House.objects.filter(user=user)
            house_ids = [house.id for house in houses]
            orders = Order.objects.filter(house_id__in=house_ids).order_by("-create_time")
        orders_dict = [order.to_dict() for order in orders]
        print(orders_dict)
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '发布成功', 'data': {'orders': orders_dict}})

    def post(self, request):
        # 获取当前用户的id
        user = request.user
        # 获取传入的参数
        dict_data = json.loads(request.body.decode())
        house_id = dict_data.get('house_id')
        start_date_str = dict_data.get('start_date')
        end_date_str = dict_data.get('end_date')
        # 校验参数
        if not all([house_id, start_date_str, end_date_str]):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            assert start_date < end_date, Exception('开始日期大于结束日期')
            # 计算入住天数
            days = (end_date - start_date).days
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        # 判断房屋是否存在
        try:
            house = House.objects.get(id=house_id)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.NODATA, 'errmsg': '房屋不存在'})
        # 判断房屋是否是当前用户的
        if user.id == house.user.id:
            return http.JsonResponse({'errno': RET.ROLEERR, 'errmsg': '不能预订自己的房间'})
        # 查询是否有订单冲突
        try:
            filters = {'house': house, 'start_date__lt': end_date, 'end_date__gt': start_date}
            count = Order.objects.filter(**filters).count()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '数据库查询错误'})
        if count > 0:
            return http.JsonResponse({'errno': RET.DATAERR, 'errmsg': '房间已经被预订'})
        amount = days * house.price
        # 生成订单的模型
        order = Order()
        order.user = user
        order.house = house
        order.start_date = start_date
        order.end_date = end_date
        order.days = days
        order.house_price = house.price
        order.amount = amount
        try:
            order.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '数据库保存失败'})
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '发布成功', 'data': {'order_id': order.pk}})


class OrderStatusView(View):
    @method_decorator(login_required)
    def put(self, request, order_id):
        user = request.user
        dict_data = json.loads(request.body.decode())
        action = dict_data.get('action')
        if action not in ('accept', 'reject'):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        try:
            order = Order.objects.filter(id=order_id, status=Order.ORDER_STATUS["WAIT_ACCEPT"]).first()
            house = order.house
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '查询数据错误'})
        # 判断订单是否存在并且当前房屋的用户id是当前用户的id
        if not order or house.user != user:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        if action == 'accept':
            # 接单
            order.status = Order.ORDER_STATUS["WAIT_PAYMENT"]
        elif action == 'reject':
            # 拒单
            reason = dict_data.get('reason')
            if not reason:
                return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '未填写拒绝理由'})

            # 设置状态为拒绝并填写拒单原因
            order.status = Order.ORDER_STATUS['REJECTED']
            order.comment = reason
        # 保存到数据库中
        try:
            order.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '保存订单状态失败'})
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '操作成功'})


class OrderCommentView(View):
    @method_decorator(login_required)
    def put(self, request, order_id):
        dict_data = json.loads(request.body.decode())
        comment = dict_data.get('comment')
        if not comment:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '请输入评论内容'})
        # 通过订单id查出订单模型
        try:
            order = Order.objects.filter(id=order_id, status=Order.ORDER_STATUS['WAIT_COMMENT']).first()
            house = order.house
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '查询数据失败'})
        # 更新数据
        house.order_count += 1
        order.status = Order.ORDER_STATUS['COMPLETE']
        order.comment = comment
        # 更新数据库
        try:
            # 事务处理
            house.save()
            order.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '数据库更新失败'})
        # 删除redis中的缓存的房屋详细信息，因为房屋详情已经更新
        redis_conn = get_redis_connection("house_cache")
        try:
            redis_conn.delete('house_info_' + str(house.id))
        except Exception as e:
            logger.error(e)
        return http.JsonResponse({'errno': RET.OK, 'errmsg': 'OK'})
