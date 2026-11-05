from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud import users
from config.db_conf import get_db
from crud import users as users_crud
from crud.users import change_password
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UpdateUserRequest, UserChangePasswordRequest
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
async def get_user_info(user: User = Depends(get_current_user)):
    # 令牌校验失败已经在依赖里抛 401，这里拿到的 user 一定是有效用户
    return success_response(message="success", data=UserInfoResponse.model_validate(user))
@router.put("/update")
# 更新用户信息：验证Token->更新（用户输入数据put提交->请求体参数->定义Pydantic模型类）->响应结果
async def update_user_info(user_data: UpdateUserRequest, user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    #  需要的参数：用户输入参数，验证token，数据库依赖项
    user = await users_crud.update_user(db, user.username, user_data)
    return success_response(message="更新信息成功", data=UserInfoResponse.model_validate(user))

@router.put("/password")
async def update_password(user_password: UserChangePasswordRequest,
                          user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    #change_password
    ch_pwd = await change_password(db, user, user_password.old_password, user_password.new_password)
    if ch_pwd is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="密码修改失败")
    return success_response(message="密码修改成功")

