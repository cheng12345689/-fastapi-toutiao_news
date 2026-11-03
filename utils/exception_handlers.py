import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.exceptions import AppException
from utils.response import error_response

logger = logging.getLogger(__name__)


def _normalize_http_status(code: int, default: int = 400) -> int:
    """HTTP 状态码只接受 400-599，其余回退到默认值"""
    if isinstance(code, int) and 400 <= code <= 599:
        return code
    return default


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """业务异常：HTTP 状态码取业务 code，响应体保留原始 code"""
    status_code = _normalize_http_status(exc.code)

    # 5xx 属于服务端故障：原文只进日志，响应体不回显，避免泄露内部信息
    if status_code >= 500:
        logger.error("服务端业务异常 code=%s path=%s message=%s", exc.code, request.url.path, exc.message)
        return error_response(
            message="服务器内部错误",
            code=exc.code,
            data=None,
            status_code=status_code,
        )

    logger.info("业务异常 code=%s path=%s message=%s", exc.code, request.url.path, exc.message)
    return error_response(
        message=exc.message,
        code=exc.code,
        data=exc.data,
        status_code=status_code,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """参数校验失败：只暴露字段路径、提示、类型，丢弃 input/ctx 等不安全内容"""
    errors = []
    for err in exc.errors()[:20]:
        loc = err.get("loc") or ()
        field = ".".join(str(item) for item in loc if item != "body") or "body"
        errors.append({
            "field": field,
            "msg": str(err.get("msg", ""))[:200],
            "type": str(err.get("type", ""))[:200],
        })
    return error_response(message="参数校验失败", code=422, data=errors, status_code=422)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    """HTTPException 统一成 {code, message, data}，覆盖 404/405 等框架层错误"""
    # 保留 WWW-Authenticate、Allow 等响应头，过滤非字符串值
    headers = {key: value for key, value in (exc.headers or {}).items() if isinstance(value, str)}

    # 2xx/3xx 语义特殊（如 304、重定向），只保留状态码与响应头
    if exc.status_code < 400:
        return Response(status_code=exc.status_code, headers=headers or None)

    # 5xx 不回显 detail，避免泄露内部信息
    if exc.status_code >= 500:
        message = "服务器内部错误"
    elif isinstance(exc.detail, str) and exc.detail:
        message = exc.detail
    else:
        message = "请求失败"

    return error_response(
        message=message,
        code=exc.status_code,
        data=None,
        status_code=exc.status_code,
        headers=headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底 500：完整堆栈只进日志，响应体不泄露任何异常细节"""
    logger.exception("未处理异常 method=%s path=%s", request.method, request.url.path)
    return error_response(message="服务器内部错误", code=500, data=None, status_code=500)


def register_exception_handlers(app: FastAPI) -> None:
    """集中注册全局异常处理器，需在应用开始服务前调用"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # 必须注册 starlette 基类，路由未匹配的 404、405 抛的是基类而非 fastapi.HTTPException
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
