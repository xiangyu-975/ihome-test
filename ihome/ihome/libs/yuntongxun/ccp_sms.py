import json

from ronglian_sms_sdk import SmsSDK

accId = '8a216da86d05dc0b016d4df574c32f95'

accToken = '91be773d51774eda94f3382c25fb1124'

appId = '8aaf07087a331dc7017a805fb7fc2136'


class CCP(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instants'):
            cls._instants = super(CCP, cls).__new__(cls, *args, **kwargs)
            # 单例在使用完会销毁，那么当我们初始化发送短信验证码的对象后，也需要销毁
            cls._instants.sdk = SmsSDK(accId, accToken, appId)
            cls._instants.sdk.sendMessage(tid='', mobile='', datas=())
        return cls._instants

    def send_message(self, tid, mobile, datas):
        resp = self.sdk.sendMessage(tid, mobile, datas)
        result = json.loads(resp)
        print(result.get('statusCode'))
        if result.get('statusCode') == '000000':
            return 1
        else:
            return -1


if __name__ == '__main__':
    CCP().send_message('1', '13337717633', ('000000', '5'))
