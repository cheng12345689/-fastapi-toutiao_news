from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud import users
from config.db_conf import get_db
from crud import users as users_crud
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse
from utils.auth import get_current_user
from utils.exceptions import AppException
from utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["users"])


@router.post("/register")
async def register(user_info: UserRequest, db: AsyncSession = Depends(get_db)):  # 用户信息和db
    # 注册逻辑：验证用户是否存在->创建用户->生成Token->响应结果
    result = await users_crud.register(db, user_info.username, user_info.password)
    if result is None:
        raise AppException("用户名已存在")

    user, token = result
    # return {
    #     "code": 200,
    #     "message": "注册成功",
    #     "data": {
    #         "token": token,
    #         "userInfo": {
    #             "id": user.id,
    #             "username": user.username,
    #             "bio": user.bio,
    #             "avatar": user.avatar
    #         }
    #     }
    # }
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功", data=response_data)

@router.post("/login")
async def login(user_info: UserRequest, db: AsyncSession = Depends(get_db)):
    # 登录逻辑：验证用户是否存在->验证密码->生成Token->响应结果
    user = await users.authenticate_user(db, user_info.username, user_info.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功", data=response_data)

@router.get("/info")
async def get_user_info(user: User | None = Depends(get_current_user)):
    # 无令牌/令牌过期/查不到用户，依赖统一返回 None，这里抛出异常
    if user is None:
        raise AppException("未登录或登录已过期", code=401)

    return success_response(message="success", data=UserInfoResponse.model_validate(user))


