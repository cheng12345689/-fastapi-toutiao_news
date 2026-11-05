from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class UserRequest(BaseModel):
    username: str
    password: str

# user_info 对应的类 ： 基础类+ info 类
class UserInfoBase(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=5000, description="个人简介")

class UserInfoResponse(UserInfoBase):
    id: int
    username: str

    # 模型类配置
    model_config = ConfigDict(
        from_attributes=True  # 允许从ORM对象属性中取值
    )


# data数据类型
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse = Field(..., alias="userInfo")

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  # 用于别名和字段名兼容
        from_attributes=True   # 允许从ORM对象属性中取值
    )

# 性别枚举：必须和数据库 Enum("male", "female", "unknown") 保持一致，
# 否则非法值会一路走到 MySQL 才报错，变成 500
Gender = Literal["male", "female", "unknown"]
# 更新用户信息的模型类（字段都可选：没传的字段保持原值）
class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[Gender] = Field(None, description="性别：male / female / unknown")
    bio: Optional[str] = Field(None, max_length=5000, description="个人简介")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")

class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword")
    new_password: str = Field(..., alias="newPassword")
