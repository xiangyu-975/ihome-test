# bind：保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff×2^(n-1))s
# max_retries：异常自动重试次数的上限
from .yuntongxun.ccp_sms import CCP
from ..main import celery_app
from .. import constants


@celery_app.task(bind=True, name='ccp_send_sms_code', retry_backoff=3)
def ccp_send_sms_code(self, mobile, sms_code):
    '''
    发送短信异步操作
    :param self:
    :param mobile:手机号
    :param sms_code:验证码
    :return:成功1 或者 失败-1
    '''
    send_ret = CCP().send_message(tid=constants.SEND_SMS_TEMPLATE_ID, mobile=mobile,
                                  datas=(sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60))
    return send_ret
