from typing import Any, Mapping

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def success_response(message: str = "success", data=None):
    content = {
        "code": 200,
        "message": message,
        "data": data
    }
    # 目标：把任何的FastAPI、Pydantic、ORM对象都要正常响应->code、message、data
    return JSONResponse(content=jsonable_encoder(content), status_code=200)


def error_response(
        message: str = "error",
        code: int = 400,
        data: Any = None,
        status_code: int | None = None,
        headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """统一错误响应，结构与 success_response 对称：code、message、data"""
    content = {
        "code": code,
        "message": message,
        "data": data
    }
    try:
        body = jsonable_encoder(content)
    except Exception:
        # data 中存在无法序列化的对象时降级，避免处理器自身抛异常
        body = {"code": code, "message": message, "data": None}

    # HTTP 状态码非法会让 JSONResponse 构造失败，统一回退到 400
    http_status = status_code if status_code is not None else code
    if not isinstance(http_status, int) or not 400 <= http_status <= 599:
        http_status = 400

    return JSONResponse(
        content=body,
        status_code=http_status,
        headers=dict(headers) if headers else None,
    )
