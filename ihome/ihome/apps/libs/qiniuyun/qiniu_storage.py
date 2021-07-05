import logging

from qiniu import Auth, put_data, etag
import qiniu.config

access_key = '66IMdEOiu0A0nLerMIaynq1Up71Re7GNmcWf_Hkj'
secret_key = 'qKT40T7syV3nKVYa5DTqeMkr6QJkhpRn4b2svZEj'
# 要上传的空间
bucket_name = 'xyihome'


def storage(data):
    if not data:
        return None
    try:
        # 构建鉴权对象
        q = Auth(access_key, secret_key)
        # 生成Token，可以制定过期时间
        token = q.upload_token(bucket_name)
        # 上传图片到七牛
        ret, info = put_data(token, None, data)
    except Exception as e:
        logging.error(e)
        raise e
    if info and info.status_code != 200:
        raise Exception('上传到七牛云失败')
    # 返回七牛云中保存的图片名，这个图片也是访问七牛云获取图片的路径
    print(ret['key'])
    return ret['key']


if __name__ == '__main__':
    file_name = input("输入要上传的图片")
    with open(file_name, "rb") as f:
        storage(f.read())
