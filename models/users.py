from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户id")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（加密存储）")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="头像URL")
    gender: Mapped[str] = mapped_column(
        Enum("male", "female", "unknown", name="gender"),
        default="unknown",
        nullable=False,
        comment="性别"
    )
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="个人简介")
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, comment="手机号")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class UserToken(Base):
    """用户访问令牌（表里只有 created_at，没有 updated_at）"""
    __tablename__ = "user_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="令牌id")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="用户id"
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="令牌值")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )

    def __repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id})>"
