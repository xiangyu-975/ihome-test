from ..tpc.qiniuyun.qiniu_storage import TPC
from ..main import celery_app


@celery_app.task(bind=True, name='tpc_storage', retry_backoff=3)
def tpc_storage(self, data):
    '''
    上传图片异步操作
    :param data:
    :return:
    '''
    ret = TPC().storage(data=data)

    return ret["key"]
