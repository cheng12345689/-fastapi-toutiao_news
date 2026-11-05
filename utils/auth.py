"""认证相关依赖：从请求头解析令牌并取出当前用户。"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud.users import get_user_by_token
from models.users import User


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(..., alias="Authorization")
) -> User:
    """解析 Authorization: Bearer <token>，返回令牌对应的用户。

    令牌不存在或已过期时抛 401，由全局异常处理器统一成 {code, message, data}。
    """
    # Bearer XXXXX
    # token = authorization.split(" ")[1]
    token = authorization.replace("Bearer ", "")
    user = await get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌或已经过期的令牌")

    return user
