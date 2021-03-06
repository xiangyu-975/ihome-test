import json
import logging
import random
import re

from django import http
from django.views import View
from django_redis import get_redis_connection

# Create your views here.
from utils import constants
from utils.response_code import RET
from .libs.captcha.captcha import captcha
from celery_tasks.sms.tasks import ccp_send_sms_code

logger = logging.getLogger('django')


class ImageCodeView(View):
    '''
    需求：获取图片验证码
    '''

    def get(self, request):
        # 1.接收参数
        cur_uuid = request.GET.get('cur')
        pre_uuid = request.GET.get('pre')
        # 2.校验参数
        if not cur_uuid:
            return http.HttpResponseForbidden('参数不全')
        #
        if not re.match(r"\w{8}(-\w{4}){3}-\w{12}", cur_uuid):
            return http.HttpResponseForbidden('参数格式不正确')
        if pre_uuid and not re.match(r"\w{8}(-\w{4}){3}-\w{12}", pre_uuid):
            return http.HttpResponseForbidden('参数格式不正确')
        # 3.生成验证码
        text, image = captcha.generate_captcha()
        logger.info("图片验证码:%s" % text)
        # 将验证码保存到redis中
        redis_conn = get_redis_connection('verify_code')
        try:
            # 删除之前的
            redis_conn.delete('ImageCode_' + pre_uuid)
            # 保存当前的
            redis_conn.setex('ImageCode_' + cur_uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('生成图形验证码失败')
        else:
            return http.HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    '''短信验证码'''

    def post(self, request):
        # 1.接收参数
        dict_data = json.loads(request.body.decode())
        mobile = dict_data.get('mobile')
        image_code_id = dict_data.get('id')
        image_code = dict_data.get('text')
        # 创建redis连接实例对象
        redis_conn = get_redis_connection('verify_code')
        # 判断该手机号的标记是否存在，如果存在就说明发送消息频繁
        sms_code_flag = redis_conn.get('sms_code_flag_%s' % mobile)
        if sms_code_flag:
            return http.JsonResponse({'errno': RET.REQERR, 'errmsg': '发送短信频繁'})
        # 2.校验参数
        if not all([mobile, image_code_id, image_code]):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        if not re.match(r"1[3-9]\d{9}", mobile):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数错误'})
        try:
            real_image_code = redis_conn.get('ImageCode_' + image_code_id)
            if not real_image_code:
                return http.JsonResponse({'errno': RET.NODATA, 'errmsg': '验证码已经过期'})
            redis_conn.delete('ImageCode_' + image_code_id)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'errno': RET.DBERR, 'errmsg': '数据库查询错误'})
        # 因为redis数据库读出的数据是bytes类型，所以要转str，decode
        if image_code.upper() != real_image_code.decode().upper():
            return http.JsonResponse({'errno': RET.DATAERR, 'errmsg': '验证码输入错误'})
        # 3.生成手机验证码
        sms_code = "%06d" % random.randint(0, 999999)
        logger.info("短信验证码是：%s" % sms_code)
        # 4.将手机验证码保存到redis中（添加使用管道逻辑）
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("sms_code_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        # 5.发送短信+异步任务处理
        # try:
        #     result = CCP().send_message(mobile=mobile, tid='1',
        #                                 datas=(sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60))
        #     if result != 1:
        #         return http.JsonResponse({'errno': RET.THIRDERR, 'errmsg': '第三方系统出错'})
        # except Exception as e:
        #     logger.error(e)
        #     return http.JsonResponse({'errno': RET.UNKOWNERR, 'errmsg': '未知错误'})
        # CCP().send_message(mobile=mobile, tid='1', datas=(sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60))
        ccp_send_sms_code.delay(mobile, sms_code)
        # 6.返回响应
        return http.JsonResponse({'errno': RET.OK, 'errmsg': '发送短信成功'})
