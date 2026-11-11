"""统一三层响应 {code, message, data}。code 与 HTTP 状态码一致。"""

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def ok(data=None, message="操作成功"):
    """成功响应:HTTP 200,{code:200, message, data}。"""
    return Response({"code": 200, "message": message, "data": {} if data is None else data}, status=200)


def fail(status_code, message, data=None):
    """失败响应:HTTP 用 status_code,body {code:status_code, message, data}。"""
    return Response(
        {"code": status_code, "message": message, "data": {} if data is None else data},
        status=status_code,
    )


def api_exception_handler(exc, context):
    """把 DRF 默认错误响应(403/401/404/400 等 {"detail": ...})也包成三层。"""
    response = drf_exception_handler(exc, context)
    if response is None:
        return fail(500, "服务器内部错误")

    data = response.data
    if isinstance(data, dict) and "detail" in data:
        message = data["detail"]
    elif isinstance(data, dict):
        message = ""
        for value in data.values():
            if isinstance(value, list) and value:
                message = value[0]
            else:
                message = value
            break
    else:
        message = data

    if not isinstance(message, str):
        message = str(message)

    return Response(
        {"code": response.status_code, "message": message, "data": {}},
        status=response.status_code,
    )