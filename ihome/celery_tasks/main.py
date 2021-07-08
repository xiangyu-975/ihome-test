from celery import Celery

# import os

# 读取django项目的配置
# os.environ["DJANGO_SETTINS_MODULE"] = ["ihome.settings"]

# 创建celery实例
celery_app = Celery('ihome')
# , broker='redis://127.0.0.1/10', backend='redis://127.0.0.1'

# 加载celery配置
celery_app.config_from_object('celery_tasks.config')
# 自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.tpc'])
