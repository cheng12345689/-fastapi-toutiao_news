"""认证相关依赖：从请求头解析令牌并取出当前用户。"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud.users import get_user_by_token
from models.users import User

BEARER_PREFIX = "bearer"


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> User | None:
    """解析 Authorization: Bearer <token>，返回令牌对应的用户。

    无请求头、格式不对、令牌不存在或已过期时统一返回 None，
    由路由处理函数决定抛什么异常、回什么错误码。
    """
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != BEARER_PREFIX or not token.strip():
        return None

    return await get_user_by_token(db, token.strip())
