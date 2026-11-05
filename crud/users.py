import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from models.users import User, UserToken
from schemas.users import UserRequest, UpdateUserRequest
from utils import security
from utils.security import hash_password

DEFAULT_BIO = "这个人很懒，什么都没留下"
DEFAULT_AVATAR = "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalars().one_or_none()


async def create_user(db: AsyncSession, username: str, password: str) -> User:
    user = User(
        username=username,
        password=hash_password(password),
        bio=DEFAULT_BIO,
        avatar=DEFAULT_AVATAR
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)  # 从数据库中读回最新的user
    return user


async def create_token(db: AsyncSession, user_id: int, expire_days: int = 7) -> str:
    token = secrets.token_urlsafe(32)
    db.add(UserToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.now() + timedelta(days=expire_days)
    ))
    await db.flush()
    return token


async def register(db: AsyncSession, username: str, password: str) -> tuple[User, str] | None:
    """注册：用户名已存在返回 None，否则创建用户并签发 token"""
    if await get_user_by_username(db, username):
        return None

    user = await create_user(db, username, password)
    token = await create_token(db, user.id)
    return user, token

async def get_user_by_token(db: AsyncSession, token: str) -> User | None:
    """按令牌查用户：令牌不存在或已过期时返回 None"""
    stmt = (
        select(User)
        .join(UserToken, UserToken.user_id == User.id)
        .where(UserToken.token == token, UserToken.expires_at > datetime.now())
    )
    result = await db.execute(stmt)
    return result.scalars().one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> tuple[User, bool] | None:
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None
    return user

# 更新用户信息
async def update_user(db: AsyncSession, username: str, user_data: UpdateUserRequest) -> User:
    # user_data是一个Pydantic类型，得到字典->**解包
    # 没有设置值的不更新
    query = update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_none=True,
        exclude_unset=True
    ))
    result = await db.execute(query)
    await db.commit()

    ## 检查更新
    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="用户不存在")
    update_user = await get_user_by_username(db, username)
    return update_user

# 修改密码
async def change_password(db: AsyncSession, user: str, old_password, new_password: str):
    if not security.verify_password(old_password, user.password):
        return False
    hash_new_password = security.hash_password(new_password)
    user.password = hash_new_password
    await db.commit()
    await db.refresh(user)
    return True