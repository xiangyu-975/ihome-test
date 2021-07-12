import json
import logging
import re

from django import http
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.utils.decorators import method_decorator
from django_redis import get_redis_connection
# Create your views here.
from django.views import View
from pymysql import DatabaseError

from utils.decorators import login_required
from utils.param_checking import image_file
from utils.response_code import RET

from libs.qiniuyun.qiniu_storage import storage
from celery_tasks.tpc.tasks import tpc_storage
from .models import User

logger = logging.getLogger('django')


class RegisterView(View):
    '''注册界面'''

    def post(self, request):
        # 1:接受参数----根据接口文档
        dict_data = json.loads(request.body.decode())
        mobile = dict_data.get('mobile')
        phonecode = dict_data.get('phonecode')
        password = dict_data.get('password')
        # 2:校验参数
        # 判断参数是否齐全
        if not all([mobile, phonecode, password]):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '请输入8-20位密码'})
        # 判断手机好号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '请输入合法的手机号'})
        # 检验用户输入的手机验证码和redis的手机验证码是否一致
        redis_conn = get_redis_connection('verify_code')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if not real_sms_code:
            return http.JsonResponse({'errno': RET.NODATA, 'errmsg': '验证码已过期'})
        if real_sms_code.decode() != phonecode:
            return http.JsonResponse({'errno': RET.DATAERR, 'errmsg': '验证码输入错误'})
        # 业务逻辑
        save_data = {
            'username': mobile,
            'mobile': mobile,
            'password': password
        }
        try:
            user = User.objects.create_user(**save_data)
        except DatabaseError as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '注册失败'})
        # 状态保持
        login(request, user)
        # 返回响应
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '注册成功'})


class LoginView(View):
    '''登录界面'''

    def get(self, request):
        '''判断是否登录'''
        # 1.获取user对象
        user = request.user
        # 2.对user进行认证
        if not user.is_authenticated:
            return http.JsonResponse({'errno': RET.SESSIONERR, 'errmsg': '用户未登录'})
        data = {
            'user_id': user.id,
            'name': user.username
        }
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '已登录', 'data': data})

    def post(self, request):
        # 接收参数
        dict_data = json.loads(request.body.decode())
        mobile = dict_data.get('mobile')
        password = dict_data.get('password')
        # 校验参数
        if not all([mobile, password]):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数不全'})
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '请输入合法手机号'})
        # 判断密码是否合法
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '密码错误'})
        # 认证登录用户
        user = authenticate(username=mobile, password=password)
        if user is None:
            return http.JsonResponse({'errno': RET.LOGINERR, 'errmsg': '请输入正确的手机号'})
        # 实现状态保持
        login(request, user)
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '登录成功'})

    def delete(self, request):
        logout(request)
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '退出成功'})


class UserInfoView(View):
    '''用户中心'''

    # 判断用户是否登录,装饰器
    @method_decorator(login_required)
    def get(self, request):
        """
        {
            "data": {
                "avatar": "http://oyucyko3w.bkt.clouddn.com/FmWZRObXNX6TdC8D688AjmDAoVrS",
                "create_time": "2017-11-07 01:10:21",
                "mobile": "18599998888",
                "name": "哈哈哈哈哈哈",
                "user_id": 1
            },
            "errmsg": "OK",
            "errno": "0"
        }
        声明：数据库中目前没有avatar字段，create_time我们用date_join字段。所以需要先给模型类添加字段
        """
        # 1.获取数据
        user = request.user
        # data = {
        #     'avatar': user.objects.get('avatar'),
        #     'create_time': datetime.strftime(user.objects.get('date_joined'), '%Y-%M-%d %H:%M:%S'),
        #     'mobile': user.objects.get('mobile'),
        #     'name': user.objects.get('username'),
        #     'user_id': user.objects.get('id')
        # }
        data = user.to_basic_dict()
        return http.JsonResponse({'errno': RET.OK, 'errmsg': 'OK', 'data': data})


class AvatarView(View):
    '''用户上传头像'''

    @method_decorator(login_required)
    def post(self, request):
        # 1.接收参数
        avatar = request.FILES.get("avatar")
        if not avatar:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        if not image_file(avatar):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        # 读取出文件对象的二进制数据
        file_data = avatar.read()
        #
        # try:
        #     key = tpc_storage.apply_async(file_data)
        # except Exception as e:
        #     logger.error(e)
        #     return http.JsonResponse({'errno': RET.THIRDERR, 'errmsg': '上传图片失败'})
        try:
            key = storage(file_data)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.THIRDERR, 'errmsg': '上传图片失败'})
        try:
            request.user.avatar = key
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.SERVERERR, 'errmsg': '图片保存失败'})
        data = {
            'avatar_url': settings.QINIU_URL + key,
        }
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '头像上传成功', 'data': data})


class ModifyNameView(View):
    '''修改用户名'''

    @method_decorator(login_required)
    def put(self, request):
        dict_data = json.loads(request.body.decode())
        username = dict_data.get('name')
        user = request.user
        try:
            user.username = username
            user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '数据保存失败'})
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '修改成功'})


class UserAuthView(View):
    '''实名制认证'''

    @method_decorator(login_required)
    def get(self, request):
        # 显示认证信息
        data = request.user.to_auth_dict()
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '认证信息查询成功', 'data': data})

    def post(self, request):
        dict_data = json.loads(request.body.decode())
        real_name = dict_data.get('real_name')
        id_card = dict_data.get('id_card')
        if not all([real_name, id_card]):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        if re.match(
                r'(^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$)|(^[1-9]\d{5}\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}$)',
                id_card):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        user = request.user
        try:
            user.real_name = real_name
            user.id_card = id_card
            user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '数据保存失败'})
        else:
            return http.JsonResponse({'errno': RET.OK, 'errmsg': '认证信息保存成功'})


class UserOrderView(View):
    '''用户订单'''

    def get(self, request):
        user = request.user
