from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class History(Base):
    """浏览历史表：用户和新闻的多对多关联

    同一篇新闻只保留一条记录，重复浏览只刷新 view_time。
    表里只有 view_time，没有创建/更新时间，所以不混入 TimestampMixin。
    """
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="历史id")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="用户id"
    )
    news_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("news.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="新闻id"
    )
    view_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment="浏览时间"
    )

    def __repr__(self):
        return f"<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id})>"
