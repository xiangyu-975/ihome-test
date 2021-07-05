from django import http

from utils.response_code import RET


def login_required(view_func):
    '''
    定义用户登录的装饰器
    :param view_func:
    :return:
    '''

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            return http.JsonResponse({'errno': RET.SESSIONERR, 'errmsg': '用户未登录'})

    return wrapper
